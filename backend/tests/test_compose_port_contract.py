import json
import os
import subprocess


REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _compose_config(**variables):
    environment = os.environ.copy()
    environment.pop("POSTGRES_PORT", None)
    environment.pop("FRONTEND_PORT", None)
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


def _published_port(config, service):
    return config["services"][service]["ports"][0]


def test_compose_preserves_default_host_ports_and_container_ports():
    config = _compose_config()

    postgres = _published_port(config, "postgres")
    frontend = _published_port(config, "frontend")

    assert (postgres["published"], postgres["target"]) == ("5432", 5432)
    assert (frontend["published"], frontend["target"]) == ("3000", 80)


def test_compose_parameterizes_postgres_and_frontend_host_ports():
    config = _compose_config(POSTGRES_PORT="55432", FRONTEND_PORT="43000")

    postgres = _published_port(config, "postgres")
    frontend = _published_port(config, "frontend")

    assert (postgres["published"], postgres["target"]) == ("55432", 5432)
    assert (frontend["published"], frontend["target"]) == ("43000", 80)


def test_compose_persists_import_storage_for_backend_recreation():
    config = _compose_config(IMPORT_STORAGE_DIR="/var/lib/elite-imports")

    backend_volumes = config["services"]["backend"]["volumes"]
    assert any(
        volume["source"] == "import_storage" and volume["target"] == "/var/lib/elite-imports"
        for volume in backend_volumes
    )
    assert "import_storage" in config["volumes"]


def test_compose_passes_configured_import_business_timezone_to_backend():
    config = _compose_config(IMPORT_DEFAULT_TIMEZONE="America/New_York")

    backend_environment = config["services"]["backend"]["environment"]

    assert backend_environment["IMPORT_DEFAULT_TIMEZONE"] == "America/New_York"
