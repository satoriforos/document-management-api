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
from modules.auth.AccountRegistration import AccountRegistration
from modules.auth.ApiKey import ApiKey
from modules.apimanager.SubscriptionPlan import SubscriptionPlan
from modules.auth.Session import Session


settings["confirm_page"] = {
    "templates_folder": "../templates",
    "session_timeout_days": 14,
    "default_redirect": "/account/",
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
    template = fetch_template("account/confirm.jinja.htm")
    query_parameters = http_server.get_query_parameters()

    if "code" not in query_parameters:
        keys["no_code_provided"] = True
        output = template.render(keys)
        # http_server.set_status(400)
        http_server.print_headers()
        print(output)

    else:
        code = query_parameters["code"]
        registration = AccountRegistration.fetch_by_confirmation_code(
            database_manager,
            code
        )
        if registration is None:
            keys["invalid_code"] = True
            output = template.render(keys)
            # http_server.set_status(400)
            http_server.print_headers()
            print(output)

        else:
            existing_account = Account.fetch_by_from_registration_id(
                database_manager,
                registration.id
            )
            if existing_account is not None:
                keys["already_confirmed"] = True
                output = template.render(keys)
                # http_server.set_status(400)
                http_server.print_headers()
                print(output)

            else:
                account = Account.from_registration(registration)
                account.insert()
                if account.id is None or account.id < 1:
                    account = Account.fetch_by_from_registration_id(
                        database_manager,
                        registration.id
                    )

                subscription = SubscriptionPlan.fetch_by_id(
                    database_manager,
                    account.subscription_plan_id
                )
                if subscription is None:
                    subscription = SubscriptionPlan.fetch_by_name(
                        database_manager,
                        "free"
                    )
                new_api_key = ApiKey(database_manager)
                new_api_key.generate_key()
                new_api_key.generate_secret()
                new_api_key.account_id = account.id
                new_api_key.update_plan(subscription)
                new_api_key.insert()

                # log in
                ip_string = http_server.get_remote_address()
                session = Session(database_manager)
                session.set_expiration_days_from_now(
                    settings["confirm_page"]["session_timeout_days"]
                )
                session_slug = session.generate_slug()
                session.account_id = account.id
                session.ip_address = ip_string
                session.slug = session_slug
                session.insert()
                http_server.set_cookie("session_id", session_slug)

                output = template.render(keys)
                http_server.print_headers()
                print(output)


web_manager.set_method_callback(
    WebManager.HTTP_METHOD_GET,
    handle_get
)

web_manager.run()


