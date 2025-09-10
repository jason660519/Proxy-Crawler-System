requirements.txt
playwright

tests/e2e/conftest.py
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

tests/e2e/test_playwright_smoke.py
def test_homepage(page):
    page.goto("http://localhost:3000")
    assert page.title() == "Expected Title"