# Sidecar Installer Build & Release Runbook

## Artifacts

- Windows installer filename: `bklite-controller-installer.exe`
- Linux installer filename: `bklite-controller-installer`

Default object storage layout:

- Latest path: `installer/<os>/<filename>`

Examples:

- `installer/windows/bklite-controller-installer.exe`
- `installer/linux/bklite-controller-installer`

## Build

From `agents/sidecar-installer/`:

```bash
make install-deps
make build
```

`make install-deps` will try to install build dependencies for:

- macOS: Homebrew
- Linux: `apt-get`, `dnf`, `yum`, `apk`, `pacman`, `zypper`
- Windows: `winget` or `choco`

Installed dependencies include Go, Python 3, Pillow, and NSIS.

To avoid Homebrew / PEP 668 system Python restrictions, Pillow is installed into a local virtualenv at `agents/sidecar-installer/.venv`, and subsequent build steps reuse that virtualenv automatically.

Outputs:

- Windows NSIS installer: `bklite-controller-installer.exe`
- Linux installer binary: `bklite-controller-installer`

Notes:

- `setup-worker.exe` is an internal Windows build artifact produced before NSIS packaging.
- The final distributable for Windows users is only `bklite-controller-installer.exe`.
- `bklite-controller-installer.exe` already embeds `setup-worker.exe`, extracts it during installation, uses it to perform the actual install steps, and then cleans it up.
- For release/upload, do not distribute `setup-worker.exe` separately.

## Upload

From `server/`:

```bash
python manage.py installer_init --os windows --file_path /path/to/bklite-controller-installer.exe
python manage.py installer_init --os linux --file_path /path/to/bklite-controller-installer
```

`installer_init` now uploads only the latest path and no longer accepts a version argument.

Upload behavior:

1. Uploads only to the latest path
2. Windows upload target: `installer/windows/bklite-controller-installer.exe`
3. Linux upload target: `installer/linux/bklite-controller-installer`

## Runtime APIs

### Installer session

- `GET /api/v1/node_mgmt/open_api/installer/session?token=...`

Returns the installer session consumed by both Windows and Linux installers.

### Installer manifest

- `GET /api/proxy/node_mgmt/api/installer/manifest/`

Returns latest artifact metadata for Windows and Linux.

### Installer metadata by OS

- `GET /api/proxy/node_mgmt/api/installer/metadata/windows/`
- `GET /api/proxy/node_mgmt/api/installer/metadata/linux/`

Returns latest artifact metadata for the target OS.

## Cloud Region Variables

Recommended direct-download variables:

- `NATS_SERVERS`
- `NATS_PROTOCOL`
- `NATS_TLS_CA`
- `NATS_DOWNLOAD_USERNAME`
- `NATS_DOWNLOAD_PASSWORD`
- `NATS_INSTALLER_BUCKET`

Fallbacks still exist, but the preferred model is a dedicated download-only credential and bucket.
