"""Email sending via SendGrid with CAN-SPAM compliance."""

import time
from dataclasses import dataclass

import requests

from src.config import get_key


@dataclass
class EmailResult:
    to_email: str
    success: bool
    status_code: int = 0
    error: str = ""


SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"


def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    body: str,
    from_email: str = "hello@oyakits.com",
    from_name: str = "OYA Team",
    unsubscribe_url: str = "",
) -> EmailResult:
    """Send a single email via SendGrid.

    Includes CAN-SPAM compliance headers:
    - From address with real name
    - Unsubscribe link in headers
    - Physical address in footer (appended automatically)
    """
    api_key = get_key("SENDGRID_API_KEY")
    if not api_key:
        return EmailResult(to_email=to_email, success=False, error="SendGrid API key not configured")

    # Append compliance footer
    compliance_footer = (
        "\n\n---\n"
        "OYA Sports | [Physical Address]\n"
        "You received this because we thought your team might be interested in custom kits.\n"
    )
    if unsubscribe_url:
        compliance_footer += f"Unsubscribe: {unsubscribe_url}\n"
    else:
        compliance_footer += "Reply STOP to unsubscribe.\n"

    full_body = body + compliance_footer

    payload = {
        "personalizations": [
            {
                "to": [{"email": to_email, "name": to_name}],
                "subject": subject,
            }
        ],
        "from": {"email": from_email, "name": from_name},
        "content": [{"type": "text/plain", "value": full_body}],
    }

    # Add unsubscribe header
    if unsubscribe_url:
        payload["headers"] = {"List-Unsubscribe": f"<{unsubscribe_url}>"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(SENDGRID_API_URL, json=payload, headers=headers, timeout=10)
        success = resp.status_code in (200, 201, 202)
        return EmailResult(
            to_email=to_email,
            success=success,
            status_code=resp.status_code,
            error="" if success else resp.text,
        )
    except requests.RequestException as e:
        return EmailResult(to_email=to_email, success=False, error=str(e))


def send_emails_batch(
    recipients: list[dict],
    subject: str,
    body_template: str,
    from_email: str = "hello@oyakits.com",
    from_name: str = "OYA Team",
    rate_limit: float = 1.0,
    on_progress: callable = None,
) -> list[EmailResult]:
    """Send emails to a batch of recipients with rate limiting.

    Each recipient dict should have: email, name, and any template variables.
    """
    results = []
    for i, recipient in enumerate(recipients):
        email = recipient.get("email", "")
        name = recipient.get("name", "")

        if not email:
            results.append(EmailResult(to_email="", success=False, error="No email"))
            continue

        # Fill in template variables
        personalized_body = body_template
        personalized_subject = subject
        for key, value in recipient.items():
            personalized_body = personalized_body.replace(f"{{{key}}}", str(value))
            personalized_subject = personalized_subject.replace(f"{{{key}}}", str(value))

        result = send_email(
            to_email=email,
            to_name=name,
            subject=personalized_subject,
            body=personalized_body,
            from_email=from_email,
            from_name=from_name,
        )
        results.append(result)

        if on_progress:
            on_progress(i + 1, len(recipients), result)

        # Rate limit
        if rate_limit > 0 and i < len(recipients) - 1:
            time.sleep(rate_limit)

    return results
