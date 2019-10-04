#!/usr/bin/env python3
import sys
sys.path.append("../../")
from jinja2 import Environment, select_autoescape, FileSystemLoader
from os import environ
from settings.settings import settings
from modules.HttpServer import HttpServer
from modules.WebManager import WebManager
from modules.databasemanager.DatabaseManager import DatabaseManager
import requests
import phonenumbers
from urllib.parse import urlencode, quote_plus


settings["confirm_page"] = {
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
        settings["confirm_page"]["templates_folder"]
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
    keys = {}
    keys["seconds_to_expire"] = 0
    template = fetch_template("account/confirm_phone.jinja.htm")
    raw_phone_number = account.phone
    keys["phone_number"] = raw_phone_number
    do_continue = False
    try:
        phone_details = phonenumbers.parse(raw_phone_number, "US")
        do_continue = True
    except Exception:
        keys["send_error"] = True
        output = template.render(keys)
        http_server.print_headers()
        print(output)

    if do_continue is True:
        authy_params = {
            "api_key": settings["authy"]["api_key"],
            "via": "sms",
            "phone_number": phone_details.national_number,
            "country_code": phone_details.country_code
        }
        response = requests.post(
            settings["authy"]["verify_start_url"],
            data=authy_params
        )
        if response.status_code == 200:
            json_response = response.json()
            keys["seconds_to_expire"] = json_response["seconds_to_expire"]
            output = template.render(keys)
            http_server.print_headers()
            print(output)
        else:
            keys["send_error"] = True
            output = template.render(keys)
            http_server.print_headers()
            print(output)


def handle_post(http_server, database_manager, session, account):
    keys = {}
    template = fetch_template("account/confirm_phone.jinja.htm")
    post_parameters = http_server.get_post_parameters()
    keys["seconds_to_expire"] = post_parameters["seconds_to_expire"]
    raw_phone_number = account.phone
    keys["phone_number"] = raw_phone_number

    if "code" not in post_parameters:
        keys["error_code"] = True
        output = template.render(keys)
        http_server.print_headers()
        print(output)

    else:
        do_continue = False
        try:
            phone_details = phonenumbers.parse(raw_phone_number, "US")
            do_continue = True
        except Exception:
            keys["send_error"] = True
            keys["phone_number"] = raw_phone_number
            output = template.render(keys)
            http_server.print_headers()
            print(output)

        if do_continue is True:
            code = post_parameters["code"]
            authy_params = {
                "api_key": settings["authy"]["api_key"],
                "verification_code": code,
                "phone_number": phone_details.national_number,
                "country_code": phone_details.country_code
            }
            response = requests.get(
                settings["authy"]["verify_check_url"],
                data=authy_params
            )
            if response.status_code == 200:
                json_response = response.json()
                if json_response["success"] is True:
                    account.is_phone_verified = 1
                    account.update()
                    keys["confirm_success"] = True
                    output = template.render(keys)
                    http_server.print_headers()
                    print(output)                    
                else:
                    keys["error_confirming"] = True
                    keys["error_code"] = True
                    output = template.render(keys)
                    http_server.print_headers()
                    print(output)
            else:
                keys["error_confirming"] = True
                keys["error_code"] = True
                output = template.render(keys)
                http_server.print_headers()
                print(output)


def handle_unauthorized(http_server, database_manager, session, account):
    query = urlencode({
        "redirect": http_server.get_request_header("REQUEST_URI")
    }, quote_via=quote_plus)
    http_server.set_status(307)
    http_server.print_headers()
    print("<!DOCTYPE html><html><meta http-equiv=\"refresh\" content=\"0;URL='/account/signin?" + query + "'\" /><head></head></html>")


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
