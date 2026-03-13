from __future__ import annotations

from app.core.time import utc_now
from app.services.parser import LeadParserService


def test_parse_godaddy_email_with_all_fields() -> None:
    parser = LeadParserService()
    parsed = parser.parse_godaddy_email(
        subject="New Form Submission from Jane Doe",
        body_text=(
            "Name: Jane Doe\n"
            "Phone: (303) 555-0112\n"
            "Email: JANE@EXAMPLE.COM\n"
            "Service: Fire Damage Repair\n"
            "City: Denver\n"
            "Message: Need someone this afternoon."
        ),
        received_at=utc_now(),
        source_ref="msg-1",
    )

    assert parsed.parse_status == "parsed"
    assert parsed.customer_name == "Jane Doe"
    assert parsed.phone == "+13035550112"
    assert parsed.email == "jane@example.com"
    assert parsed.service_type == "Fire Damage Repair"
    assert parsed.city == "Denver"
    assert parsed.message == "Need someone this afternoon."


def test_parse_godaddy_email_with_partial_fields_and_fallbacks() -> None:
    parser = LeadParserService()
    parsed = parser.parse_godaddy_email(
        subject="Website lead from Robert Miles",
        body_text=(
            "Service: Smoke Cleanup\n"
            "Details: Can you call me at 303-555-0199?\n"
            "I can also be reached at rob@example.com."
        ),
        received_at=utc_now(),
        source_ref="msg-2",
    )

    assert parsed.parse_status == "parsed"
    assert parsed.customer_name == "Robert Miles"
    assert parsed.phone == "+13035550199"
    assert parsed.email == "rob@example.com"
    assert parsed.service_type == "Smoke Cleanup"
