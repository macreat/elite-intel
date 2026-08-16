import socket
import subprocess
import time
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import Page, expect, sync_playwright


FRONTEND_ROOT = Path(__file__).resolve().parents[2] / "frontend"


def _free_port() -> int:
    with socket.socket() as socket_:
        socket_.bind(("127.0.0.1", 0))
        return int(socket_.getsockname()[1])


@pytest.fixture(scope="module")
def frontend_url():
    port = _free_port()
    process = subprocess.Popen(
        ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", str(port)],
        cwd=FRONTEND_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                break
        except OSError:
            time.sleep(0.25)
    else:
        output = process.stdout.read() if process.stdout else ""
        process.terminate()
        raise RuntimeError(f"Vite did not start on port {port}: {output}")

    try:
        yield f"http://127.0.0.1:{port}/import"
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        yield browser
        browser.close()


def _open_import_page(browser, frontend_url: str) -> Page:
    page = browser.new_page()
    page.goto(frontend_url)
    page.wait_for_load_state("networkidle")
    return page


def test_upload_step_renders_csv_xlsx_picker_and_copy(browser, frontend_url):
    page = _open_import_page(browser, frontend_url)

    expect(page.get_by_role("heading", name="1) Upload CSV or XLSX file")).to_be_visible()
    expect(page.get_by_text("Select a CSV or Excel (XLSX) file to start the import flow.")).to_be_visible()
    expect(page.get_by_text("Large Kardex/cuadernillo CSVs up to 250MB are supported.")).to_be_visible()
    expect(page.locator('input[type="file"]')).to_have_attribute("accept", ".csv,.xlsx")

    page.close()


def test_upload_step_executes_file_selection_behavior(browser, frontend_url):
    page = _open_import_page(browser, frontend_url)
    file_input = page.locator('input[type="file"]')
    upload_button = page.get_by_role("button", name="Upload file")

    expect(upload_button).to_be_disabled()
    file_input.set_input_files(
        {
            "name": "transactions.csv",
            "mimeType": "text/csv",
            "buffer": b"date,amount\n2026-01-01,10.00\n",
        }
    )

    expect(page.get_by_text("Selected: transactions.csv")).to_be_visible()
    expect(upload_button).to_be_enabled()

    page.close()


def test_import_mapping_submits_backend_occurred_at_key(browser, frontend_url):
    page = browser.new_page()
    mapping_requests = []

    def handle_upload(route):
        route.fulfill(
            status=201,
            content_type="application/json",
            body=json.dumps(
                {
                    "batch_id": 42,
                    "status": "PENDING",
                    "columns_detected": ["Date custom", "Type", "Category", "Description", "Amount"],
                    "suggested_mapping": {
                        "transaction_type": "Type",
                        "category": "Category",
                        "description": "Description",
                        "amount": "Amount",
                    },
                }
            ),
        )

    def handle_mapping(route):
        mapping_requests.append(json.loads(route.request.post_data or "{}"))
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "batch_id": 42,
                    "status": "VALIDATED",
                    "summary": {"records_total": 1, "records_valid": 1, "records_invalid": 0, "records_duplicate": 0},
                    "preview": [],
                    "invalid_rows": [],
                }
            ),
        )

    page.route("**/api/v1/imports/transactions", handle_upload)
    page.route("**/api/v1/imports/42/mapping", handle_mapping)
    page.goto(frontend_url)
    page.wait_for_load_state("networkidle")
    page.locator('input[type="file"]').set_input_files(
        {"name": "custom-date.csv", "mimeType": "text/csv", "buffer": b"Date custom,Amount\n2026-01-01,10\n"}
    )
    page.get_by_role("button", name="Upload file").click()
    page.locator("select").nth(0).select_option("Date custom")
    page.get_by_role("button", name="Validate mapping").click()

    expect(page.get_by_role("heading", name="Validation report")).to_be_visible()
    assert mapping_requests == [{"mapping": {"transaction_type": "Type", "category": "Category", "description": "Description", "amount": "Amount", "occurred_at": "Date custom"}}]
    page.close()


