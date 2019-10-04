#!/usr/bin/env python3
import sys
sys.path.append("../../")
from jinja2 import Environment, select_autoescape, FileSystemLoader
from os import environ
from settings.settings import settings
from modules.HttpServer import HttpServer
from modules.WebManager import WebManager
from modules.databasemanager.DatabaseManager import DatabaseManager
from modules.apimanager.SubscriptionPlan import SubscriptionPlan
from datetime import datetime
import stripe
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


def get_ordinality(number):
    ordinalities = ["th", "st", "nd", "rd"]
    if number % 10 in [1, 2, 3] and number not in [11, 12, 13]:
        return ordinalities[number % 10]
    else:
        return ordinalities[0]


http_server = HttpServer(environ, sys.stdin)
database_manager = get_database_connection(settings["mysql"])
web_manager = WebManager(http_server, database_manager)


def handle_get(http_server, database_manager, session, account):
    if account.is_phone_verified != 1:
        redirect_to_phone_confirmation(http_server, database_manager, session, account)
    else:
        keys = {}
        template = fetch_template("account/billing.jinja.htm")
        # http_server.print_headers()
        # print(dict(account))

        subscription_plan_template = SubscriptionPlan(database_manager)
        subscription_conditions = [{
            "column": "is_active",
            "equivalence": "=",
            "value": 1
        }]
        subscription_plans = database_manager.fetch_by(
            subscription_plan_template,
            subscription_conditions
        )
        subscription_plan_name = None
        account_subscription_plan = None
        billing_profiles = []
        for subscription_plan in subscription_plans:
            if subscription_plan.id == account.subscription_plan_id:
                subscription_plan_name = subscription_plan.name
                account_subscription_plan = subscription_plan
            billing_profiles.append({
                "slug": subscription_plan.name,
                "name": subscription_plan.name.title(),
                "amount": subscription_plan.amount,
                "currency": subscription_plan.currency,
                "allowed_requests_per_month": subscription_plan.allowed_requests_per_month,
                "allowed_requests_per_month_printed": "{:,}".format(
                    subscription_plan.allowed_requests_per_month
                ),
            })

        next_billing_date = account.get_next_billing_date()
        if account.stripe_subscription_id is not None and \
                account.stripe_subscription_id != "":
            stripe.api_key = settings["stripe"]["secret_key"]
            stripe_subscription = stripe.Subscription.retrieve(
                account.stripe_subscription_id
            )
            next_billing_date = datetime.utcfromtimestamp(
                stripe_subscription.current_period_end
            )

        keys = {
            "billing_profiles": billing_profiles,
            "current_plan_name": subscription_plan_name,
            "errors": [],
            "response": [],
            "billing_profile_name": account_subscription_plan.name.title(),
            "monthly_cost": "{:,.2f}".format(account_subscription_plan.amount),
            "currency": account_subscription_plan.currency,
            "billing_day": account.billing_day,
            "billing_day_ordinality": get_ordinality(account.billing_day),
            "next_billing_date": next_billing_date.strftime("%Y-%m-%d"),
            "max_api_calls":  "{:,}".format(
                account_subscription_plan.allowed_requests_per_month
            ),
            "selected_subscription_plan_name": account_subscription_plan.name
        }

        output = template.render(keys)
        http_server.print_headers()
        print(output)


