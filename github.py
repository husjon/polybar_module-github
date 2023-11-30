#!/usr/bin/env python
# pylint: disable=missing-function-docstring

import json
import os
import pathlib
import time
import sys
import subprocess

import requests


def error(msg=""):
    print("%{F#ff0000}", msg)
    sys.exit(0)


def load_config():
    try:
        with open(BASEDIR / "config.json", "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        error("Config missing")
    except json.decoder.JSONDecodeError:
        error("Config invalid")


def fetch_postal_data():
    cache_file = BASEDIR / "cache.json"

    data = None
    if os.path.exists(cache_file):
        interval = CONFIG.get("interval", 15) * 60
        interval = interval if interval > 300 else 300
        if time.time() - os.path.getmtime(cache_file) < interval:
            with open(cache_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)

    if data is None:
        result = requests.get(
            url=f"{API_URL}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {CONFIG['token']}",
            },
            timeout=5,
        )

        if result.status_code == 200:
            data = json.loads(result.content)
            with open(cache_file, "w+", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
        else:
            data = {}
            with open(cache_file, "w+", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
            error("No data")

    # return postal_data['nextDeliveryDays']
    return len(data)


def bar_output():
    notifications = fetch_postal_data()

    return {"icon": "", "count": notifications}


def notify():
    cache_file = BASEDIR / "cache.json"
    # cache_file = '/tmp/test.json'

    with open(cache_file, "r", encoding="utf-8") as fh:
        notifications = json.load(fh)

    _output = ""
    for notification in notifications:
        repository = notification["repository"]["full_name"]
        subject = notification["subject"]["title"]
        _output += f"<b>{repository}</b>:\n {subject}"

    subprocess.call(
        f"/usr/bin/notify-send 'GitHub Notifications' '{_output}'", shell=True
    )

    return


def main():
    if sys.argv.pop() == "notify":
        notify()
    else:
        data = bar_output()
        print("{icon} {count}".format(**data))


BASEDIR = pathlib.Path(os.path.dirname(os.path.realpath(__file__)))
CONFIG = load_config()
API_URL = "https://api.github.com/notifications"

if __name__ == "__main__":
    try:
        main()
    except requests.ConnectTimeout:
        error("Timeout")
    except requests.ConnectionError:
        error("Error")
    except Exception as e:  # pylint: disable=broad-except
        error(f"Error: {e}")
