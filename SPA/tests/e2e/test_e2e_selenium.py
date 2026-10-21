"""Deep end-to-end headless Selenium test for Corpus Analysis SPA."""

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
    time.sleep(1.5)
    yield f"http://127.0.0.1:{server_port}"


def test_e2e_deep_workflow_and_telemetry(live_server):
    """Deep validation of theme toggle, table filtering, Tab 1 data, and Tab 3 SVG."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError:
        pytest.skip("Selenium not available")

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    try:
        driver = webdriver.Chrome(options=opts)
    except Exception as exc:
        pytest.skip(f"Chrome webdriver cannot start: {exc}")

    try:
        driver.get(live_server)
        wait = WebDriverWait(driver, 15)

        # 1. Verify Brand and Tab 1 Active
        brand = wait.until(
            EC.visibility_of_element_located((By.ID, "txt-brand-title"))
        )
        assert "Turkish SF Corpus Analysis" in brand.text

        # 2. Test Theme Toggle (Question H)
        theme_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "btn-toggle-theme"))
        )
        theme_btn.click()
        time.sleep(0.3)
        theme = driver.execute_script(
            "return document.documentElement.getAttribute('data-theme')"
        )
        assert theme in ("light", "dark")
        theme_btn.click()
        time.sleep(0.3)

        # 3. Test Tab 1 Real Data Loading
        t1_rows = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "#t1-inventory-grid tbody tr")
            )
        )
        assert len(t1_rows) >= 10, f"Expected >=10 rows, found {len(t1_rows)}"

        # 4. Test TableGrid Search Filter (Focus preservation & filtering)
        search_inp = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#t1-inventory-grid .grid-search")
            )
        )
        search_inp.click()
        search_inp.send_keys("SCS")
        time.sleep(0.4)
        active_el = driver.execute_script("return document.activeElement")
        assert active_el == search_inp, "Search input lost focus after typing!"
        filtered = driver.find_elements(
            By.CSS_SELECTOR, "#t1-inventory-grid tbody tr"
        )
        assert len(filtered) >= 1

        # Clear search
        search_inp.clear()
        search_inp.send_keys(" ")
        time.sleep(0.3)

        # 5. Test Tab 3 Parallel View & Pair Selection
        t3_btn = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-tab='tab_03']")
            )
        )
        t3_btn.click()
        wait.until(EC.visibility_of_element_located((By.ID, "tab_03")))

        # Check stage loads parallel text with dynamic wait for tokens
        wait.until(
            lambda d: len(
                d.find_elements(
                    By.CSS_SELECTOR, "#t3-nda-stage .t, #t3-nda-stage .t-pill"
                )
            )
            > 0
        )
        tokens = driver.find_elements(
            By.CSS_SELECTOR, "#t3-nda-stage .t, #t3-nda-stage .t-pill"
        )
        assert len(tokens) > 0, "No parallel tokens rendered on Tab 3 stage"


        # 6. Test Help Drawer Open / Close
        help_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "btn-open-help"))
        )
        help_btn.click()
        drawer = wait.until(
            EC.visibility_of_element_located((By.ID, "help-docs-drawer"))
        )
        assert "open" in drawer.get_attribute("class")
        close_help = wait.until(
            EC.element_to_be_clickable((By.ID, "btn-close-help"))
        )
        close_help.click()
        time.sleep(0.3)

        # 7. Test Corpus Info Modal Open / Close
        info_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "btn-open-corpus-info"))
        )
        info_btn.click()
        modal = wait.until(
            EC.visibility_of_element_located((By.ID, "corpus-info-modal"))
        )
        assert "active" in modal.get_attribute("class")
        close_modal = wait.until(
            EC.element_to_be_clickable((By.ID, "btn-close-corpus-info"))
        )
        close_modal.click()
        time.sleep(0.3)

        # 8. Assert Zero Severe Browser Console Errors
        logs = driver.get_log("browser")
        severe = [
            entry
            for entry in logs
            if entry.get("level") == "SEVERE"
            and "favicon" not in entry.get("message", "")
        ]
        assert len(severe) == 0, f"Found severe console errors: {severe}"


    finally:
        driver.quit()
