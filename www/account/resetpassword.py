#!/usr/bin/env python3
import sys
sys.path.append("../../")
from jinja2 import Environment, select_autoescape, FileSystemLoader
from validate_email import validate_email
from os import environ
from settings.settings import settings
from modules.HttpServer import HttpServer
from modules.WebManager import WebManager
from modules.databasemanager.DatabaseManager import DatabaseManager
from modules.auth.Account import Account
from modules.courier.Courier import Courier


def get_database_connection(mysql_settings):
    database_manager = DatabaseManager(
        host=mysql_settings["server"],
        port=mysql_settings["port"],
        user=mysql_settings["username"],
        password=mysql_settings["password"],
        db=mysql_settings["schema"],
        charset=mysql_settings["charset"]
    )
    return database_manager


http_server = HttpServer(environ, sys.stdin)
database_manager = get_database_connection(settings["mysql"])
web_manager = WebManager(http_server, database_manager)

template_folder = '../templates'


def fetch_template(template_file):
    template_loader = FileSystemLoader(template_folder)
    env = Environment(
        loader=template_loader,
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(template_file)
    return template


def handle_get(http_server, database_manager, session, account):    
    template = fetch_template("account/resetpassword.jinja.htm")
    keys = {
        "email": "",
        "code": ""
    }
    required_keys = ["email", "code"]
    query_params = http_server.get_query_parameters()

    errors = []
    for required_key in required_keys:
        if required_key not in query_params or query_params[required_key] == "":
            errors.append(required_key)

    if len(errors) == 0:
        email = query_params["email"]
        reset_code = query_params["code"]
        keys["email"] = email
        keys["code"] = reset_code
        if validate_email(email) is False:
            errors.append("email")

    if len(errors) > 0:
        keys["get_error"] = True
        for key in errors:
            keys["error_{}".format(key)] = True

        output = template.render(keys)
        http_server.set_status(400)
        http_server.print_headers()
        print(output)

    else:
        retrieved_account = Account.fetch_by_email_and_password_reset_code(
            database_manager,
            email,
            reset_code
        )
        if retrieved_account is None:
            errors.append("email")
            keys["get_error"] = True
            keys["error_email"] = True
            output = template.render(keys)
            http_server.set_status(400)
            http_server.print_headers()
            print(output)
        else:
            http_server.set_status(200)
            http_server.print_headers()
            output = template.render(keys)
            print(output)


def handle_put_post(http_server, database_manager, session, account):    
    template = fetch_template("account/resetpassword.jinja.htm")
    keys = {
        "email": "",
        "code": ""
    }
    required_query_keys = ["email", "code"]
    required_post_keys = ["new_password", "verify_new_password"]
    query_params = http_server.get_query_parameters()

    errors = []
    for required_key in required_query_keys:
        if required_key not in query_params or query_params[required_key] == "":
            errors.append(required_key)
            keys["get_error"] = True

    post_params = http_server.get_post_parameters()
    for required_key in required_post_keys:
        if required_key not in post_params or post_params[required_key] == "":
            errors.append(required_key)

    if len(errors) == 0:
        email = query_params["email"]
        reset_code = query_params["code"]
        keys["email"] = email
        keys["code"] = reset_code
        password = post_params["new_password"]
        verify_password = post_params["verify_new_password"]
        if password != verify_password:
            errors.append("verify_new_password")
        if validate_email(email) is False:
            errors.append("email")
            keys["get_error"] = True

    if len(errors) > 0:
        keys["error"] = True
        for key in errors:
            keys["error_{}".format(key)] = True

        output = template.render(keys)
        http_server.set_status(400)
        http_server.print_headers()
        print(output)

    else:
        retrieved_account = Account.fetch_by_email_and_password_reset_code(
            database_manager,
            email,
            reset_code
        )
        if retrieved_account is None:
            errors.append("email")
            keys["get_error"] = True
            keys["error_email"] = True
            output = template.render(keys)
            http_server.set_status(400)
            http_server.print_headers()
            print(output)
        else:
            retrieved_account.password = password
            retrieved_account.password_reset_code = None
            retrieved_account.update()
            keys["update_success"] = True
            http_server.set_status(200)
            http_server.print_headers()
            output = template.render(keys)
            print(output)


web_manager.set_method_callback(
    WebManager.HTTP_METHOD_GET,
    handle_get
)


web_manager.set_method_callback(
    WebManager.HTTP_METHOD_PUT,
    handle_put_post
)


web_manager.set_method_callback(
    WebManager.HTTP_METHOD_POST,
    handle_put_post
)


web_manager.run()
