#!/usr/bin/env python3
import os
from pathlib import Path
from subprocess import call
import requests
import sys
sys.path.append("../../")
from settings.settings import settings


headers = {
    "Status": "200 OK",
}


def git_pull():
    script_path = Path(os.path.abspath(__file__))
    root_folder = script_path.parent.parent
    os.chdir(root_folder.as_posix())

    call(["git", "pull"])


def clear_cloudfront_cache():
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Key": settings["cloudflare"]["api_key"],
        "X-Auth-Email": settings["cloudflare"]["email"]
    }
    cloudflare_url = "https://api.cloudflare.com/client/v4/zones/{}/purge_cache".format(
        settings["cloudflare"]["zone_identifier"]
    )
    json_data = {"purge_everything": True}
    requests.delete(cloudflare_url, json=json_data, headers=headers)


def run():
    for key, value in headers.items():
        print("{}: {}".format(key, value))
    print("")
    print("Done")

    git_pull()
    clear_cloudfront_cache()


run()
