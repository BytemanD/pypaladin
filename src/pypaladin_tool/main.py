import functools
import re
import subprocess
import sys
from typing import Optional

import httpx

import click
from loguru import logger

from pypaladin.command.diskpart import compress_virtual_disk
from pypaladin.conf import BaseAppConfig
from pypaladin.utils import strutil
from pypaladin_map import ipinfo, location, qqmap, weather
from pypaladin_tool import types


@click.group()
@click.help_option("-h", "--help")
def cli():
    """paladin tools"""
    BaseAppConfig.setup()


def click_command_with_help(func):

    @cli.command()
    @click.help_option("-h", "--help")
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        func(*args, **kwargs)

    return _wrapper


@cli.group()
def map():
    """MAP tools"""


@map.command()
@click.option("--detail", is_flag=True, help="显示详情")
@click.option("--ip", type=types.TYPE_IPV4, help="指定IP地址")
def info(detail=False, ip=None):
    """Get Local info"""
    local_info = {}
    if ip:
        is_ip, ip_type = strutil.is_valid_ip(ip)
        if not is_ip or ip_type != strutil.V4:
            logger.error("invalid ipv4 address")
            return 1
        local_info["ip"] = ip
    else:
        local_info["ip"] = ipinfo.get_public_ip()
    try:
        ip_location = location.Location()
        for api in [location.IP77Api(), location.UUToolApi()]:
            ip_location = api.get_location(local_info.get("ip"))
            break
        if not detail:
            click.echo(f'public ip: {local_info.get("ip")}')
            click.echo(f"location : {ip_location.info()}")
        else:
            local_info.update(**ip_location.to_dict())
            for k, v in local_info.items():
                if not v:
                    continue
                click.echo(f"{k:15}: {v}")
    except IOError as e:
        logger.error("get local info failed: {}", e)
        return 1


@map.command()
@click.option("--city", help="指定城市(省,市,县|区),例如:北京市,东城区")
def query_weather(city: Optional[str] = None):
    """Get weather"""
    api = weather.HefengWeatherApi()
    if not city:
        qq_api = qqmap.QQMapAPI()
        logger.debug("get my location")
        my_location = qq_api.get_location()
        data = qq_api.get_weather(my_location)
        print(data.format())
        return

    values = re.split(r",|，", city)
    if not values:
        raise ValueError("invalid city")
    if len(values) == 1:
        adm, location_name = None, values[0]
    else:
        adm, location_name = values[0], values[1]
    logger.debug("lookup city {}", city)
    try:
        locations = api.lookup_city(location_name, adm=adm)
    except (httpx.HttpError, httpx.RequestError) as e:
        logger.error("lookup city failed: {}", e)
        return 1
    my_location = locations[0]
    data = api.get_weather(my_location)
    print(data.format())


@cli.group()
def disk():
    """Disk tools"""


@disk.command()
@click.help_option("-h", "--help")
@click.argument("vhd_path")
def compress_vhd(vhd_path):
    """Compress vhd/vhdx disk"""
    try:
        compress_virtual_disk(vhd_path)
    except subprocess.CalledProcessError as e:
        logger.error("run diskpart failed: {}", e)


if __name__ == "__main__":
    sys.exit(cli())
