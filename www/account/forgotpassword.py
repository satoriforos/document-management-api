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
from urllib.parse import urlencode, quote_plus


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
    template = fetch_template("account/forgotpassword.jinja.htm")
    keys = {
    }
    output = template.render(keys)
    http_server.print_headers()
    print(output)


def handle_put_post(http_server, database_manager, session, account):
    template = fetch_template("account/forgotpassword.jinja.htm")
    keys = {}
    required_keys = ["email"]
    post_params = http_server.get_post_parameters()
    errors = []
    for required_key in required_keys:
        if required_key not in post_params or post_params[required_key] == "":
            errors.append(required_key)

    if len(errors) == 0:
        email = post_params["email"]
        if validate_email(email) is False:
            errors.append("email")

    if len(errors) > 0:
        for key in errors:
            keys["error_{}".format(key)] = True

        output = template.render(keys)
        http_server.set_status(400)
        http_server.print_headers()
        print(output)

    else:
        retrieved_account = Account.fetch_by_email(
            database_manager,
            email
        )
        if retrieved_account is None:
            errors.append("email")
            keys["error_email"] = True
            output = template.render(keys)
            http_server.set_status(400)
            http_server.print_headers()

            print(output)
        else:
            reset_code = retrieved_account.generate_password_reset_code()
            courier = Courier(settings["sendgrid"])
            from_email = settings["email"]["from"]["email"]
            subject = "Confirm your account"
            template_id = "d-4720041c99d548bcba55f02dc9609de7"
            substitutions = {"code": reset_code, "email": email}
            response = courier.send_template_email(
                email,
                from_email,
                subject,
                template_id,
                substitutions
            )
            if response.status_code != 202:
                errors += ["email_delivery"]
                keys["errors"] = errors
                for error in errors:
                    keys["error_{}".format(error)] = True
                output = template.render(keys)
                # http_server.set_status(400)
                http_server.print_headers()
                print(output)
            else:
                retrieved_account.update()
                keys["success"] = True
                keys["email"] = post_params["email"]
                http_server.set_status(200)
                http_server.print_headers()
                output = template.render(keys)
                print(output)


web_manager.set_method_callback(
    WebManager.HTTP_METHOD_GET,
    handle_get
)


web_manager.set_method_callback(
    WebManager.HTTP_METHOD_POST,
    handle_put_post
)


web_manager.set_method_callback(
    WebManager.HTTP_METHOD_PUT,
    handle_put_post
)


web_manager.run()
