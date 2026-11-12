"""Appium session lifecycle, clean test state, and failure artifacts."""

import os
from pathlib import Path

import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.common.exceptions import WebDriverException

from stockpilot.android import APP, Android
from stockpilot.login import Login


def pytest_addoption(parser):
    group = parser.getgroup("stockpilot")
    group.addoption(
        "--device",
        default=os.getenv("ANDROID_UDID"),
        help="ADB serial of a disposable Android test device",
    )
    group.addoption(
        "--appium-url", default=os.getenv("APPIUM_URL", "http://127.0.0.1:4723")
    )
    group.addoption(
        "--apk",
        default=os.getenv("STOCKPILOT_APK"),
        help="Optional path to the existing release APK",
    )
    group.addoption(
        "--artifacts",
        default="artifacts",
        help="Directory for failure screenshots and UI hierarchies",
    )


@pytest.fixture(scope="session")
def appium_driver(pytestconfig):
    serial = pytestconfig.getoption("--device")
    if not serial:
        pytest.fail(
            "Pass --device with the ADB serial of your test emulator.", pytrace=False
        )
    options = UiAutomator2Options().load_capabilities(
        {
            "platformName": "Android",
            "appium:automationName": "UiAutomator2",
            "appium:udid": serial,
            "appium:appPackage": APP,
            "appium:appActivity": ".MainActivity",
            "appium:autoLaunch": False,
            # Use Appium's test IME so text entry does not cover controls during regression runs.
            "appium:hideKeyboard": True,
            # The fixture owns data reset. An individual test can relaunch and check persistence.
            "appium:noReset": True,
            "appium:newCommandTimeout": 180,
            "appium:adbExecTimeout": 120_000,
            "appium:uiautomator2ServerInstallTimeout": 120_000,
            "appium:uiautomator2ServerLaunchTimeout": 90_000,
        }
    )
    if apk := pytestconfig.getoption("--apk"):
        options.app = str(Path(apk).resolve(strict=True))

    driver = webdriver.Remote(pytestconfig.getoption("--appium-url"), options=options)
    try:
        # React Native exposes unqualified test IDs. Explicit waits also handle animated screens.
        driver.update_settings(
            {
                "disableIdLocatorAutocompletion": True,
                "waitForIdleTimeout": 300,
                "waitForSelectorTimeout": 0,
            }
        )
        yield driver
    finally:
        driver.quit()


@pytest.fixture
def ui(appium_driver):
    android = Android(appium_driver)
    appium_driver.orientation = "PORTRAIT"
    android.mobile("clearApp", appId=APP)
    appium_driver.activate_app(APP)
    return android


@pytest.fixture
def login(ui):
    page = Login(ui)
    page.skip_onboarding()
    return page


@pytest.fixture
def signed_in(login):
    login.sign_in()
    return login.ui


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    report = yield
    driver = item.funcargs.get("appium_driver")
    if report.failed and driver:
        # Capture before teardown while the failing screen is still present.
        destination = Path(item.config.getoption("--artifacts"))
        stem = f"{item.path.stem}-{item.name}-{report.when}"
        try:
            destination.mkdir(parents=True, exist_ok=True)
            driver.save_screenshot(str(destination / f"{stem}.png"))
            (destination / f"{stem}.xml").write_text(
                driver.page_source, encoding="utf-8"
            )
        except (OSError, WebDriverException) as error:
            # Artifact failures should never hide the original assertion or setup error.
            report.sections.append(("Appium artifact error", str(error)))
    return report
