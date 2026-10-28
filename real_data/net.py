# -*- coding: utf-8 -*-
"""Force direct HTTP connections (ignore the machine's flaky system proxy)."""
import os
import requests

for _k in list(os.environ):
    if "proxy" in _k.lower():
        os.environ.pop(_k, None)

_orig_request = requests.Session.request


def _request(self, method, url, **kwargs):
    kwargs.setdefault("proxies", {"http": None, "https": None})
    self.trust_env = False
    return _orig_request(self, method, url, **kwargs)


requests.Session.request = _request
