from pypaladin.httpclient import default_client


class IPinfoAPI:

    def __init__(self):
        self.client = default_client(base_url="https://ipinfo.io")

    def get_public_ip(self) -> str:
        resp = self.client.get("/json")
        return resp.json().get("ip")


class IPAPI:

    def __init__(self):
        self.client = default_client(base_url="http://ip-api.com")

    def get_public_ip(self) -> str:
        resp = self.client.get("/json")
        return resp.json().get("query")


def get_public_ip() -> str:
    for api in [IPinfoAPI(), IPAPI()]:
        if not isinstance(api, (IPinfoAPI, IPAPI)):
            raise Exception()
        try:
            return api.get_public_ip()
        except IOError:
            continue
    raise IOError("get public ip failed")
