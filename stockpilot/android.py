"""The Android operations shared by the migrated test scenarios."""

import re

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.support.ui import WebDriverWait

APP = "com.stockpilot.b2b"


def by_id(value):
    return AppiumBy.ID, value


def by_text(value):
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{escaped}")'


def rupees(value):
    return float(re.sub(r"[^\d.]", "", value))


class Android:
    def __init__(self, driver):
        self.driver = driver

    def wait(self, condition, *, timeout=15, message=""):
        # React Native can replace nodes during re-render. Re-locate them on every poll.
        return WebDriverWait(
            self.driver,
            timeout,
            poll_frequency=0.35,
            ignored_exceptions=(StaleElementReferenceException,),
        ).until(condition, message)

    def find_visible(self, locator):
        return next(
            (
                element
                for element in self.driver.find_elements(*locator)
                if element.is_displayed()
            ),
            None,
        )

    def visible(self, locator, timeout=15):
        return self.wait(
            lambda _: self.find_visible(locator), timeout=timeout, message=str(locator)
        )

    def el(self, test_id, timeout=15):
        return self.visible(by_id(test_id), timeout)

    def text(self, value, timeout=15):
        return self.visible(by_text(value), timeout)

    def hidden(self, test_id, timeout=15):
        self.wait(
            lambda _: not self.find_visible(by_id(test_id)),
            timeout=timeout,
            message=test_id,
        )

    def tap(self, test_id):
        self.el(test_id).click()

    def value(self, test_id):
        return self.el(test_id).text

    def enter(self, test_id, value):
        field = self.el(test_id)
        field.click()
        field.clear()
        if value:
            field.send_keys(value)

    def mobile(self, command, **arguments):
        return self.driver.execute_script(f"mobile: {command}", arguments)

    def relaunch(self):
        self.driver.terminate_app(APP)
        self.driver.activate_app(APP)

    def deep_link(self, path):
        self.mobile(
            "deepLink", url=f"stockpilot://{path}", package=APP, waitForLaunch=True
        )

    def long_press(self, test_id):
        self.mobile("longClickGesture", elementId=self.el(test_id).id, duration=800)

    def swipe(self, direction, *, container=None, percent=0.65):
        # Use the visible center of the scroll area to avoid system bars and the raised Scan tab.
        window = self.driver.get_window_size()
        width, height = window["width"], window["height"]
        if container:
            bounds = self.el(container).rect
        else:
            bounds = {"x": 0, "y": 0, "width": width, "height": height}
        # Horizontal swipes must start beyond Android's edge Back hit area.
        edge_margin = 0.14 if direction in ("left", "right") else 0.08
        left = max(bounds["x"], round(width * edge_margin))
        right = min(bounds["x"] + bounds["width"], round(width * (1 - edge_margin)))
        top = max(bounds["y"], round(height * 0.15))
        bottom = min(bounds["y"] + bounds["height"], round(height * 0.78))
        self.mobile(
            "swipeGesture",
            left=left,
            top=top,
            width=right - left,
            height=bottom - top,
            direction=direction,
            percent=percent,
            speed=round(height * 0.8),
        )

    def scroll_to(self, test_id, container=None, *, direction="up", guard_bottom=True):
        height = self.driver.get_window_size()["height"]
        for _ in range(12):
            element = self.find_visible(by_id(test_id))
            if element:
                bounds = element.rect
                center = bounds["y"] + bounds["height"] / 2
                if not guard_bottom or height * 0.14 <= center <= height * 0.78:
                    return element
                swipe_direction = "down" if center < height * 0.14 else "up"
            else:
                swipe_direction = direction
            self.swipe(swipe_direction, container=container, percent=0.47)
        raise AssertionError(f"{test_id} did not scroll into the tappable area")

    def drag(self, source, target):
        def center(test_id):
            bounds = self.el(test_id).rect
            return round(bounds["x"] + bounds["width"] / 2), round(
                bounds["y"] + bounds["height"] / 2
            )

        start, end = center(source), center(target)
        # A hold before movement activates the reorder handle instead of scrolling the list.
        actions = ActionBuilder(
            self.driver,
            mouse=PointerInput(interaction.POINTER_TOUCH, "finger"),
            duration=550,
        )
        finger = actions.pointer_action
        finger.move_to_location(*start)
        finger.pointer_down()
        finger.pause(0.8)
        finger.move_to_location(*end)
        finger.pause(0.25)
        finger.release()
        actions.perform()

    def wait_contains(self, test_id, expected, timeout=15):
        def has_text(_):
            element = self.find_visible(by_id(test_id))
            return element and expected.casefold() in element.text.casefold()

        self.wait(
            has_text, timeout=timeout, message=f"{test_id} should contain {expected!r}"
        )

    def optional(self, locator, timeout=2):
        try:
            return self.visible(locator, timeout)
        except TimeoutException:
            return None
