import json
import os
import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _compose_config(**variables):
    environment = os.environ.copy()
    environment.update(variables)
    result = subprocess.run(
        ["docker", "compose", "config", "--format", "json"],
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_compose_wires_frontend_api_base_at_build_and_runtime():
    configured_url = "https://api.example.test/api/v1"
    config = _compose_config(VITE_API_BASE_URL=configured_url)
    frontend = config["services"]["frontend"]

    assert frontend["build"]["args"]["VITE_API_BASE_URL"] == configured_url
    assert frontend["environment"]["VITE_API_BASE_URL"] == configured_url


def test_frontend_image_contains_runtime_api_config_bootstrap():
    dockerfile = (REPOSITORY_ROOT / "frontend" / "Dockerfile").read_text()
    entrypoint = REPOSITORY_ROOT / "frontend" / "docker-entrypoint.d" / "40-runtime-config.sh"

    assert "ARG VITE_API_BASE_URL" in dockerfile
    assert "40-runtime-config.sh" in dockerfile
    assert "VITE_API_BASE_URL" in entrypoint.read_text()
