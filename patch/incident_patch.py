from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect

from django.conf import settings

from stix.common import vocabs
from edge.generic import WHICH_DBOBJ
from edge import IDManager, NamespaceNotConfigured
from edge.tools import rgetattr, cleanstrings
from incident import views
from rbac import user_can_edit
from edge import incident
import json

import sys
import urllib
import traceback
from bson import ObjectId
from mongoengine.connection import get_db
import logging

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings

from stix.common import vocabs

from users.models import Repository_User, Draft
from edge import IDManager, NamespaceNotConfigured
from users.tools import jstime
from edge.generic import ApiObject, EdgeObject
from edge import incident, ttp, indicator
from edge.handling import lines2list
from edge.inbox import InboxProcessorForBuilders, InboxItem, InboxError
from trustgroups.models import Trustgroup
from edge.tools import rgetattr, would_update
from edge.relate import correlateInctoObs, correlateInctoTtp, correlateInctoAct, correlateInctoInd, correlateInctoInc
from users.models import TLP_GROUPS
from users.decorators import json_body
from crashlog.models import save as save_crash
from rbac import user_can_edit

import json

CATEGORIES = vocabs.IncidentCategory._ALLOWED_VALUES
TIMETYPES = ("First_Malicious_Action", "Initial_Compromise", "First_Data_Exfiltration", "Incident_Discovery", "Incident_Opened", "Containment_Achieved", "Restoration_Achieved", "Incident_Reported", "Incident_Closed")
TIMEZONES = ("zone1", "zone2", "zone3")

@login_required
def incident_build(request):
    request.breadcrumbs([("Incident Edit", "/incident/build/")])

    static = views.get_static(request.user)
    configuration = settings.REPOCONFIG()
    id_ns = None
    id = None
    try:
        id_ns = IDManager().get_namespace()
        id = IDManager().get_new_id('incident')
    except NamespaceNotConfigured as e:
        messages.info(request, e.message)
        return redirect('/setup')

    return render(request, 'cert-inc-build.html', {
        'mode': 'Build',
        'id': id,
        'id_ns': id_ns,
        'default_tlp' : configuration.by_key('default_tlp'),
        'effects': json.dumps(static['effects']),
        'statuses': json.dumps(static['statuses']),
        'categories': json.dumps(CATEGORIES),
        'time_types_list' : json.dumps(TIMETYPES),
        'time_zones_list' : json.dumps(TIMEZONES),
        'confidences': json.dumps(static['confidences']),
        'tlps': json.dumps(static['tlps']),
        'trustgroups': json.dumps(static['trustgroups']),
        'discovery_methods': json.dumps(static['discovery_methods']),
        'intended_effects': json.dumps(static['intended_effects']),
        'ajax_uri': reverse('incident_ajax'),
        'object_type': "incident",
    })


@login_required
def incident_view(request, id, edit=False):

    if edit:
        request.breadcrumbs([ ("Incident Edit","/incident/edit/") ])
        mode = "Edit"
    else:
        request.breadcrumbs([ ("Incident View","/incident/build/") ])
        mode = "View"

    static = views.get_static(request.user)
    return render(request, 'cert-inc-build.html', {
        'mode': mode,
        'object_type'      : 'incident',
        'id': id,
        'object_type': "incident",
        'edit_allowed' : user_can_edit(request.user, id),
        'effects': json.dumps(static['effects']),
        'statuses': json.dumps(static['statuses']),
        'categories': json.dumps(CATEGORIES),
        'time_types_list' : json.dumps(TIMETYPES),
        'time_zones_list' : json.dumps(TIMEZONES),
        'confidences': json.dumps(static['confidences']),
        'tlps': json.dumps(static['tlps']),
        'trustgroups': json.dumps(static['trustgroups']),
        'discovery_methods': json.dumps(static['discovery_methods']),
        'intended_effects': json.dumps(static['intended_effects']),
        'ajax_uri': reverse('incident_ajax'),
        'object_type': "incident",
    })

