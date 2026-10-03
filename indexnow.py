#!/usr/bin/env python3
"""Сообщает Bing и Яндексу (IndexNow) о страницах сайта после публикации."""
import json, urllib.request
from pathlib import Path

cfg = json.loads(Path("config.json").read_text(encoding="utf-8"))
site = cfg["site_url"].rstrip("/")
host = site.split("/")[2]
urls = Path("dist/urls.txt").read_text().split("\n")[:10000]
body = json.dumps({"host": host, "key": cfg["indexnow_key"],
                   "keyLocation": f"{site}/{cfg['indexnow_key']}.txt", "urlList": urls}).encode()
for api in ("https://yandex.com/indexnow", "https://www.bing.com/indexnow"):
    req = urllib.request.Request(api, body, {"Content-Type": "application/json; charset=utf-8"})
    try:
        print(api, urllib.request.urlopen(req, timeout=30).status)
    except Exception as e:
        print(api, "failed:", e)
