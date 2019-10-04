#!/usr/bin/env python3
import sys
sys.path.append("../../")
from jinja2 import Environment, select_autoescape, FileSystemLoader
import re
from os import environ
from validate_email import validate_email
from settings.settings import settings
from modules.HttpServer import HttpServer
from modules.WebManager import WebManager
from modules.databasemanager.DatabaseManager import DatabaseManager
from modules.auth.Account import Account
from modules.auth.ApiKey import ApiKey
from modules.auth.Session import Session
import stripe
from urllib.parse import urlencode, quote_plus


settings["cancel_page"] = {
    "default_redirect": "/",
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


def fetch_template(template_file):
    template_loader = FileSystemLoader(
        settings["cancel_page"]["templates_folder"]
    )
    env = Environment(
        loader=template_loader,
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(template_file)
    return template


http_server = HttpServer(environ, sys.stdin)
database_manager = get_database_connection(settings["mysql"])
web_manager = WebManager(http_server, database_manager)


def handle_get(http_server, database_manager, session, account):
    if account.is_phone_verified != 1:
        redirect_to_phone_confirmation(http_server, database_manager, session, account)
    else:
        query_parameters = http_server.get_query_parameters()
        redirect_location = settings["cancel_page"]["default_redirect"]
        if "redirect" in query_parameters:
            redirect_location = query_parameters["redirect"]
        http_server.set_status(307)
        http_server.set_header("Location", redirect_location)
        http_server.print_headers()
        print("")


def handle_post(http_server, database_manager, session, account):
    if account.is_phone_verified != 1:
        redirect_to_phone_confirmation(http_server, database_manager, session, account)
    else:
        template = fetch_template("account/cancel.jinja.htm")
        keys = {}
        if account is None or account.id <= 0:
            keys["error"] = True
        else:
            if account.stripe_subscription_id is not None:
                stripe.api_key = settings["stripe"]["secret_key"]
                try:
                    subscription = stripe.Subscription.retrieve(
                        account.stripe_subscription_id
                    )
                    subscription.delete()
                    account.stripe_subscription_id = None
                except:
                    pass
            account.is_closed = 1
            account.update()
            session_slug = http_server.get_cookie("session_id")
            http_server.delete_cookie("session_id")
            if session_slug is not None:
                session = Session.fetch_by_slug(database_manager, session_slug)
                ip_string = http_server.get_remote_address()
                if session is not None:
                    session.ip_address = ip_string
                    session.expire()
                    session.update()
            keys["success"] = True
        output = template.render(keys)
        http_server.print_headers()
        print(output)


def handle_unauthorized(http_server, database_manager, session, account):
    query = urlencode({
        "redirect": http_server.get_request_header("REQUEST_URI")
    }, quote_via=quote_plus)
    http_server.set_status(307)
    #http_server.set_header("Location", redirect_location)
    http_server.print_headers()
    print("<!DOCTYPE html><html><meta http-equiv=\"refresh\" content=\"0;URL='/account/signin?" + query + "'\" /><head></head></html>")


def redirect_to_phone_confirmation(http_server, database_manager, session, account):
    query = urlencode({
        "redirect": http_server.get_request_header("REQUEST_URI")
    }, quote_via=quote_plus)
    http_server.set_status(307)
    #http_server.set_header("Location", redirect_location)
    http_server.print_headers()
    print("<!DOCTYPE html><html><meta http-equiv=\"refresh\" content=\"0;URL='/account/confirm_phone?" + query + "'\" /><head></head></html>")


web_manager.set_method_callback(
    WebManager.HTTP_METHOD_GET,
    handle_get
)


web_manager.set_method_callback(
    WebManager.HTTP_METHOD_POST,
    handle_post
)


if web_manager.is_logged_in() is False:
    handle_unauthorized(
        http_server,
        database_manager,
        web_manager.session,
        web_manager.account
    )
else:
    web_manager.run()



