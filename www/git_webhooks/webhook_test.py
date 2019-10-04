#!/usr/bin/env python3
import sys
sys.path.append("../../")
from jinja2 import Environment, select_autoescape, FileSystemLoader
from os import environ
from settings.settings import settings
from modules.HttpServer import HttpServer
from modules.WebManager import WebManager
from modules.databasemanager.DatabaseManager import DatabaseManager
import json
from datetime import datetime


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


def handle_post(http_server, database_manager, session, account):
	post_params = http_server.get_post_json()

	json_output = {
		"ip": http_server.get_remote_address(),
		"post_data": post_params,
		"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	}
	output = json.dumps(json_output, indent=4)
	with open("/tmp/webhook_test.txt", "a") as f:
		f.write(str(output))
	http_server.print_headers()


web_manager.set_method_callback(
    WebManager.HTTP_METHOD_GET,
    handle_post
)

web_manager.set_method_callback(
    WebManager.HTTP_METHOD_POST,
    handle_post
)

web_manager.set_method_callback(
    WebManager.HTTP_METHOD_PUT,
    handle_post
)


web_manager.run()
