import pytest

from stockpilot.android import by_text
from stockpilot.webview import WebView


@pytest.fixture
def account(signed_in):
    signed_in.tap("tab-account")
    return signed_in


def test_terms_scroll_enables_native_accept(account):
    ui = account
    ui.scroll_to("account-row-terms", "account-scroll").click()
    accept = "webview-accept-button"
    assert not ui.el(accept).is_enabled()
    terms = WebView(ui, "webview")
    terms.heading("Terms of Trade")
    # Touch scrolling triggers the page's read-to-end event and updates the native footer.
    terms.find(by_text("— End of document —"), max_swipes=30, guard_bottom=False)
    ui.swipe("up", container="webview")
    ui.wait(lambda _: ui.el(accept).is_enabled())
    ui.tap(accept)


def test_feedback_validation_requires_rating(account):
    ui = account
    ui.scroll_to("account-row-feedback", "account-scroll").click()
    ui.el("webview")
    feedback = WebView(ui, "webview")
    feedback.fill("Your name", "Ravi")
    feedback.fill("Comments", "Delivery was quick and the cartons were intact.")
    feedback.click("Submit feedback", guard_bottom=False)
    ui.text("Please select a rating.")
