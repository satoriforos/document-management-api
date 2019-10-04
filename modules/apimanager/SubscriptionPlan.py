from modules.DatabaseObject import DatabaseObject


class SubscriptionPlan(DatabaseObject):

    local_exclusions = [
        'password'
    ]

    id = None
    name = None
    currency = None
    allowed_requests_per_minute = None
    allowed_requests_per_month = None
    is_active = None
    ctime = None
    mtime = None

    def __init__(self, database_manager):
        self.database_manager = database_manager

    @staticmethod
    def fetch_by_id(database_manager, id):
        conditions = [{
            "column": "id",
            "equivalence": "=",
            "value": id
        }]
        return SubscriptionPlan.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by_name(database_manager, name):
        conditions = [{
            "column": "name",
            "equivalence": "=",
            "value": name
        }]
        return SubscriptionPlan.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by(database_manager, conditions):
        obj_template = SubscriptionPlan(database_manager)
        results = database_manager.fetch_by(
            obj_template,
            conditions,
            num_rows=1
        )
        if len(results) > 0:
            obj = results[0]
            return obj
