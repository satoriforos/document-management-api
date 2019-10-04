#!/usr/bin/env python3
import sys
sys.path.append("../../")
from jinja2 import Environment, select_autoescape, FileSystemLoader
from os import environ
from settings.settings import settings
from modules.HttpServer import HttpServer
from modules.WebManager import WebManager
from modules.databasemanager.DatabaseManager import DatabaseManager
from modules.auth.ApiKey import ApiKey
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
    if account.is_phone_verified != 1:
        redirect_to_phone_confirmation(http_server, database_manager, session, account)
    else:
        api_key = ApiKey.fetch_by_account_id(database_manager, account.id)
        template = fetch_template("account/apikey.jinja.htm")

        keys = {
            'api_key': api_key.api_key
        }
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


if web_manager.is_logged_in() is False:
    handle_unauthorized(http_server, database_manager, None, None)
else:
    web_manager.run()
