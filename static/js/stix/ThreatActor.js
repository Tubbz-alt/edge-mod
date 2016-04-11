define([
    "dcl/dcl",
    "knockout",
    "./ReviewValue",
    "./StixObjectTLP",
    "kotemplate!root-act:./templates/root-ThreatActor.html",
    "kotemplate!list-act:./templates/list-ThreatActors.html"
], function (declare, ko, ReviewValue, StixObjectTLP) {
    "use strict";

    return declare(StixObjectTLP, {
        constructor: function (data, stixPackage) {
            this.name = ko.computed(function () {
                return stixPackage.safeValueGet(this.id(), this.data(), "identity.name");
            }, this);
            this.types = ko.computed(function () {
                return stixPackage.safeListGet(this.id(), this.data(), "types", "value.value");
            }, this);
            this.motivations = ko.computed(function () {
                return stixPackage.safeListGet(this.id(), this.data(), "motivations", "value.value");
            }, this);
            this.sophistications = ko.computed(function () {
                return stixPackage.safeListGet(this.id(), this.data(), "sophistications", "value.value");
            }, this);
            this.intendedEffects = ko.computed(function () {
                return stixPackage.safeListGet(this.id(), this.data(), "intended_effects", "value.value");
            }, this);
            this.operationalSupports = ko.computed(function () {
                return stixPackage.safeListGet(this.id(), this.data(), "planning_and_operational_supports", "value.value");
            }, this);
            this.observedTTPs = ko.computed(function () {
                return stixPackage.safeReferenceArrayGet(this.id(), this.data(), "observed_ttps.ttps", "ttp.idref");
            }, this);
            this.associatedActors = ko.computed(function () {
                return stixPackage.safeReferenceArrayGet(this.id(), this.data(), "associated_actors.threat_actors", "threat_actor.idref");
            }, this);
            this.associatedCampaigns = ko.computed(function () {
                return stixPackage.safeReferenceArrayGet(this.id(), this.data(), "associated_campaigns.campaigns", "campaign.idref");
            }, this);
        }
    });
});