def test_transaction_edit_preserves_calendar_date_in_negative_offset_locale(browser, frontend_url):
    context = browser.new_context(timezone_id="America/Los_Angeles")
    page = context.new_page()
    update_requests = []

    def handle_transaction(route):
        if route.request.method == "PUT":
            update_requests.append(json.loads(route.request.post_data or "{}"))
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "id": 7,
                        "occurred_at": "2026-06-15T00:00:00Z",
                        "transaction_type": "INCOME",
                        "category_id": 1,
                        "description": "Timezone regression",
                        "amount": 100,
                        "currency_code": "ARS",
                        "product_id": None,
                        "notes": None,
                        "source_type": "MANUAL",
                        "created_at": "2026-06-15T00:00:00Z",
                        "updated_at": "2026-06-15T00:00:00Z",
                    }
                ),
            )
            return

        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "id": 7,
                    "occurred_at": "2026-06-15T07:00:00Z",
                    "transaction_type": "INCOME",
                    "category_id": 1,
                    "description": "Timezone regression",
                    "amount": 100,
                    "currency_code": "ARS",
                    "product_id": None,
                    "notes": None,
                    "source_type": "MANUAL",
                    "created_at": "2026-06-15T00:00:00Z",
                    "updated_at": "2026-06-15T00:00:00Z",
                }
            ),
        )

    page.route("**/api/v1/transactions/7", handle_transaction)
    page.route(
        "**/api/v1/categories*",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                [
                    {
                        "id": 1,
                        "name": "Timezone category",
                        "type": "INCOME",
                        "description": None,
                        "active": True,
                        "created_at": "2026-06-15T00:00:00Z",
                        "updated_at": "2026-06-15T00:00:00Z",
                    }
                ]
            ),
        ),
    )
    page.goto(frontend_url.replace("/import", "/transactions/7/edit"))
    page.wait_for_load_state("networkidle")

    expect(page.locator("#occurred_at")).to_have_value("2026-06-15")
    page.get_by_role("button", name="Save").click()
    page.wait_for_url("**/transactions")
    assert update_requests == [
        {
            "occurred_at": "2026-06-15T07:00:00.000Z",
            "transaction_type": "INCOME",
            "category_id": 1,
            "description": "Timezone regression",
            "amount": 100,
            "notes": None,
        }
    ]
    context.close()


@pytest.mark.parametrize(
    ("timezone_id", "expected_instant"),
    [
        ("America/Los_Angeles", "2026-08-15T07:00:00.000Z"),
        ("Asia/Tokyo", "2026-08-14T15:00:00.000Z"),
    ],
)
def test_new_transaction_form_submits_selected_local_calendar_date(browser, frontend_url, timezone_id, expected_instant):
    context = browser.new_context(timezone_id=timezone_id)
    page = context.new_page()
    create_requests = []

    def handle_api(route):
        path = urlparse(route.request.url).path
        if path.endswith("/categories"):
            body = [
                {
                    "id": 1,
                    "name": "Local calendar category",
                    "type": "INCOME",
                    "description": None,
                    "active": True,
                    "created_at": "2026-08-15T00:00:00Z",
                    "updated_at": "2026-08-15T00:00:00Z",
                }
            ]
            route.fulfill(status=200, content_type="application/json", body=json.dumps(body))
            return
        if path.endswith("/transactions") and route.request.method == "POST":
            create_requests.append(json.loads(route.request.post_data or "{}"))
            route.fulfill(status=201, content_type="application/json", body=json.dumps({"id": 1}))
            return
        route.fulfill(status=200, content_type="application/json", body="[]")

    page.route("**/api/v1/**", handle_api)
    page.goto(frontend_url.replace("/import", "/transactions/new"))
    page.wait_for_load_state("networkidle")
    page.locator("#occurred_at").fill("2026-08-15")
    page.locator("#category_id").select_option("1")
    page.locator("#description").fill("Local calendar transaction")
    page.locator("#amount").fill("10.00")
    page.get_by_role("button", name="Save").click()
    page.wait_for_url("**/transactions")

    assert create_requests[0]["occurred_at"] == expected_instant
    context.close()


def test_dashboard_transaction_request_uses_backend_datetime_filters(browser, frontend_url):
    transaction_urls = []
    page = browser.new_page()

    def handle_api(route):
        path = urlparse(route.request.url).path
        if path.endswith("/transactions"):
            transaction_urls.append(route.request.url)
            body = {"items": [], "total": 0, "page": 1, "page_size": 10}
        elif path.endswith("/dashboard/summary"):
            body = {
                "total_income": "0.00",
                "total_expenses": "0.00",
                "net_balance": "0.00",
                "estimated_savings": "0.00",
                "savings_rate": 0,
                "transaction_count": 0,
                "period": {"start_date": "2026-08-10", "end_date": "2026-08-16"},
            }
        elif path.endswith("/dashboard/categories") or path.endswith("/dashboard/timeseries"):
            body = []
        else:
            body = []
        route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

    page.route("**/api/v1/**", handle_api)
    page.goto(frontend_url.replace("/import", "/"))
    page.wait_for_load_state("networkidle")

    assert transaction_urls
    expected_timezone = page.evaluate("Intl.DateTimeFormat().resolvedOptions().timeZone")
    for transaction_url in transaction_urls:
        query = parse_qs(urlparse(transaction_url).query)
        assert query["start_date"][0] == "2026-08-01"
        assert len(query["end_date"][0]) == 10
        assert query["end_date"][0].startswith("2026-08-")
        assert query["timezone"] == [expected_timezone]
    page.close()


