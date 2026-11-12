import pytest

from stockpilot.login import BUYER, LOCKED


def test_empty_form_shows_required_fields(login):
    ui = login.ui
    ui.tap("login-submit-button")
    assert ui.value("login-email-input-error") == "Email is required"
    assert ui.value("login-password-input-error") == "Password is required"


def test_wrong_password_shows_error(login):
    login.submit(password="wrong123")
    login.ui.wait_contains("login-error-message", "Incorrect email or password")


def test_locked_account_cannot_sign_in(login):
    login.submit(LOCKED)
    login.ui.wait_contains("login-error-message", "locked")


@pytest.mark.smoke
def test_wrong_otp_then_sms_code_signs_in(login):
    login.submit()
    code = login.sms_code()
    login.enter_otp("000000")
    login.ui.wait_contains("otp-error", "Incorrect OTP")
    login.enter_otp(code)
    login.wait_home()
    login.ui.wait_contains("header-title", "Ravi")


def test_remember_me_persists_after_logout_and_relaunch(login):
    ui = login.ui
    login.submit(remember=True)
    login.enter_otp(login.sms_code())
    login.wait_home()
    ui.tap("tab-account")
    ui.scroll_to("account-row-logout", "account-scroll").click()
    ui.text("Log out?")
    ui.el("android:id/button1").click()
    ui.el("login-screen")
    ui.relaunch()
    assert ui.value("login-email-input") == BUYER
