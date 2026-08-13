"""Entry point used when Pathlight's local API is packaged as a desktop sidecar."""

import os
from pathlib import Path

import uvicorn


def configure_runtime_directory() -> None:
    """Keep SQLite and uploads in the app-data directory, never beside the executable."""
    data_dir = Path(os.environ.get("PATHLIGHT_DATA_DIR", Path.cwd()))
    data_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(data_dir)


def main() -> None:
    configure_runtime_directory()
    from app.main import app

    port = int(os.environ.get("PATHLIGHT_API_PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
