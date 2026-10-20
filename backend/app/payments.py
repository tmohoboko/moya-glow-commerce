"""Stripe sandbox only. Card details are handled on Stripe's hosted page."""
import os
from urllib.parse import urlsplit

import stripe
from fastapi import HTTPException


def configured():
    return os.getenv("STRIPE_SECRET_KEY", "").startswith("sk_test_") and os.getenv("STRIPE_WEBHOOK_SECRET", "").startswith("whsec_")


def client():
    if not configured():
        raise HTTPException(503, "Test checkout is not configured yet.")
    return stripe.StripeClient(os.environ["STRIPE_SECRET_KEY"], max_network_retries=1,
                               http_client=stripe.RequestsClient(timeout=15))


def create_checkout(order, email, base_url):
    try:
        session = client().v1.checkout.sessions.create({
            "mode": "payment", "payment_method_types": ["card"],
            "client_reference_id": order["id"], "customer_email": email,
            "metadata": {"order_id": order["id"]},
            "success_url": f"{base_url}/checkout/return?order={order['id']}",
            "cancel_url": f"{base_url}/checkout/cancel?order={order['id']}",
            "line_items": [{"quantity": item["quantity"], "price_data": {
                "currency": "zar", "unit_amount": item["unit_amount"],
                "product_data": {"name": item["name"]}}} for item in order["items"]],
        }, options={"idempotency_key": f"lb-checkout-{order['id']}"})
        if session.livemode or not session.id.startswith("cs_test_") or urlsplit(session.url).netloc != "checkout.stripe.com":
            raise HTTPException(502, "Unable to open a sandbox checkout.")
        return {"id": session.id, "url": session.url}
    except stripe.StripeError:
        raise HTTPException(502, "Stripe test checkout is temporarily unavailable. Please retry.") from None


def verify_event(payload, signature):
    if not configured():
        raise HTTPException(503, "Test checkout is not configured yet.")
    try:
        return stripe.Webhook.construct_event(payload, signature, os.environ["STRIPE_WEBHOOK_SECRET"]).to_dict()
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(400, "Invalid webhook signature.") from None
