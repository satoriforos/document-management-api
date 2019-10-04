from modules.DatabaseObject import DatabaseObject
import hashlib
import time
from datetime import datetime
from datetime import timedelta


class Session(DatabaseObject):

    local_exclusions = ["expires"]

    id = None
    slug = None
    data = None
    expires = None
    ctime = None
    mtime = None

    def __init__(self, database_manager):
        self.database_manager = database_manager

    def generate_slug(self):
        return hashlib.md5(str(time.time()).encode("utf-8")).hexdigest()

    def set_expiration_seconds_from_now(self, seconds_from_now):
        now = datetime.now()
        self.expires = now + timedelta(seconds=seconds_from_now)

    def set_expiration_minutes_from_now(self, minutes_from_now):
        now = datetime.now()
        self.expires = now + timedelta(minutes=minutes_from_now)

    def set_expiration_days_from_now(self, days_from_now):
        now = datetime.now()
        self.expires = now + timedelta(days=days_from_now)

    def expire(self):
        now = datetime.now()
        self.expires = now

    def is_expired(self):
        now = datetime.now()
        is_expired = False
        if self.expires is not None:
            if self.expires < now:
                is_expired = True
        return is_expired

    def from_dict(self, database_manager, data):
        exclusions = self.local_exclusions + [
            'database_manager',
            'local_exclusions',
            'expires',
            'ctime',
            'mtime'
        ]
        self.database_manager = database_manager
        for key, value in data.items():
            if key not in exclusions:
                setattr(self, key, value)
        if 'ctime' in data and isinstance(data['ctime'], str):
            self.ctime = DatabaseObject.get_datetime_from_string(
                data['ctime']
            )
        if 'mtime' in data and isinstance(data['mtime'], str):
            self.mtime = DatabaseObject.get_datetime_from_string(
                data['mtime']
            )
        if 'expires' in data and isinstance(data['expires'], str):
            self.mtime = DatabaseObject.get_datetime_from_string(
                data['expires']
            )

    def to_dict(self):
        exclusions = self.local_exclusions + [
            'database_manager',
            'local_exclusions',
            'ctime',
            'mtime'
        ]
        data = {}
        for property, value in vars(self).iteritems():
            if property not in exclusions:
                    data[property] = value

        if 'ctime' in data and isinstance(data['ctime'], datetime):
            self.ctime = DatabaseObject.get_datetime_from_string(
                data['ctime']
            )
        if 'mtime' in data and isinstance(data['mtime'], datetime):
            self.mtime = DatabaseObject.get_datetime_from_string(
                data['mtime']
            )
        if 'expires' in data and isinstance(data['expires'], datetime):
            self.mtime = DatabaseObject.get_datetime_from_string(
                data['expires']
            )

        return data

    @staticmethod
    def fetch_by_id(database_manager, id):
        conditions = [{
            "column": "id",
            "equivalence": "=",
            "value": id
        }]
        return Session.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by_slug(database_manager, slug):
        conditions = [{
            "column": "slug",
            "equivalence": "=",
            "value": slug
        }]
        return Session.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by_email(database_manager, email):
        conditions = [{
            "column": "email",
            "equivalence": "=",
            "value": email
        }]
        return Session.fetch_by(database_manager, conditions)
   
    @staticmethod
    def fetch_by(database_manager, conditions):
        obj_template = Session(database_manager)
        results = database_manager.fetch_by(
            obj_template,
            conditions,
            num_rows=1
        )
        if len(results) > 0:
            obj = results[0]
            return obj
