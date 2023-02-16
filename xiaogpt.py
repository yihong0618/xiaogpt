import argparse
import json
import subprocess
import time
from http.cookies import SimpleCookie

import requests
from requests.utils import cookiejar_from_dict
from revChatGPT.V1 import Chatbot, configure
from rich import print

s = requests.session()

LATEST_ASK_API = "https://userprofile.mina.mi.com/device_profile/v2/conversation?source=dialogu&hardware={hardware}&timestamp={timestamp}&limit=2"

COOKIE_STRING = ""


### HELP FUNCTION ###
def parse_cookie_string(cookie_string):
    cookie = SimpleCookie()
    cookie.load(cookie_string)
    cookies_dict = {}
    cookiejar = None
    for k, m in cookie.items():
        cookies_dict[k] = m.value
        cookiejar = cookiejar_from_dict(cookies_dict, cookiejar=None, overwrite=True)
    return cookiejar


def get_latest_ask_from_xiaoai(hardware="LX06"):
    s.cookies = parse_cookie_string(COOKIE_STRING)
    r = s.get(
        LATEST_ASK_API.format(hardware=hardware, timestamp=str(int(time.time() * 1000)))
    )
    return r.json()


def get_last_timestamp_and_record(data):
    if d := data.get("data"):
        records = json.loads(d).get("records")
        last_record = records[0]
        timestamp = last_record.get("time")
        return timestamp, last_record
    else:
        return 0, None


def main(hardware):
    data = get_latest_ask_from_xiaoai(hardware=hardware)
    timestamp, last_record = get_last_timestamp_and_record(data)
    c = Chatbot(configure())
    while 1:
        print(f"Now listening xiaoai new message timestamp: {timestamp}")
        r = get_latest_ask_from_xiaoai(hardware=hardware)
        time.sleep(5)
        new_timestamp, last_record = get_last_timestamp_and_record(r)
        if new_timestamp > timestamp:
            timestamp = new_timestamp
            query = last_record.get("query", "")
            if query.find("帮我回答") != -1:
                # drop 帮我回答
                query = query[4:] + "，请用100字以内回答"
                print(query)
                print("Running chatgpt ask maybe a little slow we do not pay")
                # waiting for xiaoai speaker done
                time.sleep(5)
                subprocess.check_output(["micli", "5-1", "正在问GPT我们不是会员还用的API有点慢"])
                data = list(c.ask(query))[-1]
                if message := data.get("message", ""):
                    # xiaoai tts did not support space
                    message = message.replace(" ", ",")
                    message = "以下是GPT的回答，" + message
                    print(message)
                    try:
                        print(
                            "以下是小爱的回答",
                            last_record.get("answers")[0].get("tts", {}).get("text"),
                        )
                    except:
                        print("小爱没回")
                    # 5-1 for xiaoai pro tts
                    try:
                        subprocess.check_output(["micli", "5-1", message])
                        time.sleep(1)
                    except Exception as e:
                        print("Something is wrong: ", str(e))

        else:
            print("No new xiao ai record")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("cookie", help="xiao ai cookie")
    parser.add_argument(
        "--hardware",
        dest="hardware",
        type=str,
        default="LX06",
        help="小爱 hardware",
    )
    options = parser.parse_args()
    COOKIE_STRING = options.cookie
    main(options.hardware)
