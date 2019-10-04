from modules.auth.ApiAuth import ApiAuth
from modules.auth.ApiAuth import ApiAuthAccountSuspendedError
from modules.auth.ApiAuth import ApiAuthIpBannedError
from modules.auth.ApiAuth import ApiAuthNoApiKeyProvidedError
from modules.auth.ApiAuth import ApiAuthInvalidApiKeyError
from modules.auth.ApiAuth import ApiAuthAccountNotFoundError
from modules.auth.ApiAuth import ApiAuthAccountNotVerifiedError
from .RateCalculator import RateCalculator
from .RateCalculator import RateCalculatorOverLimitError


class ApiManager:

    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS, DELETE, PUT",
        "Access-Control-Allow-Headers": "x-requested-with, Content-Type, origin, authorization, accept, client-security-token"
    }

    HTTP_METHOD_GET = "GET"
    HTTP_METHOD_PUT = "PUT"
    HTTP_METHOD_POST = "POST"
    HTTP_METHOD_DELETE = "DELETE"

    HTTP_METHOD_HEAD = "HEAD"
    HTTP_METHOD_OPTIONS = "OPTIONS"

    HTTP_METHOD_CONNECT = "CONNECT"
    HTTP_METHOD_TRACE = "TRACE"

    http_server = None
    database_manager = None
    ip = None
    api_key = None
    account = None
    json_response = None
    method_callbacks = {
        "GET": None,
        "DELETE": None,
        "PUT": None,
        "POST": None,
        "HEAD": None,
        "OPTIONS": None,
        "CONNECT": None,
        "TRACE": None,
    }
    default_method_callback = None
    require_auth = False
    require_auth_callback = None

    def __init__(self, http_server, database_manager):
        self.http_server = http_server
        for key, value in self.default_headers.items():
            self.http_server.set_header(
                key, value
            )
        self.database_manager = database_manager

    def check_auth(self):
        do_proceed = True
        http_server = self.http_server
        database_manager = self.database_manager

        auth = http_server.get_authorization()
        api_key_string = auth["username"]
        ip_string = http_server.get_remote_address()
        api_auth = ApiAuth(database_manager)
        auth_failed = False
        try:
            auth_details = api_auth.require_valid_auth(
                api_key_string,
                ip_string
            )

        except ApiAuthAccountSuspendedError:
            http_server.set_status(403)
            self.json_response = {"error": "Your account has been suspended."}
            auth_failed = True
            do_proceed = False

        except ApiAuthIpBannedError:
            http_server.set_status(403)
            self.json_response = {"error": "Your IP addresss has been banned."}
            auth_failed = True
            do_proceed = False

        except ApiAuthNoApiKeyProvidedError:
            http_server.set_status(403)
            self.json_response = {"error": "You must provide an API key."}
            auth_failed = True
            do_proceed = False

        except ApiAuthInvalidApiKeyError:
            http_server.set_status(401)
            self.json_response = {
                "error":
                "Invalid API Key. Please create an API Key."
            }
            auth_failed = True
            do_proceed = False

        except ApiAuthAccountNotFoundError:
            http_server.set_status(401)
            self.json_response = {"error": "Invalid account. Please register."}
            auth_failed = True
            do_proceed = False

        except ApiAuthAccountNotVerifiedError:
            http_server.set_status(401)
            self.json_response = {
                "error": (
                    "Your account has not been verified. "
                    "Please complete the email verification process"
                )
            }
            auth_failed = True
            do_proceed = False

        if auth_failed is False:
            api_key = auth_details["api_key"]

            if api_key.access_control_allow_origin is not None:
                self.http_server.set_header(
                    "Access-Control-Allow-Origin",
                    api_key.access_control_allow_origin
                )
                
            self.api_key = api_key
            self.ip = auth_details["ip"]
            self.account = auth_details["account"]

            minute_rate_calculator = RateCalculator(
                api_key.allowed_requests_per_minute,
                RateCalculator.S_TO_MINUTE,
                api_key.total_requests,
                api_key.last_request_minute_start_ts
            )
            try:
                minute_rate_calculator.increment_transactions()
            except RateCalculatorOverLimitError:
                http_server.set_status(429)
                self.json_response = {
                    "error": (
                        "You have exceeded your rate limit of "
                        "{} transactions per minute".format(
                            str(api_key.allowed_requests_per_minute)
                        )
                    )
                }
                do_proceed = False

            month_rate_calculator = RateCalculator(
                api_key.allowed_requests_per_month,
                RateCalculator.S_TO_MONTH,
                api_key.total_requests,
                api_key.last_request_month_start_ts
            )
            try:
                month_rate_calculator.increment_transactions()
            except RateCalculatorOverLimitError:
                http_server.set_status(429)
                self.json_response = {
                    "error": (
                        "You have exceeded your total monthly transactions. "
                        "Please upgrade your package."
                    )
                }
                do_proceed = False

        return do_proceed

    def set_method_callback(self, method, callback):
        self.method_callbacks[method] = callback
        self.set_allowed_methods()

    def require_auth(self, callback=None):
        self.require_auth = True
        if callback is not None:
            self.require_auth_callback = callback

    def run(self):
        http_server = self.http_server
        method = http_server.get_method()
        callback_found = False
        callback = None
        if method in self.method_callbacks:
            if self.method_callbacks[method] is not None:
                callback_found = True
                callback = self.method_callbacks[method]
        if callback_found is False:
            if method == self.HTTP_METHOD_OPTIONS:
                callback = self.run_default_options
            else:
                if self.default_method_callback is None:
                    callback = self.run_default_error
                else:
                    callback = self.default_method_callback
        do_proceed = True
        if self.require_auth is True and \
                http_server.get_method() != "OPTIONS":
            do_proceed = self.check_auth()
            if do_proceed is False:
                if self.require_auth_callback is None:
                    self.run_default_auth_error()
                else:
                    self.require_auth_callback()
        if do_proceed is True:
            callback(
                self.http_server,
                self.database_manager,
                self.ip,
                self.account,
                self.api_key
                )

    def set_allowed_methods(self):
        http_server = self.http_server
        allowed_methods = [self.HTTP_METHOD_OPTIONS]
        for key, value in self.method_callbacks.items():
            if value is not None:
                if key not in allowed_methods:
                    allowed_methods.append(key)
        http_server.set_header(
            "Access-Control-Allow-Methods",
            ", ".join(allowed_methods)
        )

    def run_default_options(self, h, d, i, a, p):
        allowed_methods = ["OPTIONS"]
        for method, callback in self.method_callbacks.items():
            if callback is not None:
                allowed_methods.append(method)
        allowed_methods = set(allowed_methods)
        self.http_server.set_header(
            "Access-Control-Allow-Methods",
            ", ".join(allowed_methods)
        )
        http_server = self.http_server
        http_server.set_status(200)
        http_server.print_headers()

    def run_default_error(self, h, d, i, a, p):
        http_server = self.http_server
        http_server.set_status(405)
        http_server.print_headers()
        self.json_response = {"error": "method not found"}
        http_server.print_json(self.json_response)

    def run_default_auth_error(self):
        http_server = self.http_server
        do_proceed = self.check_auth()
        if do_proceed is False:
            http_server.print_headers()
            http_server.print_json(self.json_response)
