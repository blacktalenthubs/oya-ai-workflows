"""AI-powered lead segmentation using OpenAI."""

import json

from openai import OpenAI

from src.config import get_key

SYSTEM_PROMPT = """You are a lead scoring AI for OYA, a soccer/football kit brand.
Given information about a team/club, classify it with the following attributes.

Respond with ONLY valid JSON (no markdown, no explanation):
{
    "team_type": "youth" | "amateur" | "adult" | "academy" | "semi_pro" | "sunday_league",
    "competitive_level": "recreational" | "competitive" | "semi_pro" | "elite",
    "buying_potential": "low" | "medium" | "high",
    "custom_kit_likelihood": 0.0-1.0,
    "reasoning": "brief explanation"
}

Scoring guidelines:
- Academies and competitive youth teams = high buying potential (regular kit orders)
- Sunday league / amateur adult teams = medium potential (occasional orders)
- Single individuals or unrelated orgs = low potential
- Teams with websites/social presence = higher custom kit likelihood
- Teams in organized leagues = higher buying potential
"""


def classify_lead(
    team_name: str,
    league: str = "",
    location: str = "",
    website: str = "",
    additional_context: str = "",
) -> dict:
    """Classify a single lead using OpenAI.

    Returns dict with team_type, competitive_level, buying_potential,
    custom_kit_likelihood, reasoning.
    """
    if not get_key("OPENAI_API_KEY"):
        return _fallback_classification(team_name, league)

    client = OpenAI(api_key=get_key("OPENAI_API_KEY"))

    user_msg = f"""Team: {team_name}
League: {league or 'Unknown'}
Location: {location or 'Unknown'}
Website: {website or 'None'}
Additional: {additional_context or 'None'}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=200,
        )
        content = response.choices[0].message.content.strip()
        return json.loads(content)
    except (json.JSONDecodeError, Exception):
        return _fallback_classification(team_name, league)


def classify_leads_batch(leads: list[dict]) -> list[dict]:
    """Classify multiple leads. Each lead is a dict with at least 'team_name'."""
    results = []
    for lead in leads:
        result = classify_lead(
            team_name=lead.get("team_name", ""),
            league=lead.get("league", ""),
            location=lead.get("location", ""),
            website=lead.get("website", ""),
        )
        results.append(result)
    return results


def _fallback_classification(team_name: str, league: str = "") -> dict:
    """Rule-based fallback when OpenAI is unavailable."""
    name_lower = team_name.lower()
    league_lower = league.lower() if league else ""

    # Team type detection
    team_type = "amateur"
    if any(kw in name_lower for kw in ["academy", "development", "school"]):
        team_type = "academy"
    elif any(kw in name_lower for kw in ["youth", "junior", "u12", "u14", "u16", "u18", "u21", "boys", "girls"]):
        team_type = "youth"
    elif any(kw in name_lower or kw in league_lower for kw in ["sunday", "recreational", "social"]):
        team_type = "sunday_league"
    elif any(kw in name_lower for kw in ["semi-pro", "semipro", "semi pro"]):
        team_type = "semi_pro"

    # Competitive level
    competitive_level = "recreational"
    if team_type in ("academy", "semi_pro"):
        competitive_level = "competitive"
    elif team_type == "youth":
        competitive_level = "competitive"
    elif any(kw in league_lower for kw in ["premier", "championship", "division 1", "elite"]):
        competitive_level = "competitive"

    # Buying potential
    buying_potential = "medium"
    if team_type in ("academy", "semi_pro"):
        buying_potential = "high"
    elif team_type == "sunday_league":
        buying_potential = "medium"

    # Kit likelihood
    kit_likelihood = 0.5
    if team_type == "academy":
        kit_likelihood = 0.8
    elif team_type == "youth":
        kit_likelihood = 0.7
    elif team_type == "sunday_league":
        kit_likelihood = 0.4

    return {
        "team_type": team_type,
        "competitive_level": competitive_level,
        "buying_potential": buying_potential,
        "custom_kit_likelihood": kit_likelihood,
        "reasoning": f"Rule-based classification (OpenAI unavailable). Detected type: {team_type}",
    }