class DBIncidentPatch(incident.DBIncident):

    def __init__(self, obj=None, id_=None, idref=None, timestamp=None, title=None, description=None, short_description=None):
        super(DBIncidentPatch, self).__init__(obj, id_, idref, timestamp, title, description, short_description)

    @classmethod
    def to_draft(cls, incident, tg, load_by_id, id_ns=''):
        draft = super(DBIncidentPatch, cls).to_draft(incident, tg, load_by_id, id_ns)
        draft['categories'] =  [ c.value for c in rgetattr(incident,['categories'],[]) ]
        return draft

    @classmethod
    def from_draft(cls, draft):
        target = super(DBIncidentPatch, cls).from_draft(draft)
        target.categories = cleanstrings(draft.get('categories'))
        return target

@json_body
@login_required
def ajax_create_incident(request, draft):
    # Start by building the object.  This includes mapping all of the STIX
    #   values (as strings) to stix library objects so that to_dict() works
    #   correctly
    result = False
    message = ""
    thrown = None

    try:
        errors = views.validate_related_items(draft)
        if errors:
            return {'success' : False, 'message' : '\n'.join([str(err) for err in errors]) }

        generic_object = None
        usercanedit = user_can_edit(request.user, draft.get('id'))
        wouldupdate = would_update(draft.get('id'))
        if wouldupdate:
            if usercanedit:
                eo = EdgeObject.load(draft.get('id'))  # populating eo with data from DB
                # Compares eo's active attributes with attributes in the draft and mutates active attributes as needed
                eo.obj.update_with(DBIncidentPatch.from_draft(draft))
                generic_object = eo.to_ApiObject()
                user_action_log = logging.getLogger('user_actions')
                user_action_log.info("%s updated STIX item %s (%s)" % (request.user.username, eo.id_, eo.obj.title))
            else:
                return {'success' : False, 'message' : "You do not have permission to update this document"}
        else:
            generic_object = ApiObject('inc', DBIncidentPatch.from_draft(draft))

        [ correlateInctoInd(generic_object, item['idref']) for item in draft.get('related_indicators',[]) ]
        [ correlateInctoObs(generic_object, item['idref']) for item in draft.get('related_observables',[]) ]
        [ correlateInctoTtp(generic_object, item['idref']) for item in draft.get('leveraged_ttps',[]) ]
        [ correlateInctoAct(generic_object, item['idref']) for item in draft.get('attributed_actors',[]) ]
        [ correlateInctoInc(generic_object, item['idref']) for item in draft.get('related_incidents',[]) ]
        # Wanted to try to correlate Incidents on commonalities among the target lists... gonna need more
        # than this one line of code, but maybe we get to it soon.
        #[ correlateInctoInc(generic_object, item['idref']) for item in d.get('victims',[]) ]

        etlp = (draft.get('tlp') or 'NULL').upper()
        esms = lines2list(draft.get('markings', ""))

        ip = InboxProcessorForBuilders(
            user=request.user,
            trustgroups=draft.get('trustgroups', []),
        )
        ip.add(InboxItem(api_object=generic_object,
                         etlp=etlp,
                         esms=esms))
        ip.run()

        Draft.maybe_delete(draft['id'], request.user)
    except InboxError as thrown:
        message = thrown.message
    except Exception as thrown:
        message = "An unknown error has occurred and has been logged.  Contact your system administrator if the problem persists"
    else:
        result = True
        message = "Your Incident has been saved."
    finally:
        if thrown is not None:
            result = False
            save_crash('incident', thrown.message, traceback.format_exc())
    return {'success': result, 'message': message}




def apply_patch():
    WHICH_DBOBJ['inc'] = DBIncidentPatch
    views.incident_view = incident_view
    views.incident_build = incident_build
    views.ajax_create_incident = ajax_create_incident