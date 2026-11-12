"""Interact with release WebViews through Android's accessibility hierarchy."""

from appium.webdriver.common.appiumby import AppiumBy


class WebView:
    def __init__(self, ui, test_id):
        self.ui = ui
        self.test_id = test_id

    def find(self, locator, *, max_swipes=14, guard_bottom=True):
        ui = self.ui
        height = ui.driver.get_window_size()["height"]
        for attempt in range(max_swipes + 1):
            element = ui.find_visible(locator)
            direction = "up"
            if element:
                bounds = element.rect
                viewport = ui.el(self.test_id).rect
                center = bounds["y"] + bounds["height"] / 2
                top = viewport["y"]
                bottom = top + viewport["height"]
                if guard_bottom:
                    bottom = min(bottom, height * 0.79)
                # Chromium exposes offscreen nodes in the native tree. Their centers
                # must also fall inside the visible WebView before we tap or assert.
                if bounds["height"] > 0 and top <= center < bottom:
                    return element
                if center < top:
                    direction = "down"
            if attempt < max_swipes:
                ui.swipe(direction, container=self.test_id, percent=0.48)
        raise AssertionError(f"WebView control was not reachable: {locator}")

    def heading(self, label, timeout=15):
        self.ui.el(self.test_id, timeout)
        return self.ui.text(label, timeout)

    def fill(self, label, value):
        # Android can expose an HTML label as a hint, text, or content description.
        # Restrict the selector to EditText so the adjacent label cannot match.
        locator = (
            AppiumBy.XPATH,
            f'//android.widget.EditText[@text="{label}" or @hint="{label}" or @content-desc="{label}"]',
        )
        field = self.find(locator)
        field.click()
        ui = self.ui
        ui.wait(lambda _: field.get_attribute("focused") == "true")
        ui.mobile("type", text=value)
        return field

    def click(self, label, *, guard_bottom=True):
        # An HTML button may expose an icon alongside its accessible name.
        button = (
            AppiumBy.XPATH,
            (
                f'//*[@resource-id="{self.test_id}"]//android.widget.Button'
                f'[contains(@text, "{label}") or @content-desc="{label}"]'
            ),
        )
        self.find(button, guard_bottom=guard_bottom).click()
