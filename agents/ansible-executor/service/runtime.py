import os
import shutil
import sys
from pathlib import Path

from core.config import logger


def application_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def find_dotenv_path() -> str | None:
    candidates = [Path.cwd() / ".env", application_root() / ".env"]
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists() and resolved.is_file():
            return str(resolved)
    return None


def find_config_path(explicit_path: str | None = None) -> str | None:
    candidates: list[Path] = []
    if explicit_path:
        candidates.append(Path(explicit_path))

    candidates.extend(
        [
            Path.cwd() / "config.yml",
            Path.cwd() / "config.yaml",
            application_root() / "config.yml",
            application_root() / "config.yaml",
        ]
    )

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists() and resolved.is_file():
            return str(resolved)
    return None


def current_entrypoint_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable]
    return [sys.executable, str(application_root() / "main.py")]


def configure_ansible_environment() -> None:
    if os.environ.get("ANSIBLE_COLLECTIONS_PATH"):
        return
    root = application_root()
    candidates = [
        root / "collections",
        root / "ansible-executor" / "collections",
        root / "_internal" / "collections",
    ]
    for collections_dir in candidates:
        if collections_dir.exists() and collections_dir.is_dir():
            os.environ["ANSIBLE_COLLECTIONS_PATH"] = str(collections_dir)
            return


def repair_ansible_windows_collection_layout(collections_path: str | Path) -> bool:
    collections_root = Path(collections_path)
    windows_root = collections_root / "ansible_collections" / "ansible" / "windows"
    if not windows_root.exists() or not windows_root.is_dir():
        return False

    repaired = False
    for path in windows_root.rglob("*"):
        nested_file = path / path.name
        if not path.is_dir() or not nested_file.is_file():
            continue
        backup_content = nested_file.read_bytes()
        shutil.rmtree(path)
        path.write_bytes(backup_content)
        repaired = True
        logger.warning(
            "repaired ansible windows collection entry: path=%s nested_file=%s",
            path,
            nested_file,
        )

    return repaired
