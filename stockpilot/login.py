"""Login, the demo SMS overlay, and the authenticated home screen."""

import re

from .android import by_id

BUYER = "buyer@stockpilot.in"
LOCKED = "locked@stockpilot.in"
APPROVER = "approver@stockpilot.in"
PASSWORD = "Pilot@123"


class Login:
    def __init__(self, ui):
        self.ui = ui

    def skip_onboarding(self):
        ui = self.ui
        # The fresh install starts on onboarding. A restored app can start at Login.
        element = ui.wait(
            lambda _: (
                ui.find_visible(by_id("onboarding-skip-button"))
                or ui.find_visible(by_id("login-screen"))
            ),
        )
        if element.get_attribute("resource-id") == "onboarding-skip-button":
            element.click()
        ui.el("login-screen")

    def submit(self, email=BUYER, password=PASSWORD, *, remember=False):
        ui = self.ui
        ui.enter("login-email-input", email)
        # The keyboard can cover the password field on smaller emulator screens.
        ui.scroll_to("login-password-input", "login-scroll")
        ui.enter("login-password-input", password)
        if remember:
            ui.scroll_to("login-remember-checkbox", "login-scroll").click()
        ui.scroll_to("login-submit-button", "login-scroll").click()

    def sms_code(self):
        # The release demo shows its generated OTP in the in-app SMS preview.
        # Read it on each login because the value can change between sessions.
        message = self.ui.el("otp-sms-text", timeout=20).text
        code = re.search(r"\b\d{6}\b", message)
        assert code, "The demo SMS preview should contain a six-digit OTP"
        return code.group()

    def enter_otp(self, code):
        self.ui.enter("otp-input-0", code)
        self.ui.tap("otp-verify-button")

    def wait_home(self):
        ui = self.ui
        ui.wait(
            lambda _: (
                ui.find_visible(by_id("home-screen"))
                or ui.find_visible(by_id("promo-modal-close"))
            ),
            timeout=25,
            message="Expected the signed-in home screen",
        )
        # The demo promo appears only on some launches and can cover navigation.
        close = ui.optional(by_id("promo-modal-close"), timeout=3)
        if close:
            close.click()
            ui.hidden("promo-modal-close")
        ui.el("home-screen")

    def sign_in(self):
        self.submit()
        self.enter_otp(self.sms_code())
        self.wait_home()
