from pathlib import Path
import subprocess


def ensure_ansible_windows_collection(
    collections_root: Path,
    cwd: Path | None = None,
) -> Path:
    root = Path(collections_root).resolve()
    windows_root = root / "ansible_collections" / "ansible" / "windows"
    if windows_root.exists():
        return windows_root
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ansible-galaxy",
            "collection",
            "install",
            "ansible.windows",
            "-p",
            str(root),
            "--force",
        ],
        check=True,
        cwd=str(Path(cwd).resolve() if cwd else Path.cwd()),
    )
    return windows_root
