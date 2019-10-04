from modules.auth.Session import Session
from modules.auth.Account import Account


class WebManager:

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
    session = None
    account = None
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

    def __init__(self, http_server, database_manager):
        self.http_server = http_server
        self.http_server.set_header('Content-Type', "text/html")
        self.database_manager = database_manager

    def is_logged_in(self):
        http_server = self.http_server
        database_manager = self.database_manager

        is_logged_in = False
        cookie_slug = http_server.get_cookie("session_id")
        if cookie_slug is not None:
            if self.session is None:
                self.session = Session.fetch_by_slug(
                    database_manager,
                    cookie_slug
                )
            if self.session is not None and self.session.is_expired() is False:
                if self.account is None:
                    self.account = Account.fetch_by_id(
                        database_manager,
                        self.session.account_id)
                if self.account is not None and self.account.is_suspended == 0 and self.account.is_closed == 0:
                    is_logged_in = True

        return is_logged_in

    def require_login(self, callback=None):
        http_server = self.http_server
        is_logged_in = self.is_logged_in()
        if is_logged_in is False:
            if callback is None:
                http_server.set_status(403)
                http_server.set_header('Content-Type', "text/html")
                http_server.print_headers()
            else:
                callback(
                    self.http_server,
                    self.database_manager,
                    self.session,
                    self.account
                )
        return is_logged_in

    def set_method_callback(self, method, callback):
        self.method_callbacks[method] = callback
        self.set_allowed_methods()

    def run(self):
        http_server = self.http_server
        method = http_server.get_method()
        callback_found = False
        if method in self.method_callbacks:
            if self.method_callbacks[method] is not None:
                callback_found = True
                self.method_callbacks[method](
                    self.http_server,
                    self.database_manager,
                    self.session,
                    self.account
                )
        if callback_found is False:
            if method == self.HTTP_METHOD_OPTIONS:
                self.run_default_options()
            else:
                if self.default_method_callback is None:
                    self.run_default_error()
                else:
                    self.default_method_callback()

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

    def run_default_error(self):
        http_server = self.http_server
        http_server.set_status(405)
        http_server.print_headers()
