# -*- coding: utf-8 -*-
"""
ui_app.py — Native arayüz şablonunu (ui_app_template.html) yükler ve
Python'dan gelen veri yükünü (payload) içine enjekte eder.
"""
import os
import json

_DIR = os.path.dirname(os.path.abspath(__file__))
_TPL = os.path.join(_DIR, "ui_app_template.html")


def _load_template():
    with open(_TPL, "r", encoding="utf-8") as f:
        return f.read()


def render(payload=None):
    """
    payload: payload.build_payload() çıktısı (dict) veya None.
    None / boş ise şablon kendi gömülü demo verisini gösterir.
    """
    html = _load_template()
    data_js = json.dumps(payload or None, ensure_ascii=False)
    # Şablondaki yer tutucu: window.__APP_DATA__ = /*__DATA__*/null;
    html = html.replace("/*__DATA__*/null", data_js)
    return html
