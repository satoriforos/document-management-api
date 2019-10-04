from modules.DatabaseObject import DatabaseObject
import hashlib
import time
from datetime import datetime
from calendar import monthrange
from datetime import date


class Account(DatabaseObject):

    local_exclusions = [
        'password'
    ]

    id = None
    from_registration_id = None
    first_name = None
    last_name = None
    company_name = None
    email = None
    is_marketing_ok = None
    is_email_verified = None
    is_suspended = None
    phone = None
    is_phone_verified = None
    hashed_password = None
    password = None
    password_salt = None
    password_reset_code = None
    discount_code = None
    stripe_customer_id = None
    stripe_source_id = None
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

    def get_next_billing_date(self):
        today = datetime.now()
        billing_year = today.year
        billing_month = today.month
        billing_day = self.billing_day
        if today.day >= self.billing_day:
            billing_month = billing_month + 1
            if billing_month > 12:
                billing_year = billing_year + 1
                billing_month = 1
        month_range = monthrange(2012, billing_month)
        num_days_in_month = month_range[1]
        if billing_day > num_days_in_month:
            billing_day = num_days_in_month
        billing_date = date(billing_year, billing_month, billing_day)
        return billing_date

    def from_dict(self, database_manager, data):
        exclusions = self.local_exclusions + [
            'database_manager',
            'local_exclusions',
            'confirmation_code',
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
        if 'is_email_verified' in data and isinstance(data['is_email_verified'], int):
            self.is_email_verified = DatabaseObject.get_boolean_from_string(
                data["is_email_verified"]
            )
        if 'is_suspended' in data and isinstance(data['is_suspended'], int):
            self.is_suspended = DatabaseObject.get_boolean_from_string(
                data["is_suspended"]
            )

    @staticmethod
    def from_registration(account_registration):
        account_registration_dict = dict(account_registration)
        account_registration_dict["from_registration_id"] = account_registration_dict["id"]
        del(account_registration_dict["id"])
        account = Account(account_registration.database_manager)
        account.from_dict(
            account_registration.database_manager,
            account_registration_dict
        )
        account.is_email_verified = True
        return account

    def generate_password_reset_code(self):
        self.password_reset_code = hashlib.md5(
            str(time.time()).encode("utf-8")
        ).hexdigest()
        return self.password_reset_code

    @staticmethod
    def generate_salt():
        return hashlib.md5(str(time.time()).encode("utf-8")).hexdigest()

    def does_password_match(self, password):
        verify_password_hash = Account.hash_password(
            password,
            self.password_salt
        )
        return self.hashed_password == verify_password_hash

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
        return Account.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by_email(database_manager, email):
        conditions = [{
            "column": "email",
            "equivalence": "=",
            "value": email
        }]
        return Account.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by_email_and_password(
        database_manager,
        email,
        password
    ):
        possible_account = Account.fetch_by_email(database_manager, email)
        if possible_account is not None:
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
            return Account.fetch_by(database_manager, conditions)

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
        return Account.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by_email_and_password_reset_code(
        database_manager,
        email,
        password_reset_code
    ):
        conditions = [
            {
                "column": "email",
                "equivalence": "=",
                "value": email
            },
            {
                "column": "password_reset_code",
                "equivalence": "=",
                "value": password_reset_code
            },
        ]
        return Account.fetch_by(database_manager, conditions)

    @staticmethod
    def fetch_by_from_registration_id(database_manager, from_registration_id):
        conditions = [{
            "column": "from_registration_id",
            "equivalence": "=",
            "value": from_registration_id
        }]
        return Account.fetch_by(database_manager, conditions)        

    @staticmethod
    def fetch_by(database_manager, conditions):
        obj_template = Account(database_manager)
        results = database_manager.fetch_by(
            obj_template,
            conditions,
            num_rows=1
        )
        if len(results) > 0:
            obj = results[0]
            return obj
