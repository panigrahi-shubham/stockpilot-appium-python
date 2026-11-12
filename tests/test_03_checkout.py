import re

import pytest

from stockpilot.shopping import SKU, Cart, Catalog


@pytest.fixture
def cart(signed_in):
    catalog = Catalog(signed_in)
    catalog.open()
    catalog.add()
    page = Cart(signed_in)
    page.open()
    return page


def test_coupon_requires_minimum_cart_value(cart):
    ui = cart.ui
    cart.coupon("B2B10")
    ui.wait_contains("cart-coupon-input-error", "more to use this code")
    cart.increase_quantity(4)
    assert re.fullmatch(r"\d+", ui.value(f"cart-item-qty-{SKU}-single-value"))
    cart.coupon("B2B10")
    ui.wait_contains("cart-coupon-status", "You save")


def test_swipe_left_deletes_only_cart_item(cart):
    ui = cart.ui
    ui.mobile(
        "swipeGesture",
        elementId=ui.el(f"cart-item-{SKU}-single").id,
        direction="left",
        percent=0.8,
    )
    ui.tap(f"cart-item-delete-{SKU}-single")
    ui.el("cart-empty")


@pytest.mark.smoke
def test_checkout_validates_delivery_step(cart):
    ui = cart.ui
    cart.increase_quantity(2)
    cart.checkout()
    ui.el("checkout-step-0-active")
    ui.tap("checkout-continue-button")
    ui.el("checkout-step-1-active")
    ui.tap("checkout-continue-button")
    assert ui.value("checkout-delivery-date-error") == "Select a delivery date"
    # The delivery options can extend below the fixed footer on a denser emulator.
    slot_error = ui.scroll_to("checkout-slot-error", "checkout-scroll")
    assert slot_error.text == "Select a delivery slot"
    evening = ui.scroll_to("checkout-slot-evening", "checkout-scroll", direction="down")
    assert not evening.is_enabled()


def test_checkout_back_prompts_to_stay(cart):
    ui = cart.ui
    cart.increase_quantity(2)
    cart.checkout()
    ui.driver.back()
    ui.text("Leave checkout?")
    ui.text("STAY").click()
    ui.el("checkout-screen")
