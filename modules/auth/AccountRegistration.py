from modules.DatabaseObject import DatabaseObject
from .Account import Account
import hashlib
import time


class AccountRegistration(DatabaseObject):

    local_exclusions = [
        'password'
    ]

    id = None
    first_name = None
    last_name = None
    company_name = None
    email = None
    is_marketing_ok = None
    is_email_verified = None
    confirmation_code = None
    phone = None
    is_phone_verified = None
    hashed_password = None
    password = None
    password_salt = None
    discount_code = None
    stripe_source_id = None
    stripe_customer_id = None
    subscription_plan_id = None
    billing_year = None
    billing_month = None
    billing_day = None
    billing_interval = None
    ctime = None
    mtime = None

    def __init__(self, database_manager):
        self.database_manager = database_manager

    def update_hashed_password(self):
        if self.password is not None:
            self.password_salt = Account.generate_salt()
            self.hashed_password = Account.hash_password(
                self.password,
                self.password_salt
            )

    def insert_if_not_exists(self):
        self.update_hashed_password()
        self.id = self.database_manager.insert_if_not_exists(self)
        return self.id

    def save(self):
        self.update_hashed_password()
        self.id = self.database_manager.save(self)
        return self.id

    def insert(self):
        self.update_hashed_password()
        self.id = self.database_manager.insert(self)
        return self.id

    def update(self):
        self.update_hashed_password()
        result = self.database_manager.update(self)
        return result

    def from_dict(self, database_manager, data):
        super.from_dict(database_manager, data)
        if 'is_email_verified' in data:
            self.is_email_verified = DatabaseObject.get_string_from_boolean(
                data["is_email_verified"]
            )

    def generate_confirmation_code(self):
        self.confirmation_code = hashlib.md5(
            str(time.time()).encode("utf-8")
        ).hexdigest()
        return self.confirmation_code

    @staticmethod
    def generate_salt():
        return hashlib.md5(str(time.time()).encode("utf-8")).hexdigest()

    @staticmethod
    def hash_password(password, salt):
        hashed_password = hashlib.sha256(
            salt.encode() + password.encode()
        ).hexdigest()
        return hashed_password

    @staticmethod
    def fetch_by_id(database_manager, id):
        conditions = [{
            "column": "id",
            "equivalence": "=",
            "value": id
        }]
        return AccountRegistration.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by_email(database_manager, email):
        conditions = [{
            "column": "email",
            "equivalence": "=",
            "value": email
        }]
        return AccountRegistration.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by_confirmation_code(database_manager, confirmation_code):
        conditions = [{
            "column": "confirmation_code",
            "equivalence": "=",
            "value": confirmation_code
        }]
        return AccountRegistration.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by_email_and_confirmation_code(
        database_manager,
        email,
        confirmation_code
    ):
        conditions = [
            {
                "column": "email",
                "equivalence": "=",
                "value": email
            }, {
                "column": "confirmation_code",
                "equivalence": "=",
                "value": confirmation_code

            }
        ]
        return AccountRegistration.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by_email_password_and_confirmation_code(
        database_manager,
        email,
        password,
        confirmation_code
    ):
        possible_account = Account.fetch_by_email_and_confirmation_code(
            database_manager,
            email,
            confirmation_code
        )
        if possible_account.id is not None:
            salt = possible_account.password_salt
            hashed_password = Account.hash_password(password, salt)
            conditions = [
                {
                    "column": "email",
                    "equivalence": "=",
                    "value": email
                }, {
                    "column": "hashed_password",
                    "equivalence": "=",
                    "value": hashed_password
                }, {
                    "column": "confirmation_code",
                    "equivalence": "=",
                    "value": confirmation_code

                }
            ]
            return AccountRegistration.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by_email_and_password(
        database_manager,
        email,
        password
    ):
        possible_account = Account.fetch_by_email(database_manager, email)
        if possible_account.id is not None:
            salt = possible_account.password_salt
            hashed_password = Account.hash_password(password, salt)
            conditions = [
                {
                    "column": "email",
                    "equivalence": "=",
                    "value": email
                },
                {
                    "column": "hashed_password",
                    "equivalence": "=",
                    "value": hashed_password
                },
            ]
            return AccountRegistration.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by_email_and_hashed_password(
        database_manager,
        email,
        hashed_password
    ):
        conditions = [
            {
                "column": "email",
                "equivalence": "=",
                "value": email
            },
            {
                "column": "hashed_password",
                "equivalence": "=",
                "value": hashed_password
            },
        ]
        return AccountRegistration.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by(database_manager, conditions):
        obj_template = AccountRegistration(database_manager)
        results = database_manager.fetch_by(
            obj_template,
            conditions,
            num_rows=1
        )
        if len(results) > 0:
            obj = results[0]
            return obj
