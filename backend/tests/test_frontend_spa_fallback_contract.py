from pathlib import Path


FRONTEND_ROOT = Path(__file__).resolve().parents[2] / "frontend"


def test_nginx_serves_index_for_client_routes():
    nginx_config = (FRONTEND_ROOT / "nginx.conf").read_text()

    assert "try_files $uri $uri/ /index.html;" in nginx_config
