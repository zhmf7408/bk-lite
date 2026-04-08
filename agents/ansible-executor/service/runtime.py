import logging
import os
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
        logger.info(
            "ansible collections path preset: application_root=%s collections_path=%s",
            application_root(),
            os.environ.get("ANSIBLE_COLLECTIONS_PATH"),
        )
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
            logger.info(
                "ansible collections path configured: application_root=%s collections_path=%s",
                root,
                collections_dir,
            )
            return
    logger.warning(
        "ansible collections path not found: application_root=%s candidates=%s",
        root,
        [str(candidate) for candidate in candidates],
    )
