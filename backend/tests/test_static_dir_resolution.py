import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import _register_frontend_routes, _resolve_static_dir


TEST_LAYOUT_ROOT = Path(__file__).resolve().parent / ".test-layouts"


def _create_layout_root():
    root = TEST_LAYOUT_ROOT / str(uuid4())
    root.mkdir(parents=True, exist_ok=False)
    return root


def _remove_layout_root(root: Path):
    shutil.rmtree(root, ignore_errors=True)


def test_resolve_static_dir_prefers_configured_existing_path():
    root = _create_layout_root()
    try:
        backend_root = root / "backend"
        backend_root.mkdir(parents=True)

        configured = root / "configured-static"
        configured.mkdir(parents=True)

        repo_fallback = root / "frontend" / "dist"
        repo_fallback.mkdir(parents=True)

        resolved = _resolve_static_dir(configured_static_dir=str(configured), backend_root=backend_root)

        assert resolved == configured
    finally:
        _remove_layout_root(root)


def test_resolve_static_dir_uses_repo_layout_fallback():
    root = _create_layout_root()
    try:
        backend_root = root / "backend"
        backend_root.mkdir(parents=True)

        repo_fallback = root / "frontend" / "dist"
        repo_fallback.mkdir(parents=True)

        resolved = _resolve_static_dir(configured_static_dir=None, backend_root=backend_root)

        assert resolved == repo_fallback
    finally:
        _remove_layout_root(root)


def test_resolve_static_dir_uses_packaged_sibling_fallback():
    root = _create_layout_root()
    try:
        backend_root = root / "app.asar.unpacked" / "backend"
        backend_root.mkdir(parents=True)

        packaged_fallback = root / "frontend" / "dist"
        packaged_fallback.mkdir(parents=True)

        resolved = _resolve_static_dir(configured_static_dir=None, backend_root=backend_root)

        assert resolved == packaged_fallback
    finally:
        _remove_layout_root(root)


def test_register_frontend_routes_serves_spa_with_fallback_dist():
    root = _create_layout_root()
    try:
        backend_root = root / "backend"
        backend_root.mkdir(parents=True)

        static_dir = root / "frontend" / "dist"
        assets_dir = static_dir / "assets"
        assets_dir.mkdir(parents=True)

        (static_dir / "index.html").write_text("<html><body>elite-intel</body></html>")
        (static_dir / "runtime-config.js").write_text("window.RUNTIME_CONFIG = {};")
        (assets_dir / "app.js").write_text("console.log('asset-ok');")

        resolved = _resolve_static_dir(configured_static_dir=None, backend_root=backend_root)
        assert resolved == static_dir

        test_app = FastAPI()
        _register_frontend_routes(test_app, resolved)
        client = TestClient(test_app)

        assert client.get("/").status_code == 200
        assert "elite-intel" in client.get("/deep/link").text
        assert "RUNTIME_CONFIG" in client.get("/runtime-config.js").text
        assert "asset-ok" in client.get("/assets/app.js").text
    finally:
        _remove_layout_root(root)
