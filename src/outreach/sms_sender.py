"""SMS sending via Twilio."""

import time
from dataclasses import dataclass

from src.config import get_key


@dataclass
class SMSResult:
    to_phone: str
    success: bool
    sid: str = ""
    error: str = ""


def send_sms(to_phone: str, body: str) -> SMSResult:
    """Send a single SMS via Twilio."""
    account_sid = get_key("TWILIO_ACCOUNT_SID")
    auth_token = get_key("TWILIO_AUTH_TOKEN")
    from_phone = get_key("TWILIO_PHONE_NUMBER")

    if not all([account_sid, auth_token, from_phone]):
        return SMSResult(to_phone=to_phone, success=False, error="Twilio credentials not configured")

    # Truncate to SMS limit
    if len(body) > 1600:
        body = body[:1597] + "..."

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_phone,
            to=to_phone,
        )
        return SMSResult(to_phone=to_phone, success=True, sid=message.sid)
    except ImportError:
        # Twilio SDK not installed, use REST API directly
        import requests
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        data = {
            "To": to_phone,
            "From": from_phone,
            "Body": body,
        }
        resp = requests.post(url, data=data, auth=(account_sid, auth_token), timeout=10)
        if resp.status_code in (200, 201):
            return SMSResult(to_phone=to_phone, success=True, sid=resp.json().get("sid", ""))
        else:
            return SMSResult(to_phone=to_phone, success=False, error=resp.text)
    except Exception as e:
        return SMSResult(to_phone=to_phone, success=False, error=str(e))


def send_sms_batch(
    recipients: list[dict],
    body_template: str,
    rate_limit: float = 1.0,
    on_progress: callable = None,
) -> list[SMSResult]:
    """Send SMS to a batch of recipients with rate limiting.

    Each recipient dict should have: phone, and any template variables.
    """
    results = []
    for i, recipient in enumerate(recipients):
        phone = recipient.get("phone", "")
        if not phone:
            results.append(SMSResult(to_phone="", success=False, error="No phone"))
            continue

        # Fill template variables
        personalized = body_template
        for key, value in recipient.items():
            personalized = personalized.replace(f"{{{key}}}", str(value))

        result = send_sms(to_phone=phone, body=personalized)
        results.append(result)

        if on_progress:
            on_progress(i + 1, len(recipients), result)

        if rate_limit > 0 and i < len(recipients) - 1:
            time.sleep(rate_limit)

    return results
