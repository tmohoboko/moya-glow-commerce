import json
from urllib.parse import parse_qs

import pytest
import stripe
from fastapi import HTTPException

from backend.app import payments


def test_current_sdk_checkout_payload_and_idempotency(monkeypatch):
    captured = []
    class Transport(stripe.HTTPClient):
        name = "unit-test"
        def request(self, method, url, headers, post_data=None, **kwargs):
            captured.append((method, url, headers, parse_qs(post_data)))
            return json.dumps({"object": "checkout.session", "id": "cs_test_fixture", "livemode": False,
                               "url": "https://checkout.stripe.com/c/pay/cs_test_fixture"}), 200, {}
    sdk = stripe.StripeClient("sk_test_fixture", http_client=Transport(), max_network_retries=0)
    monkeypatch.setattr(payments, "client", lambda: sdk)
    order = {"id": "order-fixture", "items": [{"name": "Full Body", "quantity": 2, "unit_amount": 45000}]}
    assert payments.create_checkout(order, "customer@example.com", "https://preview.example")["id"] == "cs_test_fixture"
    method, url, headers, body = captured[0]
    assert method.lower() == "post" and url == "https://api.stripe.com/v1/checkout/sessions"
    assert headers["Idempotency-Key"] == "lb-checkout-order-fixture"
    assert body["line_items[0][price_data][currency]"] == ["zar"]
    assert body["line_items[0][price_data][unit_amount]"] == ["45000"]
    assert body["line_items[0][quantity]"] == ["2"]
    assert body["metadata[order_id]"] == ["order-fixture"]
    assert body["success_url"] == ["https://preview.example/checkout/return?order=order-fixture"]


def test_live_keys_are_never_used(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_rejected")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_fixture")
    with pytest.raises(HTTPException) as error:
        payments.client()
    assert error.value.status_code == 503
