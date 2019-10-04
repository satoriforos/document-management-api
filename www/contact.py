#!/usr/bin/env python3
import sys
sys.path.append("../")
from jinja2 import Environment, select_autoescape, FileSystemLoader
from os import environ
from settings.settings import settings
from modules.HttpServer import HttpServer
from modules.WebManager import WebManager
from validate_email import validate_email
from modules.courier.Courier import Courier


http_server = HttpServer(environ, sys.stdin)
web_manager = WebManager(http_server, None)


template_folder = 'templates'


def fetch_template(template_file):
    template_loader = FileSystemLoader(template_folder)
    env = Environment(
        loader=template_loader,
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(template_file)
    return template


def handle_get(http_server, database_manager, session, account):
    template = fetch_template("contact.jinja.htm")
    keys = {}
    output = template.render(keys)
    http_server.print_headers()
    print(output)


def handle_put_post(http_server, database_manager, session, account):
    template = fetch_template("contact.jinja.htm")
    keys = {}

    post_params = http_server.get_post_parameters()

    do_proceed = True
    if "email" not in post_params or post_params["email"].strip() == "":
        keys["error_email"] = True
        do_proceed = False

    if "message" not in post_params or post_params["message"].strip() == "":
        keys["error_message"] = True
        do_proceed = False

    # verify email
    if do_proceed is True:
        email = post_params["email"].strip()
        message = post_params["message"].strip()
        if validate_email(email) is False:
            keys["error_email"] = True
            do_proceed = False

    if do_proceed is True:
        courier = Courier(settings["sendgrid"])
        from_email = settings["email"]["from"]["email"]
        subject = "From Data With Love Customer Inquiry"
        template_id = "d-3765f5ef527542759f4a0937a3e24115"
        substitutions = {"email": email, "message": message}
        to_email = "email@example.com"
        from_email = email
        response = courier.send_template_email(
            to_email,
            from_email,
            subject,
            template_id,
            substitutions
        )
        if response.status_code != 202:
            keys["error_sending"] = True
        else:
            keys["send_success"] = True

    output = template.render(keys)
    http_server.print_headers()
    print(output)


web_manager.set_method_callback(
    WebManager.HTTP_METHOD_GET,
    handle_get
)

web_manager.set_method_callback(
    WebManager.HTTP_METHOD_POST,
    handle_put_post
)


web_manager.run()
