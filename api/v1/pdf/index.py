#!/usr/bin/env python3
import sys
sys.path.append("../../../")
import re
from os import environ
from settings.settings import settings
from modules.HttpServer import HttpServer
from modules.apimanager.ApiManager import ApiManager
from modules.databasemanager.DatabaseManager import DatabaseManager
from modules.DatabaseObject import DatabaseObject
from modules.PdfData import PdfData
from modules.PdfCollager import PdfCollager
import base64


class ApiParamMissingParameterError(Exception):
    pass


class ApiParamInvalidPdf(Exception):
    pass


class ApiParamMissingRequestParameterError(Exception):
    pass


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
api_manager = ApiManager(http_server, database_manager)


def handle_put(http_server, database_manager, ip, account, api_key):
    query_params = http_server.get_query_parameters()
    required_params = ["name"]
    for required_param in required_params:
        if required_param not in query_params or query_params[required_param] == "":
            raise ApiParamMissingParameterError

    name = post_params["name"]
    file_info = http_server.get_file("file")
    file_data = file_info["data"]
    if file_data is None or file_data == "":
        raise ApiParamInvalidPdf

    pdf_data = PdfData(database_manager)
    pdf_data.account_id = account.id
    pdf_data.slug = pdf_data.generate_slug()
    pdf_data.name = name
    pdf_data.data = file_data.encode()
    pdf_data.insert()

    http_server.set_status(201)
    http_server.print_json(output)


def handle_post(http_server, database_manager, ip, account, api_key):
    query_params = http_server.get_query_parameters()
    required_params = ["name"]
    for required_param in required_params:
        if required_param not in query_params or query_params[required_param] == "":
            raise ApiParamMissingParameterError

    name = post_params["name"]
    file_info = http_server.get_file("file")
    file_data = file_info["data"]
    if file_data is None or file_data == "":
        raise ApiParamInvalidPdf

    pdf_data = PdfData.fetch_by_name_and_account_id(name, account.id)

    if pdf_data is not None:
        raise ApiParamInvalidPdf

    pdf_data.data = file_data.encode()
    pdf_data.update()

    http_server.set_status(202)
    http_server.print_json(output)


def handle_get(http_server, database_manager, ip, account, api_key):
    post_params = http_server.get_post_parameters()
    required_params = ["name", "requests"]
    for required_param in required_params:
        if required_param not in post_params or post_params[required_param] == "":
            raise ApiParamMissingParameterError

    name = post_params["name"]
    requests = post_params["requests"]

    required_request_params = ["text", 'x', 'y', 'page_number']
    for required_request_param in required_request_params:
        if required_request_param not in requests or requests[required_request_param] == "":
            raise ApiParamMissingRequestParameterError

    pdf_data = PdfData.fetch_by_name_and_account_id(name, account.id)

    if pdf_data is not None:
        raise ApiParamInvalidPdf

    collager = PdfCollager()
    raw_pdf_data = collager.open_pdf_from_data()
    pdf_data = collager.add_texts(
        raw_pdf_data,
        requests
    )

    output = base64.b64encode(pdf_data.read()).decode("utf-8")
    extension = ".pdf"
    file_name = pdf_data.name
    if file_name < len(extension) or filename[:-len(extension)] != extension:
        file_name = "{}{}".format(file_name, extension)

    http_server.set_header("Pragma", "public")
    http_server.set_header("Expires", "0")
    http_server.set_header(
        "Cache-Control",
        "must-revalidate, post-check=0, pre-check=0"
    )
    http_server.set_header("Content-Type", "application/octet-stream") # "application/pdf")
    http_server.set_header("Content-Transfer-Encoding", "binary")
    http_server.set_header(
        "Content-Disposition",
        "attachment; filename={}".format(file_name)
    )
    http_server.set_header("Content-Length", len(output))
    http_server.print_json(output)


def handle_delete(http_server, database_manager, ip, account, api_key):
    post_params = http_server.get_post_parameters()
    required_params = ["name"]
    for required_param in required_params:
        if required_param not in post_params or post_params[required_param] == "":
            raise ApiParamMissingParameterError

    name = post_params["name"]

    pdf_data = PdfData.fetch_by_name_and_account_id(name, account.id)

    if pdf_data is not None:
        raise ApiParamInvalidPdf

    pdf_data.delete()
    http_server.set_status(202)
    http_server.print_json(output)


api_manager.set_method_callback(
    ApiManager.HTTP_METHOD_GET,
    handle_get
)


api_manager.set_method_callback(
    ApiManager.HTTP_METHOD_POST,
    handle_post
)


api_manager.set_method_callback(
    ApiManager.HTTP_METHOD_PUT,
    handle_put
)


api_manager.set_method_callback(
    ApiManager.HTTP_METHOD_DELETE,
    handle_delete
)


api_manager.require_auth()


try:
    api_manager.run()
except ApiParamMissingParameterError:
    http_server.set_status(400)
    json_response = {"error": "Parameter missing"}
    http_server.print_headers()
    http_server.print_json(json_response)
except ApiParamInvalidPdf:
    http_server.set_status(400)
    json_response = {"error": "A PDF with this name cannot be found"}
    http_server.print_headers()
    http_server.print_json(json_response)

