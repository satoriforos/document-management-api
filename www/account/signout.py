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


settings["login_page"] = {
    "default_redirect": "/",
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


def handle_get(http_server, database_manager, session, account):
    session_slug = http_server.get_cookie("session_id")
    http_server.delete_cookie("session_id")
    if session_slug is not None:
        session = Session.fetch_by_slug(database_manager, session_slug)
        ip_string = http_server.get_remote_address()
        if session is not None:
            session.ip_address = ip_string
            session.expire()
            session.update()

    query_parameters = http_server.get_query_parameters()
    redirect_location = settings["login_page"]["default_redirect"]
    if "redirect" in query_parameters:
        redirect_location = query_parameters["redirect"]
    http_server.set_status(307)
    http_server.set_header("Location", redirect_location)
    http_server.print_headers()
    print("")


web_manager.set_method_callback(
    WebManager.HTTP_METHOD_GET,
    handle_get
)

web_manager.run()


