from datetime import datetime
import functools
from pathlib import Path
import re
import subprocess
import sys
from typing import Dict, List, Optional

import httpx

import click
from loguru import logger

from pypaladin import log
from pypaladin.command.diskpart import compress_virtual_disk
from pypaladin.conf import BaseAppConfig
from pypaladin.httpclient import default_client
from pypaladin.utils import strutil
from pypaladin.utils.fileutil import move_files
from pypaladin_map import ipinfo, location, qqmap, weather
from pypaladin_tool import _types
from pypaladin_tool._constants import WEATHER_TEMPLATE


CONF = BaseAppConfig.setup()


def _error_msg(message: str):
    return click.style(message, fg="red")


@click.group()
@click.help_option("-h", "--help")
@click.option("-v", "--verbose", count=True, help="Verbose mode")
def cli(verbose: int):
    """paladin tools"""
    if verbose:
        if not CONF.log.file:
            CONF.log.level = ["INFO", "DEBUG", "TRACE"][min(verbose, 3) - 1]
            logger.remove()
        log.add_conole_handler(
            ["INFO", "DEBUG", "TRACE"][min(verbose, 3) - 1], CONF.log
        )


def click_command_with_help(func):
    @cli.command()
    @click.help_option("-h", "--help")
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        func(*args, **kwargs)

    return _wrapper


@cli.command()
@click.option("-T", "--timeout", type=click.IntRange(min=1), help="Timeout")
@click.option(
    "-X",
    "--method",
    type=click.Choice(["GET", "POST", "PUT", "DELETE", "OPTIONS"]),
    default="GET",
    help="request method, default: GET",
)
@click.option("-D", "--data", help="request body")
@click.option(
    "-H",
    "--header",
    type=_types.TYPE_HEADER,
    multiple=True,
    help="HTTP headers. e.g. 'content-type: application/json",
)
@click.argument("url", type=click.STRING)
def curl(
    url: str,
    method: str = "GET",
    header: List[Dict] = [],
    timeout: Optional[int] = None,
    data: Optional[str] = None,
):
    """curl command

    \b
    Args:
        URl: 请求URL
    e.g.
        curl http://www.example.com
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        raise click.UsageError(
            _error_msg(f'url "{url}" is invalid, do you mean http(s)://{url} ?')
        )

    client = default_client(timeout=timeout)
    try:
        resp = client.request(
            method=method,
            url=url,
            headers={k: v for h in header for k, v in h.items()},
            content=data,
        )
    except httpx.HTTPError as e:
        raise click.ClickException(_error_msg(f"{method} {url} failed: {e}"))
    click.echo(f"{resp.request.method} {resp.request.url}")
    for k, v in resp.request.headers.items():
        click.echo(f"{k.title()}: {v}")
    click.echo("")
    if data:
        click.echo(data)

    click.secho("========== response ==========", fg="cyan")
    click.secho(
        f"{resp.status_code} {resp.reason_phrase}",
        fg="red" if resp.status_code >= 400 else "green",
    )
    for k, v in resp.headers.items():
        click.echo(f"{k.title()}: {v}")

    click.echo("")
    click.echo(resp.content.decode() if resp.content else "")
    click.secho(f"(Elapsed: {resp.elapsed.total_seconds()}s)", fg="bright_black")


@cli.group()
def network():
    """Network tools"""


@network.command("location")
@click.option("--detail", is_flag=True, help="显示详情")
@click.option("--ip", type=_types.TYPE_IPV4, help="指定IP地址")
def _location(detail=False, ip=None):
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
            click.echo(f"public ip: {local_info.get('ip')}")
            click.echo(f"location : {ip_location.info()}")
        else:
            local_info.update(**ip_location.to_dict())
            for k, v in local_info.items():
                if not v:
                    continue
                click.echo(f"{k:15}: {v}")
    except IOError as e:
        raise click.ClickException(_error_msg(f"get local info failed: {e}"))


@network.command("weather")
@click.option("--city", help="指定城市(省,市,县|区),例如:北京市,东城区")
def _weather(city: Optional[str] = None):
    """Get weather"""
    api = weather.HefengWeatherApi()

    def _format_weather(weather: weather.Weather) -> str:
        return WEATHER_TEMPLATE.format(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            area=click.style(weather.location.info(), fg="cyan"),
            weather=click.style(weather.weather, fg="cyan"),
            temperature=click.style(f"{weather.temperature}℃", fg="cyan"),
            winddirection=click.style(weather.winddirection, fg="blue"),
            windpower=click.style(weather.windpower or "-", fg="blue"),
            windspeed=click.style(weather.windspeed or "-", fg="blue"),
            humidity=click.style(weather.humidity or "-", fg="yellow"),
            reporttime=click.style(
                f"更新时间: {weather.reporttime}", fg="bright_black"
            ),
            link=click.style(f"更多信息: {weather.link or '-'}", fg="bright_black"),
        )

    if not city:
        qq_api = qqmap.QQMapAPI()
        logger.debug("get my location")
        my_location = qq_api.get_location()
        data = qq_api.get_weather(my_location)
        click.echo(_format_weather(data))
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
    except httpx.HTTPError as e:
        logger.error("lookup city failed: {}", e)
        return 1
    my_location = locations[0]
    data = api.get_weather(my_location)
    click.echo(_format_weather(data))


@cli.group()
def disk():
    """Disk tools"""


@disk.command()
@click.help_option("-h", "--help")
@click.argument("path", type=click.Path(exists=True))
def compress_vhd(path: str):
    """Compress vhd/vhdx disk"""
    if not Path(path).exists():
        raise click.ClickException(_error_msg(f"file {path} not found"))
    try:
        compress_virtual_disk(Path(path))
    except (subprocess.CalledProcessError, OSError) as e:
        raise click.ClickException(_error_msg(f"compress failed: {e}"))


@cli.group()
def file():
    """File tools"""


@file.command()
@click.argument("sources", nargs=-1, type=click.Path(exists=True))
@click.argument("dest", type=click.Path())
def move(sources: List[Path], dest: Path):
    """Move files

    \b
    e.g.
        move dir/path/1 /target/path
        move dir/path/1 dir/path/2 /target/path
    """
    if not sources:
        raise click.UsageError(_error_msg("至少需要指定1个源目录"))

    for src in sources:
        try:
            move_files(Path(src), Path(dest), recursive=True, if_exists="ignore")
        except (FileNotFoundError, FileExistsError, PermissionError) as e:
            raise click.UsageError(_error_msg(f"执行失败, {e}"))


if __name__ == "__main__":
    sys.exit(cli())
