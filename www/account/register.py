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
from modules.courier.Courier import Courier
from modules.apimanager.SubscriptionPlan import SubscriptionPlan
from datetime import datetime
import stripe
import requests
import phonenumbers
from twilio.rest import Client
import json


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
    billing_profiles = []
    for subscription_plan in subscription_plans:
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

    template = fetch_template("account/register.jinja.htm")
    keys = {
        "billing_profiles": billing_profiles,
        "errors": [],
        "response": []
    }
    output = template.render(keys)
    http_server.print_headers()
    print(output)


def handle_put_post(http_server, database_manager, session, account):
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
    billing_profiles = []
    for available_subscription_plan in subscription_plans:
        billing_profiles.append({
            "slug": available_subscription_plan.name,
            "name": available_subscription_plan.name.title(),
            "amount": available_subscription_plan.amount,
            "currency": available_subscription_plan.currency,
            "allowed_requests_per_month": available_subscription_plan.allowed_requests_per_month,
            "allowed_requests_per_month_printed": "{:,}".format(
                available_subscription_plan.allowed_requests_per_month
            ),
        })
    template = fetch_template("account/register.jinja.htm")
    keys = {
        "billing_profiles": billing_profiles,
    }

    errors = []
    required_keys = [
        "billing_id",
        "email",
        "password",
        "verify_password",
        "phone",
        #"g-recaptcha-response"
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
        email = post_params["email"]
        password = post_params["password"]
        verify_password = post_params["verify_password"]
        phone = post_params["phone"]
        formatted_number = phone
        if password != verify_password:
            errors.append("verify_password")
        #try:
        phone_details = phonenumbers.parse(phone, "US")
        if phonenumbers.is_valid_number(phone_details) is False:
            errors.append("phone")
        else:
            formatted_number = "+{} {}".format(
                phone_details.country_code,
                phonenumbers.format_number(
                    phone_details,
                    phonenumbers.PhoneNumberFormat.NATIONAL
                )
            )
            client = Client(
                settings["twilio"]["account_sid"],
                settings["twilio"]["auth_token"]
            )
            twilio_phone_details = client.lookups.phone_numbers(
                formatted_number
            ).fetch(type='carrier')
            if twilio_phone_details.carrier["error_code"] is not None:
                errors.append("phone")
            else:
                if twilio_phone_details.carrier["type"] == "voip":
                    errors.append("phone_voip")
        #except:
        #    errors.append("phone")
        if validate_email(email) is False:
            errors.append("email")
        else:
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
        is_captcha_valid = True
        '''
        recaptcha_response = post_params['g-recaptcha-response']
        captcha_data = {
            "secret": settings["google_recaptcha3"]["secret_key"],
            "response": recaptcha_response
        }
        recaptcha_response = requests.post(
            settings["google_recaptcha3"],
            data=captcha_data
        )
        recapcha_json = recaptcha_response.json()

        is_captcha_valid = True
        if recapcha_json['success']:
            is_captcha_valid = True
        else:
            is_captcha_valid = False
        '''

        if is_captcha_valid is False:
            keys["error_invalid_captcha"] = True
            output = template.render(keys)
            # http_server.set_status(400)
            http_server.print_headers()
            print(output)
        else:
            is_marketing_ok = False
            if "subscribe" in post_params:
                if int(post_params["subscribe"]) == 1:
                    is_marketing_ok = True
                    keys["is_marketing_ok"] = True

            do_continue = True
            stripe_source_token = None
            stripe_customer_id = None
            stripe_subscription_id = None
            if subscription_plan.amount > 0:
                stripe.api_key = settings["stripe"]["secret_key"]

                discount_code = None
                stripe_coupon = None
                stripe_coupon_id = None
                if "discount_code" in post_params:
                    discount_code = post_params["discount_code"]
                    try:
                        stripe_coupon = stripe.Coupon.retrieve(discount_code)
                        do_continue = True
                        stripe_coupon_id = stripe_coupon.id
                    except Exception:
                        errors += ["discount_code"]
                        keys["errors"] = errors
                        for error in errors:
                            keys["error_{}".format(error)] = True
                        output = template.render(keys)
                        # http_server.set_status(400)
                        http_server.print_headers()
                        print(output)

                if do_continue is True:
                    stripe_plan = stripe.Plan.retrieve(subscription_plan.stripe_id)
                    # How to acquire stripe tokens
                    # https://stripe.com/docs/sources/cards
                    # if "stripe_token" not in post_params:
                    #    raise ApiParamMissingStripeTokenError
                    stripe_source_token = post_params["stripe_token"]

                    stripe_customer_description = email
                    try:
                        customer = stripe.Customer.create(
                            description=stripe_customer_description,
                            source=stripe_source_token
                        )
                        stripe_customer_id = customer.id

                        # will throw an exception if it fails. Must catch
                        subscription = stripe.Subscription.create(
                            customer=stripe_customer_id,
                            items=[{
                              "plan": stripe_plan.id
                            }],
                            coupon=stripe_coupon_id
                        )
                        stripe_subscription_id = subscription.id
                    except Exception:
                        errors += ["duplicate_submission"]
                        keys["errors"] = errors
                        for error in errors:
                            keys["error_{}".format(error)] = True
                        output = template.render(keys)
                        # http_server.set_status(400)
                        http_server.print_headers()
                        print(output)
                        do_continue = False

            if do_continue is True:
                # verify email doesn't already exist
                account = Account.fetch_by_email(database_manager, email)
                if account is not None:
                    errors += ["email_taken"]
                    keys["errors"] = errors
                    for error in errors:
                        keys["error_{}".format(error)] = True
                    output = template.render(keys)
                    # http_server.set_status(400)
                    http_server.print_headers()
                    print(output)
                else:
                    registration = AccountRegistration.fetch_by_email(
                        database_manager,
                        email
                    )
                    if registration is not None:
                        errors += ["email_taken"]
                        keys["errors"] = errors
                        for error in errors:
                            keys["error_{}".format(error)] = True
                        output = template.render(keys)
                        # http_server.set_status(400)
                        http_server.print_headers()
                        print(output)
                    else:
                        registration_epoch = datetime.now()
                        registration = AccountRegistration(database_manager)
                        registration.email = post_params["email"]
                        registration.password = post_params["password"]
                        registration.phone = formatted_number
                        registration.subscription_plan_id = subscription_plan.id
                        registration.is_marketing_ok = is_marketing_ok
                        registration.stripe_source_id = stripe_source_token
                        registration.stripe_customer_id = stripe_customer_id
                        registration.stripe_subscription_id = stripe_subscription_id
                        registration.billing_interval = "monthly"
                        registration.billing_year = registration_epoch.year
                        registration.billing_month = registration_epoch.month
                        registration.billing_day = registration_epoch.day

                        confirmation_code = registration.generate_confirmation_code()
                        # send confirmation email
                        courier = Courier(settings["sendgrid"])
                        from_email = settings["email"]["from"]["email"]
                        subject = "Confirm your account"
                        template_id = "d-52d09c7b03f64d6caeab90b722249472"
                        substitutions = {"confirm_code": confirmation_code}
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
                            registration.insert()
                            template = fetch_template(
                                "account/register-success.jinja.htm"
                            )
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
