"""Shared catalog and cart flows, including React Native list virtualization."""

import re

from appium.webdriver.common.appiumby import AppiumBy

from .android import by_id, rupees

SKU = "SKU-10001"  # In stock. Add starts at the minimum order quantity of two.


class Catalog:
    results = "catalog-results-count"
    search_input = "catalog-search-input"

    def __init__(self, ui):
        self.ui = ui

    def open(self):
        self.ui.tap("tab-catalog")
        self.wait_for_results()

    def wait_for_results(self):
        ui = self.ui
        ui.hidden("catalog-skeleton")

        def result_count(_):
            element = ui.find_visible(by_id(self.results))
            return (
                element
                and re.search(r"\d+", element.text)
                and "Searching" not in element.text
            )

        ui.wait(result_count, message="Catalog should show the final result count")

    def search(self, keyword):
        self.ui.enter(self.search_input, keyword)
        # The results update after a debounce. Wait for the new query to appear.
        self.ui.wait_contains(self.results, f"“{keyword}”")
        self.wait_for_results()

    def count(self):
        match = re.search(r"\d+", self.ui.value(self.results))
        assert match, "The catalog should show a numeric result count"
        return int(match.group())

    def prices(self):
        # A virtualized list exposes only the visible cards. Sort by screen position.
        locator = (
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().resourceIdMatches("product-price-SKU-.*")',
        )
        elements = [
            e for e in self.ui.driver.find_elements(*locator) if e.is_displayed()
        ]
        return [
            rupees(e.text)
            for e in sorted(elements, key=lambda e: (e.rect["y"], e.rect["x"]))
        ]

    def add(self, sku=SKU):
        self.ui.scroll_to(f"product-add-{sku}").click()
        self.ui.wait_contains("toast-message", "to cart", timeout=6)


class Cart:
    def __init__(self, ui):
        self.ui = ui

    def open(self):
        self.ui.tap("header-cart-button")
        self.ui.el("cart-screen")

    def coupon(self, code):
        ui = self.ui
        ui.scroll_to("cart-coupon-input", "cart-scroll")
        ui.enter("cart-coupon-input", code)
        ui.scroll_to("cart-coupon-apply-button", "cart-scroll").click()

    def increase_quantity(self, times):
        plus = self.ui.scroll_to(
            f"cart-item-qty-{SKU}-single-increment", "cart-scroll", direction="down"
        )
        for _ in range(times):
            plus.click()

    def checkout(self):
        button = self.ui.el("cart-checkout-button")
        assert button.is_enabled()
        button.click()
        self.ui.el("checkout-screen")
