import subprocess

from loguru import logger


def execute(cmd: str, check=True, success_codes=None):
    """执行系统命令
    """
    logger.debug("RUN: {}", cmd)
    status, output = subprocess.getstatusoutput(cmd)
    if check and status not in (success_codes or [0]):
        raise subprocess.CalledProcessError(status, cmd=cmd, output=output)
    return status, output
