import ntpath
import posixpath
import re


_LINUX_ABS_RE = re.compile(r"^/(?!/).+")
_WIN_ABS_RE = re.compile(r"^[A-Za-z]:\\.+")
_INVALID_GLOB_RE = re.compile(r"[*?]")


def validate_absolute_path(path: str) -> bool:
    """校验 Linux / Windows 文件绝对路径，拒绝空串、通配符和目录路径。"""
    if not path or not isinstance(path, str):
        return False

    normalized_path = path.strip()
    if not normalized_path or _INVALID_GLOB_RE.search(normalized_path):
        return False

    if normalized_path.endswith(("/", "\\")):
        return False

    file_name = extract_file_name(normalized_path)
    if not file_name or file_name in {".", ".."}:
        return False

    return bool(_LINUX_ABS_RE.match(normalized_path) or _WIN_ABS_RE.match(normalized_path))


def extract_file_name(path: str) -> str:
    """兼容 Linux / Windows 绝对路径提取文件名。"""
    if not path or not isinstance(path, str):
        return ""

    normalized_path = path.strip()
    if _WIN_ABS_RE.match(normalized_path):
        return ntpath.basename(normalized_path)
    return posixpath.basename(normalized_path)
