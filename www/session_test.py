#!/usr/bin/env python3
import sys
sys.path.append("../")
import re
from os import environ
from settings.settings import settings
from modules.HttpServer import HttpServer

from http import cookies


http_server = HttpServer(environ, sys.stdin)


query_parameters = http_server.get_query_parameters()
if "drop_cookie" in query_parameters:
    http_server.set_cookie("test", "value")

if "delete_cookie" in query_parameters:
    http_server.delete_cookie("test")


http_server.print_headers()


print("retrieved cookie:")
http_cookies = http_server.get_cookies()
print(http_cookies.output(header="Cookie:"))

print("")
print("")

for key in environ.keys():
    print(key, environ.get(key))



#if self.headers.has_key('cookie'):
#            self.cookie=Cookie.SimpleCookie(self.headers.getheader("cookie"))
