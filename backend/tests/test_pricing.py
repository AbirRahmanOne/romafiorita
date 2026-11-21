from app.domain.pricing import QuoteLine, compute_quote


def test_single_item() -> None:
    q = compute_quote([QuoteLine(unit_price_cents=4900, quantity=1)])
    assert q.subtotal_cents == 4900
    assert q.delivery_cents == 0
    assert q.time_fee_cents == 0
    assert q.total_cents == 4900
    assert q.currency == "EUR"


def test_quantity_and_addons() -> None:
    q = compute_quote(
        [QuoteLine(unit_price_cents=5000, quantity=2, addon_prices_cents=[1200, 1800])]
    )
    # (5000 + 1200 + 1800) * 2 = 16000
    assert q.subtotal_cents == 16000
    assert q.total_cents == 16000


def test_window_and_exact_time_fees() -> None:
    line = [QuoteLine(unit_price_cents=4900, quantity=1)]
    assert compute_quote(line, "window").time_fee_cents == 500
    assert compute_quote(line, "exact").time_fee_cents == 900
    assert compute_quote(line, "courier").time_fee_cents == 0
    assert compute_quote(line, "standard").time_fee_cents == 0


def test_exact_fee_added_to_total() -> None:
    q = compute_quote([QuoteLine(unit_price_cents=4900, quantity=1)], "exact")
    assert q.total_cents == 4900 + 900


def test_empty_cart() -> None:
    q = compute_quote([])
    assert q.total_cents == 0