def test_custom_period_keeps_inclusive_calendar_dates_in_negative_offset_timezone(browser, frontend_url):
    context = browser.new_context(timezone_id="America/Los_Angeles")
    page = context.new_page()
    summary_urls = []

    def handle_api(route):
        path = urlparse(route.request.url).path
        if path.endswith("/dashboard/summary"):
            summary_urls.append(route.request.url)
            body = {
                "total_income": "0.00",
                "total_expenses": "0.00",
                "net_balance": "0.00",
                "estimated_savings": "0.00",
                "savings_rate": 0,
                "transaction_count": 0,
                "period": {"start_date": "2026-08-15", "end_date": "2026-08-20"},
            }
        elif path.endswith("/dashboard/categories") or path.endswith("/dashboard/timeseries"):
            body = []
        elif path.endswith("/transactions"):
            body = {"items": [], "total": 0, "page": 1, "page_size": 10}
        else:
            body = []
        route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

    page.route("**/api/v1/**", handle_api)
    page.goto(frontend_url.replace("/import", "/"))
    page.wait_for_load_state("networkidle")
    summary_urls.clear()

    page.locator("select").first.select_option("custom")
    date_inputs = page.locator('input[type="date"]')
    date_inputs.nth(0).fill("2026-08-15")
    date_inputs.nth(1).fill("2026-08-20")
    page.wait_for_timeout(500)

    assert summary_urls
    query = parse_qs(urlparse(summary_urls[-1]).query)
    assert query["start_date"] == ["2026-08-15"]
    assert query["end_date"] == ["2026-08-20"]
    assert query["timezone"] == ["America/Los_Angeles"]
    context.close()


@pytest.mark.parametrize(
    ("timezone_id", "expected_date"),
    [("America/Los_Angeles", "2026-08-13"), ("Asia/Tokyo", "2026-08-14")],
)
def test_transaction_form_default_preserves_local_calendar_date(browser, frontend_url, timezone_id, expected_date):
    context = browser.new_context(timezone_id=timezone_id)
    context.add_init_script(
        """
        (() => {
          const RealDate = Date;
          const fixedNow = RealDate.parse('2026-08-14T00:30:00.000Z');
          class MockDate extends RealDate {
            constructor(...args) {
              super(args.length === 0 ? fixedNow : args[0]);
            }
            static now() { return fixedNow; }
          }
          window.Date = MockDate;
        })();
        """
    )
    page = context.new_page()
    page.route(
        "**/api/v1/categories*",
        lambda route: route.fulfill(status=200, content_type="application/json", body="[]"),
    )
    page.goto(frontend_url.replace("/import", "/transactions/new"))
    page.wait_for_load_state("networkidle")

    expect(page.locator("#occurred_at")).to_have_value(expected_date)
    context.close()


def test_custom_period_keeps_inclusive_calendar_dates_in_positive_offset_timezone(browser, frontend_url):
    context = browser.new_context(timezone_id="Asia/Tokyo")
    page = context.new_page()
    summary_urls = []

    def handle_api(route):
        path = urlparse(route.request.url).path
        if path.endswith("/dashboard/summary"):
            summary_urls.append(route.request.url)
            body = {
                "total_income": "0.00",
                "total_expenses": "0.00",
                "net_balance": "0.00",
                "estimated_savings": "0.00",
                "savings_rate": 0,
                "transaction_count": 0,
                "period": {"start_date": "2026-08-15", "end_date": "2026-08-20"},
            }
        elif path.endswith("/dashboard/categories") or path.endswith("/dashboard/timeseries"):
            body = []
        elif path.endswith("/transactions"):
            body = {"items": [], "total": 0, "page": 1, "page_size": 10}
        else:
            body = []
        route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

    page.route("**/api/v1/**", handle_api)
    page.goto(frontend_url.replace("/import", "/"))
    page.wait_for_load_state("networkidle")
    summary_urls.clear()

    page.locator("select").first.select_option("custom")
    date_inputs = page.locator('input[type="date"]')
    date_inputs.nth(0).fill("2026-08-15")
    date_inputs.nth(1).fill("2026-08-20")
    page.wait_for_timeout(500)

    assert summary_urls
    query = parse_qs(urlparse(summary_urls[-1]).query)
    assert query["start_date"] == ["2026-08-15"]
    assert query["end_date"] == ["2026-08-20"]
    assert query["timezone"] == ["Asia/Tokyo"]
    context.close()


def test_frontend_uses_runtime_api_base_config(browser, frontend_url):
    page = browser.new_page()
    api_urls = []

    page.add_init_script(
        "window.__ELITE_CONFIG__ = { apiBaseUrl: 'https://api.example.test/api/v1' };"
    )

    def handle_api(route):
        api_urls.append(route.request.url)
        path = urlparse(route.request.url).path
        if path.endswith("/dashboard/summary"):
            body = {
                "total_income": "0.00",
                "total_expenses": "0.00",
                "net_balance": "0.00",
                "estimated_savings": "0.00",
                "savings_rate": 0,
                "transaction_count": 0,
                "period": {"start_date": "2026-08-01", "end_date": "2026-08-31"},
            }
        elif path.endswith("/dashboard/categories") or path.endswith("/dashboard/timeseries"):
            body = []
        elif path.endswith("/transactions"):
            body = {"items": [], "total": 0, "page": 1, "page_size": 10}
        else:
            body = []
        route.fulfill(status=200, content_type="application/json", body=json.dumps(body))

    page.route("https://api.example.test/api/v1/**", handle_api)
    page.goto(frontend_url.replace("/import", "/"))
    page.wait_for_load_state("networkidle")

    assert api_urls
    assert all(url.startswith("https://api.example.test/api/v1/") for url in api_urls)
    page.close()
