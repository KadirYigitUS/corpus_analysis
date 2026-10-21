"""End-to-end headless Selenium test for Corpus Analysis SPA."""

import threading
import time

import pytest

from SPA.app import create_app


@pytest.fixture(scope="module")
def live_server():
    """Start SPA Flask server on an ephemeral port in a daemon thread."""
    app = create_app()
    server_port = 5098
    server_thread = threading.Thread(
        target=lambda: app.run(
            host="127.0.0.1", port=server_port, debug=False, use_reloader=False
        ),
        daemon=True,
    )
    server_thread.start()
    time.sleep(1.2)  # Give server time to bind
    yield f"http://127.0.0.1:{server_port}"


def test_e2e_tab_navigation_and_dom_elements(live_server):
    """Verify that all 11 tabs, modals, and drawers are present and interactive."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
    except ImportError:
        pytest.skip("Selenium or Chrome webdriver not available in environment")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as exc:
        pytest.skip(f"Chrome webdriver cannot start: {exc}")

    try:
        driver.get(live_server)
        time.sleep(1.5)

        # 1. Verify Global Header & Title
        title_el = driver.find_element(By.ID, "txt-brand-title")
        assert "Turkish SF Corpus Analysis" in title_el.text

        # 2. Verify all 11 Tab Buttons
        for i in range(1, 12):
            tab_id = f"tab_{i:02d}"
            btn = driver.find_element(
                By.CSS_SELECTOR, f"button[data-tab='{tab_id}']"
            )
            assert btn is not None
            btn.click()
            time.sleep(0.3)
            pane = driver.find_element(By.ID, tab_id)
            assert "active" in pane.get_attribute("class")

        # 3. Test Help & Formulas Drawer Open & Close
        help_btn = driver.find_element(By.ID, "btn-open-help")
        help_btn.click()
        time.sleep(0.5)
        drawer = driver.find_element(By.ID, "help-docs-drawer")
        assert "open" in drawer.get_attribute("class")

        close_help = driver.find_element(By.ID, "btn-close-help")
        close_help.click()
        time.sleep(0.3)
        assert "open" not in drawer.get_attribute("class")

        # 4. Test Corpus Info Modal Open & Close
        info_btn = driver.find_element(By.ID, "btn-open-corpus-info")
        info_btn.click()
        time.sleep(0.5)
        modal = driver.find_element(By.ID, "corpus-info-modal")
        assert "active" in modal.get_attribute("class")

        close_modal = driver.find_element(By.ID, "btn-close-corpus-info")
        close_modal.click()
        time.sleep(0.3)
        assert "active" not in modal.get_attribute("class")

    finally:
        driver.quit()
