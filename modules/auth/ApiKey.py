from modules.DatabaseObject import DatabaseObject
import hashlib
import time

class ApiKey(DatabaseObject):
    
    local_exclusions = [
        'password'
    ]

    id = None
    account_id = None
    api_key = None
    api_secret = None
    total_requests = 0
    last_request_minute_start_ts = 0
    last_request_month_start_ts = 0
    allowed_requests_per_minute = None
    allowed_requests_per_month = None
    access_control_allow_origin = None
    ctime = None
    mtime = None

    def __init__(self, database_manager):
        self.database_manager = database_manager

    @staticmethod
    def fetch_by_api_key(database_manager, api_key_string):
        conditions = [{
            "column": "api_key",
            "equivalence": "=",
            "value": api_key_string
        }]
        return ApiKey.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by_account_id(database_manager, account_id):
        conditions = [{
            "column": "account_id",
            "equivalence": "=",
            "value": account_id
        }]
        return ApiKey.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by(database_manager, conditions):
        obj_template = ApiKey(database_manager)
        results = database_manager.fetch_by(
            obj_template,
            conditions,
            num_rows=1
        )
        if len(results) > 0:
            obj = results[0]
            return obj

    def increment_requests(self):
        self.total_requests += 1
        self.update()

    def generate_key(self):
        prefix = "k_"
        key = "{}{}".format(
            prefix,
            hashlib.md5(str(time.time()).encode("utf-8")).hexdigest()
        )
        self.api_key = key
        return self.api_key

    def generate_secret(self):
        prefix = "s_"
        key = "{}{}".format(
            prefix,
            hashlib.md5(str(time.time()).encode("utf-8")).hexdigest()
        )
        self.api_secret = key
        return self.api_secret

    def update_plan(self, subscription_plan):
        self.allowed_requests_per_minute = \
            subscription_plan.allowed_requests_per_minute
        self.allowed_requests_per_month = \
            subscription_plan.allowed_requests_per_month
