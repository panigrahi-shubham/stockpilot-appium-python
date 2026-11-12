import pytest

from stockpilot.shopping import Catalog


@pytest.fixture
def catalog(signed_in):
    page = Catalog(signed_in)
    page.open()
    return page


@pytest.mark.smoke
def test_search_narrows_catalog(catalog):
    original = catalog.count()
    catalog.search("ghee")
    assert 0 < catalog.count() < original


def test_clearing_no_results_restores_catalog(catalog):
    ui = catalog.ui
    ui.enter(catalog.search_input, "zzzz-no-such-product")
    ui.el("catalog-empty")
    ui.tap("catalog-empty-action")
    field = ui.el(catalog.search_input)
    assert field.text in ("", field.get_attribute("hint"))
    catalog.wait_for_results()
    ui.wait(lambda _: catalog.count() > 50)


def test_sort_prices_low_to_high(catalog):
    catalog.ui.tap("catalog-sort-button")
    catalog.ui.tap("catalog-sort-option-price_asc")
    catalog.wait_for_results()
    prices = catalog.prices()
    assert len(prices) > 1
    assert prices == sorted(prices)


def test_product_long_press_adds_favourite(catalog):
    ui = catalog.ui
    ui.long_press("product-card-SKU-10001-open")
    ui.el("catalog-quick-actions")
    ui.tap("quick-action-favorite")
    ui.wait_contains("toast-message", "favourites")


def test_dairy_chip_filters_catalog(catalog):
    ui = catalog.ui
    ui.tap("catalog-category-dairy")
    catalog.wait_for_results()
    assert ui.el("catalog-category-dairy").is_selected()
    assert catalog.count() < 20
