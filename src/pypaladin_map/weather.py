import dataclasses
import time
from functools import lru_cache
from typing import List, Optional

import jwt

from pypaladin.httpclient import default_client

from pypaladin_map import location as net_location


@dataclasses.dataclass
class Weather:
    location: net_location.Location
    weather: str
    temperature: int | float
    winddirection: str
    reporttime: str
    windpower: Optional[str] = None
    # 体感温度
    feels_like: Optional[int | float] = None
    # 风速(公里/小时)
    windspeed: Optional[int] = None
    # 相对湿度，百分比数值
    humidity: Optional[int | float] = None
    link: Optional[str] = None


class XDApi:
    def __init__(self):
        self.client = default_client(base_url="http://u.api.xdapi.com")

    def get_weather(self, location: net_location.Location) -> Weather:
        resp = self.get("/api/v2/Weather/city", params={"code": location.area_code})
        data = resp.json()
        if data.get("code") != 1 or not data.get("data"):
            raise ValueError(
                f"get weather failed, {data.get('msg')}, data: {data.get('data')}"
            )
        value = data.get("data")[0]
        return Weather(
            location=location,
            weather=value.get("weather"),
            temperature=value.get("temperature_float") or value.get("temperature"),
            winddirection=value.get("winddirection"),
            windpower=value.get("windpower"),
            humidity=value.get("humidity_float") or value.get("humidity"),
            reporttime=value.get("reporttime"),
        )


DEFAULT_HEFENG_PROJECT_ID = "482GDEAV8N"
DEFAULT_HEFENG_KID = "KJGUHXCCMM"
DEFAULT_HEFENG_PRIVATE_KEY = """
-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEIG+OSUl393SKw7d5kVdWKKp4ViL1EGMs7UCqFAWCs9CU
-----END PRIVATE KEY-----
"""


class HefengWeatherApi:
    def __init__(self, project_id: Optional[str]=None, private_key: Optional[str]=None,
                 kid: Optional[str]=None):  # fmt: skip
        self.project_id = project_id or DEFAULT_HEFENG_PROJECT_ID
        self.private_key = private_key or DEFAULT_HEFENG_PRIVATE_KEY
        self.kid = kid or DEFAULT_HEFENG_KID
        self.client = default_client(base_url="https://ju44u937u3.re.qweatherapi.com")

    @lru_cache()
    def _get_token(self) -> str:
        payload = {
            "iat": int(time.time()) - 30,
            "exp": int(time.time()) + 900,
            "sub": self.project_id,
        }
        headers = {"kid": self.kid}

        # Generate JWT
        encoded_jwt = jwt.encode(
            payload, self.private_key, algorithm="EdDSA", headers=headers
        )
        return encoded_jwt

    @lru_cache
    def lookup_city(
        self, location: str, adm: Optional[str] = None
    ) -> List[net_location.Location]:
        params = {"location": location}
        if adm:
            params["adm"] = adm
        resp = self.client.get(
            "/geo/v2/city/lookup",
            params=params,
            headers={"Authorization": f"Bearer {self._get_token()}"},
        )
        locations = resp.json().get("location", [])
        return [
            net_location.Location(
                area_code=x.get("id"),
                country=x.get("country"),
                city=x.get("adm2") or x.get("adm1"),
                district=x.get("name"),
                latitude=x.get("lat"),
                longitude=x.get("lon"),
            )
            for x in locations
        ]

    def get_weather(self, location: net_location.Location) -> Weather:
        resp = self.client.get("/v7/weather/now", params={"location": location.area_code},
                        headers={"Authorization": f"Bearer {self._get_token()}"})  # fmt: skip
        data = resp.json()
        value = data.get("now")
        return Weather(
            location=location,
            weather=value.get("text"),
            temperature=value.get("temp"),
            winddirection=value.get("windDir"),
            windpower=value.get("windScale"),
            windspeed=value.get("windSpeed"),
            humidity=value.get("humidity"),
            reporttime=data.get("updateTime"),
            link=data.get("fxLink"),
        )
