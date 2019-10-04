#!/usr/bin/env python3
import sys
sys.path.append("../")
from jinja2 import Environment, select_autoescape, FileSystemLoader
from os import environ
from settings.settings import settings
from modules.HttpServer import HttpServer
from modules.WebManager import WebManager


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
    template = fetch_template("index.jinja.htm")
    keys = {}
    output = template.render(keys)
    http_server.print_headers()
    print(output)


web_manager.set_method_callback(
    WebManager.HTTP_METHOD_GET,
    handle_get
)


web_manager.run()
