#!/usr/bin/env python3
import sys
sys.path.append("../../")
from jinja2 import Environment, select_autoescape, FileSystemLoader
from os import environ
from validate_email import validate_email
from settings.settings import settings
from modules.HttpServer import HttpServer
from modules.WebManager import WebManager
from modules.databasemanager.DatabaseManager import DatabaseManager
from modules.auth.Account import Account
from modules.auth.Session import Session


settings["login_page"] = {
    "session_timeout_days": 14,
    "default_redirect": "/account/",
    "templates_folder": "../templates"
}


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


def fetch_template(template_file):
    template_loader = FileSystemLoader(
        settings["login_page"]["templates_folder"]
    )
    env = Environment(
        loader=template_loader,
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(template_file)
    return template


def handle_get(http_server, database_manager, session, account):
    template = fetch_template("account/signin.jinja.htm")
    keys = {
    }
    output = template.render(keys)
    http_server.print_headers()
    print(output)


def handle_put_post(http_server, database_manager, session, account):
    template = fetch_template("account/signin.jinja.htm")
    keys = {
    }

    errors = []
    required_keys = ["email", "password"]
    post_params = http_server.get_post_parameters()
    for required_key in required_keys:
        if required_key not in post_params or post_params[required_key] == "":
            errors.append(required_key)

    if len(errors) == 0:
        email = post_params["email"]
        password = post_params["password"]
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
        account = Account.fetch_by_email_and_password(
            database_manager,
            email,
            password
        )
        if account is None or account.is_closed == 1:
            errors.append("password")
            keys["error_password"] = True
            output = template.render(keys)
            http_server.set_status(400)
            http_server.print_headers()
            print(output)
        else:
            ip_string = http_server.get_remote_address()
            session = Session(database_manager)
            session.set_expiration_days_from_now(
                settings["login_page"]["session_timeout_days"]
            )
            session_slug = session.generate_slug()
            session.account_id = account.id
            session.ip_address = ip_string
            session.slug = session_slug
            session.insert()

            http_server.set_cookie("session_id", session_slug)
            query_parameters = http_server.get_query_parameters()
            redirect_location = settings["login_page"]["default_redirect"]
            if "redirect" in query_parameters:
                redirect_location = query_parameters["redirect"]
            http_server.set_status(307)
            #http_server.set_header("Location", redirect_location)
            http_server.print_headers()
            print("<!DOCTYPE html><html><meta http-equiv=\"refresh\" content=\"0;URL='/account'\" /><head></head></html>")


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


