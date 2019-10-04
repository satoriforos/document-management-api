#!/usr/bin/env python3
import sys
sys.path.append("../../")
from jinja2 import Environment, select_autoescape, FileSystemLoader
import re
from os import environ
from settings.settings import settings
from modules.HttpServer import HttpServer
from modules.WebManager import WebManager
from modules.databasemanager.DatabaseManager import DatabaseManager
from modules.auth.Account import Account
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
        template = fetch_template("account/password.jinja.htm")
        keys = {
        }
        output = template.render(keys)
        http_server.print_headers()
        print(output)

def handle_put_post(http_server, database_manager, session, account):
    if account.is_phone_verified != 1:
        redirect_to_phone_confirmation(http_server, database_manager, session, account)
    else:
        template = fetch_template("account/password.jinja.htm")
        keys = {}
        required_keys = ["old_password", "new_password", "verify_new_password"]
        post_params = http_server.get_post_parameters()
        errors = []
        for required_key in required_keys:
            if required_key not in post_params or post_params[required_key] == "":
                errors.append(required_key)

        if len(errors) == 0:
            # verify email
            old_password = post_params["old_password"]
            new_password = post_params["new_password"]
            verify_new_password = post_params["verify_new_password"]

            if new_password != verify_new_password:
                errors.append("error_verify_new_password")


        if len(errors) > 0:
            for key in errors:
                keys["error_{}".format(key)] = True
            
            output = template.render(keys)
            http_server.set_status(400)
            http_server.print_headers()
            #print(keys)

            print(output)

        else:
            retrieved_account = Account.fetch_by_email_and_password(
                database_manager,
                account.email,
                old_password
            )
            if retrieved_account is None:
                errors.append("old_password")
                keys["error_old_password"] = True
                output = template.render(keys)
                http_server.set_status(400)
                http_server.print_headers()

                #print(old_password)
                #print(new_password)
                #print(verify_new_password)

                print(output)
            else:
                retrieved_account.password = new_password
                retrieved_account.update()
                keys["password_updated"] = True
                output = template.render(keys)
                http_server.print_headers()

                #print(old_password)
                #print(new_password)
                #print(verify_new_password)
                #print(alerts)
                #print(keys)

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
    handle_put_post
)


web_manager.set_method_callback(
    WebManager.HTTP_METHOD_PUT,
    handle_put_post
)


if web_manager.is_logged_in() is False:
    handle_unauthorized(http_server, database_manager, web_manager.session, web_manager.account)
else:
    web_manager.run()
