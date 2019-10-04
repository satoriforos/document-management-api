from .DatabaseObject import DatabaseObject


class PdfData(DatabaseObject):

    local_exclusions = []

    id = None
    account_id = None
    slug = None
    name = None
    data = None
    ctime = None
    mtime = None

    def generate_slug(self):
        return hashlib.md5(str(time.time()).encode("utf-8")).hexdigest()

    @staticmethod
    def fetch_by_name_and_account_id(self, name, account_id):
        conditions = [
            {
                "column": "name",
                "equivalence": "=",
                "value": name
            }, {
                "column": "account_id",
                "equivalence": "=",
                "value": account_id
            }
        ]
        return PdfData.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by(database_manager, conditions):
        obj_template = PdfData(database_manager)
        results = database_manager.fetch_by(
            obj_template,
            conditions,
            num_rows=1
        )
        if len(results) > 0:
            obj = results[0]
            return obj
