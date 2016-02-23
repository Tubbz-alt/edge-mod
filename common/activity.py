import pymongo
from datetime import datetime
from mongoengine.connection import get_db

VALID_STATES = ["FATAL", "ERROR", "WARN", "INFO", "DEBUG", "TRACE"]


def _activity_log():
    return get_db().certuk_activity


def save(user, category, state, message):
    _activity_log().save({
        'timestamp': datetime.utcnow(),
        'user': user,
        'category': category,
        'state': state if state in VALID_STATES else "INFO",
        'message': message
    })


def find(user=None, category=None, state=None, message=None, limit=20):
    query = {}
    if user and user != '*':
        query['user'] = {'$eq': user}
    if category and category != '*':
        query['category'] = {'$eq': category}
    if state and state in VALID_STATES:
        query['state'] = {'$eq': state}
    if message and message != '*':
        query['message'] = {'$regex': message}
    return [match for match in
            _activity_log().find(query, {'_id': 0}).sort('timestamp', pymongo.DESCENDING).limit(int(limit))]
