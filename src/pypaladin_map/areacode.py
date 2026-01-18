from functools import lru_cache

from pypaladin.httpclient import default_client


class WenyisoAAPI:
    def __init__(self):
        self.client = default_client(base_url="https://www.wenyiso.com")

    @lru_cache()
    def get_areacode_list(self) -> dict:
        resp = self.client.get("/jres/json/quhuadaima/list.json")
        return resp.json()

    def get_areacode(self, area) -> str:
        arearcodes = self.get_areacode_list()
        code = [k for k, v in arearcodes.items() if v == area]
        if not code:
            raise ValueError(f"area code is not found for {area}")
        return code[0]
