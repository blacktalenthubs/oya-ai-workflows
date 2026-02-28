"""Email validation: format checking, MX record lookup, bounce risk scoring."""

import re
import socket
from dataclasses import dataclass


@dataclass
class EmailValidationResult:
    email: str
    is_valid_format: bool = False
    has_mx_record: bool = False
    is_free_provider: bool = False
    bounce_risk: float = 1.0  # 0.0 = safe, 1.0 = high risk
    reason: str = ""


# Common free email providers (not ideal for B2B outreach)
FREE_PROVIDERS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "icloud.com", "mail.com", "protonmail.com", "zoho.com", "yandex.com",
    "live.com", "msn.com", "gmx.com", "fastmail.com",
}

# Known disposable/temporary email domains
DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "tempmail.com", "throwaway.email",
    "10minutemail.com", "trashmail.com", "fakeinbox.com",
}

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


def validate_email_format(email: str) -> bool:
    """Check if email matches valid format."""
    return bool(EMAIL_REGEX.match(email.strip().lower()))


def check_mx_record(domain: str) -> bool:
    """Check if domain has MX records (can receive email)."""
    try:
        socket.getaddrinfo(domain, None)
        # Try MX-specific lookup via DNS
        import dns.resolver
        answers = dns.resolver.resolve(domain, "MX")
        return len(answers) > 0
    except ImportError:
        # dnspython not installed, fall back to basic check
        try:
            socket.getaddrinfo(f"mail.{domain}", None)
            return True
        except socket.gaierror:
            # Just check if domain resolves at all
            try:
                socket.getaddrinfo(domain, None)
                return True
            except socket.gaierror:
                return False
    except Exception:
        return False


def validate_email(email: str) -> EmailValidationResult:
    """Full email validation: format, MX, bounce risk."""
    email = email.strip().lower()
    result = EmailValidationResult(email=email)

    # Format check
    if not validate_email_format(email):
        result.reason = "Invalid format"
        result.bounce_risk = 1.0
        return result
    result.is_valid_format = True

    domain = email.split("@")[1]

    # Disposable domain check
    if domain in DISPOSABLE_DOMAINS:
        result.reason = "Disposable email domain"
        result.bounce_risk = 0.95
        return result

    # Free provider check
    result.is_free_provider = domain in FREE_PROVIDERS

    # MX record check
    result.has_mx_record = check_mx_record(domain)

    # Calculate bounce risk
    if not result.has_mx_record:
        result.bounce_risk = 0.9
        result.reason = "No MX record found"
    elif result.is_free_provider:
        result.bounce_risk = 0.3
        result.reason = "Free email provider (less reliable for teams)"
    else:
        result.bounce_risk = 0.1
        result.reason = "Valid business email"

    return result


def validate_emails_batch(emails: list[str]) -> list[EmailValidationResult]:
    """Validate a batch of emails."""
    return [validate_email(e) for e in emails if e]
