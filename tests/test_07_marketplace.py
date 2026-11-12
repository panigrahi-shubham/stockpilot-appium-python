from urllib.parse import quote

import pytest
from appium.webdriver.common.appiumby import AppiumBy

from stockpilot.android import by_id, rupees
from stockpilot.shopping import Catalog
from stockpilot.webview import WebView


def test_switch_to_seller_opens_hub(signed_in):
    ui = signed_in
    ui.tap("tab-account")
    ui.tap("account-mode-switch-seller")
    # Android exposes the badge text as a sibling of the badge container.
    ui.el("account-mode-badge")
    ui.text("SELLER")
    ui.tap("account-open-seller-hub")
    ui.el("seller-hub-screen")
    ui.hidden("seller-mode-off-card")


def test_listing_validation_spec_limit_and_draft_persistence(signed_in):
    ui = signed_in
    ui.deep_link("seller/product-form")
    ui.tap("listing-publish-button")
    assert (
        ui.value("listing-title-input-error") == "Title must be at least 10 characters"
    )
    assert ui.value("listing-photos-error") == "Add at least one photo"

    title = "Groundnut Oil 15 L Tin"
    ui.enter("listing-title-input", title)
    assert ui.value("listing-title-input-counter") == "22/80"
    add = "listing-add-spec-button"
    for count in range(2, 7):
        ui.scroll_to(add, "listing-form-scroll").click()
        assert (
            ui.scroll_to(
                "listing-spec-count",
                "listing-form-scroll",
                direction="down",
                guard_bottom=False,
            ).text
            == f"{count}/6"
        )
    assert not ui.scroll_to(add, "listing-form-scroll").is_enabled()

    ui.tap("listing-save-draft-button")
    # Saving should return directly. A discard dialog here is a product failure.
    ui.wait(
        lambda _: ui.find_visible(by_id("home-screen")),
        timeout=20,
        message="Saving a draft should return home without a discard confirmation",
    )
    ui.deep_link("seller/products")
    ui.enter("my-products-search-input", title)
    ui.text(title)


def test_lead_quotation_uses_quantity_and_unit_price(signed_in):
    ui = signed_in
    ui.deep_link("seller/lead/LD-9031")
    ui.el("lead-detail-status")
    ui.text("NEW")
    ui.scroll_to("lead-status-select-quoted", "lead-detail-scroll").click()
    ui.enter("lead-quote-input", "1800")
    ui.wait_contains("lead-quote-total", "72,000")
    ui.tap("lead-quote-send-button")
    ui.wait_contains("lead-detail-quote", "1,800")


def test_inbox_archive_can_be_undone(signed_in):
    ui = signed_in
    ui.deep_link("messages")
    row = "conversation-C-logistics"
    ui.mobile("swipeGesture", elementId=ui.el(row).id, direction="left", percent=0.8)
    ui.tap("conversation-archive-C-logistics")
    ui.hidden(row)
    ui.tap("toast-action")
    ui.el(row)


def test_chat_message_is_read_and_buyer_replies(signed_in):
    ui = signed_in
    ui.deep_link("chat?cid=C-buyer-1")
    ui.enter("chat-input", "Best I can do is ₹1,800")
    ui.tap("chat-send-button")
    ui.wait_contains("chat-last-status", "Read", timeout=6)
    ui.hidden("chat-typing-indicator", timeout=8)
    ui.visible(
        (
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textContains("15 days credit")',
        )
    )


def test_compare_products_side_by_side(signed_in):
    ui = signed_in
    Catalog(ui).open()
    for sku in ("SKU-10001", "SKU-10002"):
        product = ui.scroll_to(f"product-card-{sku}-open")
        ui.mobile("longClickGesture", elementId=product.id, duration=800)
        ui.tap("quick-action-compare")
        ui.hidden("catalog-quick-actions")
    assert ui.value("catalog-compare-count") == "2 selected to compare"
    ui.hidden("toast")
    ui.tap("catalog-compare-open")
    ui.el("compare-screen")
    ui.swipe("left", container="compare-table-scroll")
    ui.el("compare-column-SKU-10002")
    ui.scroll_to("compare-best-price", "compare-scroll", guard_bottom=False)


@pytest.mark.live
def test_live_usd_exchange_rate(signed_in):
    ui = signed_in
    ui.deep_link("market")
    ui.el("market-rate-USD", timeout=20)
    assert 50 < rupees(ui.value("market-rate-USD-inr")) < 150


@pytest.mark.live
def test_live_practice_portal_login(signed_in):
    ui = signed_in
    url = quote("https://the-internet.herokuapp.com/login", safe="")
    ui.deep_link(f"browser?url={url}")
    portal = WebView(ui, "browser-webview")
    portal.heading("Login Page", timeout=30)
    username = portal.fill("Username", "tomsmith")
    assert username.text == "tomsmith"
    portal.fill("Password", "SuperSecretPassword!")
    portal.click("Login")
    ui.visible(
        (
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textContains("You logged into a secure area!")',
        ),
        timeout=30,
    )
    assert ui.el("browser-back-button").is_enabled()
