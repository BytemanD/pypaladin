from enum import Enum
import os
from pathlib import Path
import shutil
from typing import Literal, Optional, Union, overload

import humanize
from loguru import logger


class IfExists(str, Enum):
    """文件存在时处理方式"""

    overwrite = "overwrite"
    ignore = "ignore"
    raise_error = "raise_error"


def create_text(
    dir: Union[Path, str],
    file: Union[Path, str],
    content: str = "",
    encoding: Optional[str] = None,
):
    """创建文本文件夹和文件
    Args:
        dir (Path): 根目录
        file_dir (Union[Path, str]): 相对路径
    """
    file_path = Path(dir).joinpath(file)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding=encoding)
    return file_path


def move_files(
    src: Path,
    dst: Path,
    recursive: bool = False,
    if_exists: Union[IfExists, str] = IfExists.raise_error,
):
    """移动文件
    Args:
        src (Path): 源路径
        dst (Path): 目标路径
        recursive (bool, optional): 是否递归移动. Defaults to False.
    """
    if dst.is_file():
        raise FileExistsError(f"路径 {dst} 不是一个有效的目录")
    if not src.exists():
        raise FileNotFoundError(f"路径 {src} 不存在")
    if src.is_file():
        files = [src]
    elif recursive:
        files = [x for x in src.rglob("*") if x.is_file()]
    else:
        files = [x for x in src.glob("*") if x.is_file()]

    dst.mkdir(parents=True, exist_ok=True)
    for file in files:
        if dst.joinpath(file.name).exists():
            if if_exists == IfExists.raise_error:
                raise FileExistsError(f"目标文件已存在: {dst}")
            elif if_exists == IfExists.overwrite:
                logger.warning("删除文件: {}", dst.joinpath(file.name))
                os.remove(dst.joinpath(file.name))
            elif if_exists == IfExists.ignore:
                logger.warning("跳过文件: {}", file)
                continue
            else:
                raise ValueError(f"未知的 if_exists 值: {if_exists}")
        logger.debug("移动文件: {} -> {}", file, dst)
        shutil.move(file, dst)


@overload
def file_size(path: Union[Path, str], natural: Literal[False] = False) -> int:
    """处理整数"""
    ...


@overload
def file_size(path: Union[Path, str], natural: Literal[True]) -> str:
    """处理字符串"""
    ...


def file_size(path: Union[Path, str], natural=False) -> Union[int, str]:
    """获取文件大小，单位字节

    Args:
        path (Union[Path, str]): 文件路径

    Returns:
        int: 文件大小，单位字节
    """
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    if natural:
        return humanize.naturalsize(file_path.stat().st_size)
    else:
        return file_path.stat().st_size
