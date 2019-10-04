from modules.DatabaseObject import DatabaseObject


class IpAddress(DatabaseObject):

    local_exclusions = [
    ]

    id = None
    ip = None
    is_banned = False
    ctime = None
    mtime = None

    def __init__(self, database_manager):
        self.database_manager = database_manager

    @staticmethod
    def fetch_by_ip(database_manager, ip_string):
        conditions = [{
            "column": "ip",
            "equivalence": "=",
            "value": ip_string
        }]
        return IpAddress.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by(database_manager, conditions):
        obj_template = IpAddress(database_manager)
        results = database_manager.fetch_by(
            obj_template,
            conditions,
            num_rows=1
        )
        if len(results) > 0:
            obj = results[0]
            return obj

    def from_dict(self, database_manager, data):
        super.from_dict(database_manager, data)
        if 'is_banned' in data:
            self.is_banned = DatabaseObject.get_boolean_from_string(
                data["is_banned"]
            )
