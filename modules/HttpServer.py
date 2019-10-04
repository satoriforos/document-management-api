import json
from urllib import parse
import base64
from http import cookies
import cgi
import re
from urllib.parse import parse_qs


class HttpServer:
    request_headers = {}
    response_headers = {
        "Status": "200 OK",
    }
    post_params = {}
    files = {}
    payload = None
    STATUS_CODES = {
        100: "Continue",
        101: "Switching Protocols",
        102: "Processing",
        103: "Early Hints",
        200: "OK",
        201: "Created",
        202: "Accepted",
        203: "Non-Authoritative Information",
        204: "No Content",
        205: "Reset Content",
        206: "Partial Content",
        207: "Multi-Status",
        208: "Already Reported",
        226: "IM Used",
        300: "Multiple Choices",
        301: "Moved Permanently",
        302: "Found",
        303: "See Other",
        304: "Not Modified",
        305: "Switch Proxy",
        307: "Temporary Redirect",
        308: "Permanent Redirect",
        400: "Bad Request",
        401: "Unauthorized",
        402: "Payment Required",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        406: "Not Acceptable",
        407: "Proxy Authentication Required",
        408: "Request",
        409: "Conflict",
        410: "Gone",
        411: "Length Required",
        412: "Precondition Failed",
        413: "Payload Too Large",
        414: "URI Too Long",
        415: "Unnsupported Media Type",
        416: "Range Not Satisfiable",
        417: "Expectation Failed",
        429: "Too Many Requests",

        500: "Internal Server Error",
        501: "Not Implemented",
        502: "Service Unavailable"
    }

    def __init__(self, environ, payload):
        self.environ = environ
        self.payload = payload
        self.query_string = self.environ.get("QUERY_STRING")
        self.cookies = self.get_cookies()
        keys = list(environ.keys())
        for key in keys:
            self.request_headers[key] = environ.get(key)
        self.process_post_data()

    def process_post_data(self):
        raw_post_body = self.payload
        if "CONTENT_TYPE" in self.request_headers:
            content_type = self.request_headers["CONTENT_TYPE"]
            if "multipart/form-data" in content_type.lower():
                form_body = self.get_multipart_form_body()
                if form_body is not None:
                    for row in form_body:
                        is_file = "; filename=\"" in row["headers"][
                            "Content-Disposition"
                        ]
                        if is_file is True:
                            file_data = self.get_file_from_multipart(row)
                            self.files[file_data["name"]] = file_data
                        else:
                            key, value = \
                                self.get_post_key_value_from_multipart(row)
                            self.post_params[key] = value
            elif "application/x-www-form-urlencoded" in content_type.lower():
                if raw_post_body != "":
                    params = parse_qs(raw_post_body)
                    self.post_params = {
                        key: value[0] for key, value in params.items()
                    }

    def get_post_key_value_from_multipart(self, data):
        key = self.get_field_name_from_multipart_form_data(
            data["headers"]["Content-Disposition"]
        )
        value = data["body"]
        return key, value

    def get_post_body(self):
        return self.raw_post_body

    def get_field_name_from_multipart_form_data(self, content_disposition):
        keys = re.findall(
            r'form-data; name=\"([^\"]+)\"',
            content_disposition
        )
        key = keys[0]
        return key

    def get_file_from_multipart(self, data):
        filename_matches = re.findall(
            r"filename=\"([^\"]+)\"",
            data["headers"]["Content-Disposition"]
        )
        file_name = filename_matches[0]
        name_matches = re.findall(
            r"; name=\"([^\"]+)\"",
            data["headers"]["Content-Disposition"]
        )
        name = name_matches[0]
        file_data = data["body"]
        mime_type = None
        if "Content-Type" in data["headers"]:
            mime_type = data["headers"]["Content-Type"]
        output = {
            "name": name,
            "file_name": file_name,
            "mime_type": mime_type,
            "data": file_data
        }
        return output

    def get_file(self, input_name):
        response = None
        if input_name in self.files:
            response = self.files[input_name]
        return response

    def get_multipart_form_body(self):
        body = []
        boundary = None
        if "CONTENT_TYPE" in self.request_headers:
            content_type = self.request_headers["CONTENT_TYPE"]
            if "multipart/form-data" in content_type.lower():
                boundary = content_type[len("multipart/form-data; boundary="):]

        raw_post_body = self.get_post_body()
        if boundary is not None and \
                raw_post_body is not None and \
                raw_post_body != "":
            post_sections = raw_post_body.split(boundary)

            for post_section in post_sections:
                if "\r\n\r\n" in post_section:
                    form_info = {"headers": {}, "body": None}
                    headers_body = post_section.split("\r\n\r\n", 1)
                    form_info["body"] = headers_body[1].strip()[:-len(
                        "--\r\n"
                    )]
                    for key_value in headers_body[0].split("\r\n"):
                        if ": " in key_value:
                            kv = key_value.split(": ", 1)
                            form_info["headers"][kv[0]] = kv[1]
                    body.append(form_info)
        return body

    def get_method(self):
        method = self.environ.get("REQUEST_METHOD")
        if method is None:
            method = "GET"
        else:
            method = method.upper()
        return method

    def get_request_header(self, key):
        return self.environ.get(key)

    def get_remote_address(self):
        return self.environ.get("REMOTE_ADDR")

    def get_authorization(self):
        authorization = {
            "type": "",
            "username": "",
            "password": ""
        }
        raw_authentication = self.environ.get("HTTP_AUTHORIZATION")
        if raw_authentication is not None and raw_authentication != "":
            split_authorization = raw_authentication.split(" ", 1)
            if len(split_authorization) > 0:
                authorization["type"] = split_authorization[0]
                user_pass = base64.decodestring(
                    split_authorization[1].encode("utf-8")
                ).decode("utf-8")
                if ":" in user_pass:
                    split_user_pass = user_pass.split(":", 1)
                    authorization["username"] = split_user_pass[0]
                    authorization["password"] = split_user_pass[1]
                else:
                    authorization["username"] = user_pass
        return authorization

    def get_query_string(self):
        query_string = self.environ.get("QUERY_STRING")
        return query_string

    def get_query_parameters(self):
        query_params = []
        if self.query_string is not None:
            raw_query_params = dict(parse.parse_qsl(
                self.query_string
            ))
            query_params = {}
            for key, value in raw_query_params.items():
                if value.lower() == "true":
                    query_params[key] = True
                elif value.lower() == "false":
                    query_params[key] = False
                else:
                    query_params[key] = value
        return query_params

    def get_post_parameters(self):
        form = cgi.FieldStorage()
        post_parameters = {}
        keys = form.keys()
        for key in keys:
            post_parameters[key] = form.getvalue(key)
        return post_parameters

    def get_post_json(self):
        post_data = {}
        try:
            post_data = json.load(self.payload)
        except Exception:
            pass
        return post_data

    def print_headers(self):
        for key, value in self.response_headers.items():
            print("{}: {}".format(key, value))
        print(self.cookies)
        print("")

    def print_json(self, data):
        print(json.dumps(data, indent=3))

    def set_header(self, key, value):
        self.response_headers[key] = value

    def set_status(self, code):
        self.response_headers["Status"] = "{} {}".format(
            str(code), self.STATUS_CODES[code]
        )

    def get_cookies(self):
        http_cookies = cookies.SimpleCookie()
        cookie_string = self.environ.get("HTTP_COOKIE")
        if cookie_string is not None and cookie_string != "":
            http_cookies.load(cookie_string)
        return http_cookies

    def get_cookie(self, key, default_value=None):
        return_value = default_value
        try:
            return_value = self.cookies[key].value
        except Exception:
            pass
        return return_value

    def set_cookie(self, key, value):
        self.cookies[key] = value

    def delete_cookie(self, key):
        self.cookies[key] = ""
        self.cookies[key]['expires'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
