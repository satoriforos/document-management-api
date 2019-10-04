from .ApiKey import ApiKey
from .Account import Account
from .IpAddress import IpAddress


class ApiAuthIpBannedError(Exception):
    pass

class ApiAuthNoApiKeyProvidedError(Exception):
    pass

class ApiAuthInvalidApiKeyError(Exception):
    pass


class ApiAuthAccountNotFoundError(Exception):
    pass


class ApiAuthAccountNotVerifiedError(Exception):
    pass


class ApiAuthAccountSuspendedError(Exception):
    pass


class ApiAuth:

    local_exclusions = [
    ]

    def __init__(self, database_manager):
        self.database_manager = database_manager

    def is_ip_banned(self, ip):
        result = False
        if ip is not None:
            if ip.is_banned is True or ip.is_banned == 1:
                result = True
        return result

    def is_valid_api_key(self, api_key):
        result = False
        if api_key is not None and api_key.id > 0:
            result = True
        return result

    def is_account_verified(self, account):
        result = False
        if account is not None:
            if account.is_email_verified is True or \
                    account.is_email_verified == 1:
                result = True
        return result

    def is_account_valid(self, account):
        result = False
        if account is not None and account.id > 0:
            result = True
        return result

    def is_account_suspended(self, account):
        result = False
        if account is not None:
            if account.is_suspended is True or account.is_suspended == 1:
                result = True
        return result

    def require_valid_auth(self, api_key_string, ip_string):
        output = {
            "api_key": None,
            "account": None,
            "ip": None
        }
        #ip = IpAddress(self.database_manager)
        ip = IpAddress.fetch_by_ip(self.database_manager, ip_string)
        if self.is_ip_banned(ip) is True:
            raise ApiAuthIpBannedError
        output["ip"] = ip

        api_key = ApiKey.fetch_by_api_key(
            self.database_manager,
            api_key_string
        )
        if api_key_string is None or api_key_string == "":
            raise ApiAuthNoApiKeyProvidedError
        if self.is_valid_api_key(api_key) is False:
            raise ApiAuthInvalidApiKeyError
        output["api_key"] = api_key

        account = Account.fetch_by_id(
            self.database_manager,
            api_key.account_id
        )
        if self.is_account_valid(account) is False:
            raise ApiAuthAccountNotFoundError
        if self.is_account_verified(account) is False:
            raise ApiAuthAccountNotVerifiedError
        if self.is_account_suspended(account) is True:
            raise ApiAuthAccountSuspendedError

        output["account"] = account
        return output
