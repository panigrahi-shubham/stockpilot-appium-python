import pytest
from appium.webdriver.common.appiumby import AppiumBy


@pytest.mark.smoke
def test_product_deep_link(signed_in):
    ui = signed_in
    ui.deep_link("product/SKU-10005")
    ui.el("product-screen")
    ui.wait_contains("product-sku", "SKU-10005")


def test_promo_deep_link_opens_cart(signed_in):
    ui = signed_in
    ui.deep_link("promo/DIWALI25")
    assert ui.value("promo-code") == "DIWALI25"
    ui.tap("promo-cart-button")
    ui.el("cart-screen")


def test_android_camera_permission(signed_in):
    ui = signed_in
    ui.tap("tab-scan")
    ui.tap("scan-allow-camera-button")
    # This is an Android system control and belongs to the permission controller package.
    ui.visible(
        (
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().resourceIdMatches(".*permissioncontroller:id/permission_allow_foreground_only_button")',
        )
    ).click()
    ui.el("scan-camera-container")


def test_barcode_checksum_and_valid_lookup(signed_in):
    ui = signed_in
    ui.tap("tab-scan")
    ui.enter("scan-manual-input", "1234567890123")
    ui.scroll_to("scan-manual-submit-button", "scan-scroll").click()
    ui.wait_contains("scan-manual-input-error", "valid check digit")
    ui.scroll_to("scan-sample-0", "scan-scroll").click()
    ui.scroll_to("scan-manual-submit-button", "scan-scroll").click()
    ui.scroll_to("scan-result-card", "scan-scroll", guard_bottom=False)


def test_reports_hides_rotate_hint_in_landscape(signed_in):
    ui = signed_in
    ui.deep_link("reports")
    ui.scroll_to("reports-rotate-hint", "reports-scroll", guard_bottom=False)
    try:
        ui.driver.orientation = "LANDSCAPE"
        ui.hidden("reports-rotate-hint")
    finally:
        ui.driver.orientation = "PORTRAIT"


def test_app_lock_after_background_and_pin_unlock(signed_in):
    ui = signed_in
    ui.deep_link("settings")
    ui.scroll_to("settings-app-lock-switch", "settings-scroll").click()
    ui.wait(
        lambda _: ui.el("settings-app-lock-switch").get_attribute("checked") == "true"
    )
    # The feature intentionally locks only after five seconds out of the foreground.
    ui.driver.background_app(6)
    ui.el("app-lock-screen")
    for key in "1234":
        ui.tap(f"app-lock-key-{key}")
    ui.hidden("app-lock-screen")