def handle_put_post(http_server, database_manager, session, account):
    if account.is_phone_verified != 1:
        redirect_to_phone_confirmation(http_server, database_manager, session, account)
    else:
        keys = {}
        template = fetch_template("account/billing.jinja.htm")
        # http_server.print_headers()
        # print(dict(account))

        subscription_plan_template = SubscriptionPlan(database_manager)
        subscription_conditions = [{
            "column": "is_active",
            "equivalence": "=",
            "value": 1
        }]
        subscription_plans = database_manager.fetch_by(
            subscription_plan_template,
            subscription_conditions
        )
        subscription_plan_name = None
        account_subscription_plan = None
        billing_profiles = []
        for subscription_plan in subscription_plans:
            if subscription_plan.id == account.subscription_plan_id:
                subscription_plan_name = subscription_plan.name
                account_subscription_plan = subscription_plan
            billing_profiles.append({
                "slug": subscription_plan.name,
                "name": subscription_plan.name.title(),
                "amount": subscription_plan.amount,
                "currency": subscription_plan.currency,
                "allowed_requests_per_month": subscription_plan.allowed_requests_per_month,
                "allowed_requests_per_month_printed": "{:,}".format(
                    subscription_plan.allowed_requests_per_month
                ),
            })

        next_billing_date = account.get_next_billing_date()
        if account.stripe_subscription_id is not None and \
                account.stripe_subscription_id != "":
            stripe.api_key = settings["stripe"]["secret_key"]
            stripe_subscription = stripe.Subscription.retrieve(
                account.stripe_subscription_id
            )
            next_billing_date = datetime.utcfromtimestamp(
                stripe_subscription.current_period_end
            )

        keys = {
            "billing_profiles": billing_profiles,
            "current_plan_name": subscription_plan_name,
            "errors": [],
            "response": [],
            "billing_profile_name": account_subscription_plan.name.title(),
            "monthly_cost": "{:,.2f}".format(account_subscription_plan.amount),
            "currency": account_subscription_plan.currency,
            "billing_day": account.billing_day,
            "billing_day_ordinality": get_ordinality(account.billing_day),
            "next_billing_date": next_billing_date.strftime("%Y-%m-%d"),
            "max_api_calls":  "{:,}".format(
                account_subscription_plan.allowed_requests_per_month
            ),
            "selected_subscription_plan_name": account_subscription_plan.name
        }

        # new get post info
        errors = []
        required_keys = [
            "billing_id",
        ]
        post_params = http_server.get_post_parameters()
        if "billing_id" in post_params:
            if post_params["billing_id"] != "free":
                required_keys += [
                    "stripe_token"
                ]

        keys["response"] = post_params

        for required_key in required_keys:
            if required_key not in post_params or post_params[required_key] == "":
                errors.append(required_key)

        if len(errors) == 0:
            subscription_plan_name = post_params["billing_id"]
            subscription_plan = SubscriptionPlan.fetch_by_name(
                database_manager,
                subscription_plan_name
            )
            if subscription_plan is None:
                errors.append("billing_id")

        keys["errors"] = errors
        for error in errors:
            keys["error_{}".format(error)] = True

        if len(errors) > 0:
            output = template.render(keys)
            # http_server.set_status(400)
            http_server.print_headers()
            print(output)

        else:
            if account.stripe_customer_id:
                stripe_subscription_id = account.stripe_subscription_id
                if account.stripe_subscription_id:
                    try:
                        subscription = stripe.Subscription.retrieve(
                            account.stripe_subscription_id
                        )
                        subscription.delete()
                    except:
                        pass

            stripe_source_token = None
            stripe_subscription_id = None
            if subscription_plan.amount > 0:
                stripe.api_key = settings["stripe"]["secret_key"]
                stripe_plan = stripe.Plan.retrieve(subscription_plan.stripe_id)
                # How to acquire stripe tokens
                # https://stripe.com/docs/sources/cards
                stripe_source_token = post_params["stripe_token"]

                stripe_customer_description = account.email

                # will throw an exception if it fails. Must catch
                subscription = stripe.Subscription.create(
                    customer=account.stripe_customer_id,
                    items=[{
                      "plan": stripe_plan.id
                    }]
                )
                stripe_subscription_id = subscription.id

            billing_epoch = datetime.now()
            account.subscription_plan_id = subscription_plan.id
            account.stripe_source_id = stripe_source_token
            account.stripe_subscription_id = stripe_subscription_id
            account.billing_interval = "monthly"
            account.billing_year = billing_epoch.year
            account.billing_month = billing_epoch.month
            account.billing_day = billing_epoch.day

            account.update()
            #keys["update_succeeded"] = True

            # retrieve updated subscription plan info
            subscription_plan_name = None
            account_subscription_plan = None
            billing_profiles = []
            for subscription_plan in subscription_plans:
                if subscription_plan.id == account.subscription_plan_id:
                    subscription_plan_name = subscription_plan.name
                    account_subscription_plan = subscription_plan
                billing_profiles.append({
                    "slug": subscription_plan.name,
                    "name": subscription_plan.name.title(),
                    "amount": subscription_plan.amount,
                    "currency": subscription_plan.currency,
                    "allowed_requests_per_month": subscription_plan.allowed_requests_per_month,
                    "allowed_requests_per_month_printed": "{:,}".format(
                        subscription_plan.allowed_requests_per_month
                    ),
                })

            next_billing_date = account.get_next_billing_date()
            if account.stripe_subscription_id is not None and \
                    account.stripe_subscription_id != "":
                stripe.api_key = settings["stripe"]["secret_key"]
                stripe_subscription = stripe.Subscription.retrieve(
                    account.stripe_subscription_id
                )
                next_billing_date = datetime.utcfromtimestamp(
                    stripe_subscription.current_period_end
                )

            keys = {
                "update_succeeded": True,
                "billing_profiles": billing_profiles,
                "current_plan_name": subscription_plan_name,
                "errors": [],
                "response": [],
                "billing_profile_name": account_subscription_plan.name.title(),
                "monthly_cost": "{:,.2f}".format(account_subscription_plan.amount),
                "currency": account_subscription_plan.currency,
                "billing_day": account.billing_day,
                "billing_day_ordinality": get_ordinality(account.billing_day),
                "next_billing_date": next_billing_date.strftime("%Y-%m-%d"),
                "max_api_calls":  "{:,}".format(
                    account_subscription_plan.allowed_requests_per_month
                ),
                "selected_subscription_plan_name": account_subscription_plan.name
            }

            http_server.set_status(200)
            http_server.print_headers()
            output = template.render(keys)
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
    handle_unauthorized(
        http_server,
        database_manager,
        web_manager.session,
        web_manager.account
    )
else:
    web_manager.run()
