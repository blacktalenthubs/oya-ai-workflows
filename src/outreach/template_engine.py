"""AI-powered outreach message generation with variable substitution."""

import json
import re

from openai import OpenAI

from src.config import get_key

# Default templates when OpenAI is not available
DEFAULT_EMAIL_TEMPLATES = {
    "youth": {
        "subject": "Custom kits for {team_name} - designed by your players",
        "body": """Hi {contact_name},

I came across {team_name} and wanted to reach out. At OYA, we help youth teams like yours get professional-quality custom kits at affordable prices.

What makes us different:
- Your players can help design their own kit using our AI designer
- Fast turnaround (2-3 weeks from design to delivery)
- Pricing built for youth team budgets

Would you be open to a quick chat about kitting out {team_name} for the upcoming season?

Best,
The OYA Team

P.S. Check out some of our designs at [website link]""",
    },
    "academy": {
        "subject": "OYA x {team_name} - Premium custom kits for your academy",
        "body": """Hi {contact_name},

We work with academies across the country to deliver premium custom kits that match the professionalism of your programme.

For {team_name}, we can offer:
- Full kit customization (home, away, training)
- AI-assisted design tool for quick iterations
- Bulk pricing for multiple age groups
- Dedicated account management

I'd love to show you what we can create for {team_name}. Do you have 15 minutes this week?

Best,
The OYA Team""",
    },
    "amateur": {
        "subject": "Kit up {team_name} with OYA - custom designs, team prices",
        "body": """Hi {contact_name},

Looking for new kits for {team_name}? We make it easy.

OYA lets you design custom kits in minutes using our AI design tool. Pick your colors, add your badge, and we handle the rest.

- No minimum order required
- Prices from [price] per jersey
- Full customization (names, numbers, sponsors)

Want to see a free mockup for {team_name}? Just reply with your team colors and we'll send one over.

Cheers,
The OYA Team""",
    },
    "default": {
        "subject": "Custom team kits for {team_name} by OYA",
        "body": """Hi {contact_name},

I'm reaching out from OYA - we design and produce custom soccer kits for teams of all levels.

We'd love to work with {team_name}. Our AI design tool lets you create your perfect kit in minutes, and we handle production and delivery.

Interested in seeing a free mockup? Just reply to this email.

Best,
The OYA Team""",
    },
}

DEFAULT_SMS_TEMPLATES = {
    "default": "Hi {contact_name}! OYA here - we make custom soccer kits for teams like {team_name}. Want to see a free mockup? Reply YES or check us out at [link]",
    "youth": "Hi {contact_name}! OYA makes affordable custom kits for youth teams. We'd love to kit out {team_name}. Interested? Reply YES for a free mockup!",
    "academy": "Hi {contact_name}, OYA works with academies to deliver premium custom kits. Can we show {team_name} what we can create? Reply YES!",
}

SYSTEM_PROMPT = """You are a sales copywriter for OYA, a soccer/football kit brand.
Write a personalized outreach message for a potential team customer.

Rules:
- Be friendly and professional, not pushy
- Reference the team by name and any known details
- Keep it concise
- Include a clear call-to-action
- Never use fake urgency or spam tactics
- Sound human, not like a template

Respond with JSON only:
{
    "subject": "email subject line",
    "body": "the full message body"
}"""


def fill_template(template: str, variables: dict) -> str:
    """Replace {variable_name} placeholders with values."""
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{key}}}", value or "there")
    # Replace any remaining unfilled variables with sensible defaults
    result = re.sub(r"\{contact_name\}", "there", result)
    result = re.sub(r"\{team_name\}", "your team", result)
    result = re.sub(r"\{[^}]+\}", "", result)
    return result


def get_default_template(channel: str, team_type: str = "default") -> dict:
    """Get a default template for the given channel and team type."""
    if channel == "sms":
        template = DEFAULT_SMS_TEMPLATES.get(team_type, DEFAULT_SMS_TEMPLATES["default"])
        return {"subject": "", "body": template}
    else:
        templates = DEFAULT_EMAIL_TEMPLATES.get(team_type, DEFAULT_EMAIL_TEMPLATES["default"])
        return {"subject": templates["subject"], "body": templates["body"]}


def generate_message(
    team_name: str,
    contact_name: str = "",
    league: str = "",
    location: str = "",
    team_type: str = "",
    channel: str = "email",
    custom_instructions: str = "",
) -> dict:
    """Generate a personalized outreach message.

    Returns dict with 'subject' and 'body'.
    Uses OpenAI if available, otherwise falls back to templates.
    """
    api_key = get_key("OPENAI_API_KEY")

    variables = {
        "team_name": team_name,
        "contact_name": contact_name or "there",
        "league": league,
        "location": location,
    }

    if not api_key:
        template = get_default_template(channel, team_type or "default")
        return {
            "subject": fill_template(template["subject"], variables),
            "body": fill_template(template["body"], variables),
        }

    # AI generation
    client = OpenAI(api_key=api_key)
    user_msg = f"""Generate a {channel} outreach message for:
- Team: {team_name}
- Contact: {contact_name or 'Unknown'}
- League: {league or 'Unknown'}
- Location: {location or 'Unknown'}
- Team type: {team_type or 'Unknown'}
- Channel: {channel}
{"- Special instructions: " + custom_instructions if custom_instructions else ""}

{"Keep SMS under 160 characters." if channel == "sms" else ""}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        content = response.choices[0].message.content.strip()
        result = json.loads(content)
        return {"subject": result.get("subject", ""), "body": result.get("body", "")}
    except Exception:
        # Fallback to templates
        template = get_default_template(channel, team_type or "default")
        return {
            "subject": fill_template(template["subject"], variables),
            "body": fill_template(template["body"], variables),
        }


def generate_variants(
    team_name: str,
    contact_name: str = "",
    team_type: str = "",
    channel: str = "email",
    count: int = 3,
) -> list[dict]:
    """Generate multiple message variants for A/B testing."""
    variants = []
    for i in range(count):
        tone = ["friendly", "professional", "casual"][i % 3]
        msg = generate_message(
            team_name=team_name,
            contact_name=contact_name,
            team_type=team_type,
            channel=channel,
            custom_instructions=f"Use a {tone} tone. Variant {i+1} of {count}.",
        )
        msg["variant"] = f"Variant {i+1} ({tone})"
        variants.append(msg)
    return variants
