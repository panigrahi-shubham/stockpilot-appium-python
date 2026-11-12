from stockpilot.login import APPROVER


def test_swipe_onboarding_pages(ui):
    size = ui.driver.get_window_size()
    # Start well away from Android's Back gesture region so the swipe reaches the carousel.
    area = {
        "left": round(size["width"] * 0.14),
        "top": round(size["height"] * 0.30),
        "width": round(size["width"] * 0.72),
        "height": round(size["height"] * 0.10),
    }
    ui.el("onboarding-dot-0-active")
    ui.mobile("swipeGesture", **area, direction="left", percent=1.0)
    ui.el("onboarding-dot-1-active")
    ui.mobile("swipeGesture", **area, direction="left", percent=1.0)
    ui.el("onboarding-get-started-button")


def test_logo_long_press_opens_demo_account_picker(login):
    ui = login.ui
    ui.mobile("longClickGesture", elementId=ui.el("login-logo").id, duration=1500)
    ui.el("test-accounts-sheet")
    ui.tap("test-account-approver")
    assert ui.value("login-email-input") == APPROVER


def test_pinch_zoom_product_image(signed_in):
    ui = signed_in
    ui.deep_link("product/SKU-10003")
    ui.tap("product-image-0")
    assert ui.value("image-viewer-zoom-level") == "1.0×"
    # UiAutomator2 injects a simultaneous two-finger gesture.
    ui.mobile(
        "pinchOpenGesture", elementId=ui.el("image-viewer-canvas").id, percent=0.8
    )
    ui.wait(lambda _: float(ui.value("image-viewer-zoom-level").rstrip("×")) > 1.5)


def test_drag_reorders_quick_list(signed_in):
    ui = signed_in
    ui.deep_link("quick-list")
    assert ui.value("quick-list-position-SKU-10001") == "#1"
    ui.drag("quick-list-handle-SKU-10001", "quick-list-handle-SKU-10027")
    ui.wait_contains("quick-list-position-SKU-10001", "#4")


def test_scroll_until_app_version_is_visible(signed_in):
    ui = signed_in
    ui.deep_link("settings")
    assert ui.scroll_to(
        "settings-about-version", "settings-scroll", guard_bottom=False
    ).is_displayed()


def test_double_tap_product_image_adds_favourite(signed_in):
    ui = signed_in
    ui.deep_link("product/SKU-10010")
    ui.mobile("doubleClickGesture", elementId=ui.el("product-image-0").id)
    ui.wait_contains("toast-message", "Added to favourites")
