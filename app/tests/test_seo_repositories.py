from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.business import Business
from app.models.seo_audit_finding import SEOAuditFinding
from app.models.seo_audit_page import SEOAuditPage
from app.models.seo_audit_run import SEOAuditRun
from app.models.seo_site import SEOSite
from app.repositories.seo_audit_repository import SEOAuditRepository
from app.repositories.seo_site_repository import SEOSiteRepository


def test_seo_site_repository_business_scoping(db_session, seeded_business) -> None:
    other_business = Business(
        id=str(uuid4()),
        name="Other Tenant",
        notification_phone="+13035550199",
        notification_email="owner@other.example",
        sms_enabled=True,
        email_enabled=True,
        customer_auto_ack_enabled=True,
        contractor_alerts_enabled=True,
        timezone="America/Denver",
    )
    db_session.add(other_business)
    db_session.flush()

    site_repo = SEOSiteRepository(db_session)
    site_a = site_repo.create(
        SEOSite(
            id=str(uuid4()),
            business_id=seeded_business.id,
            display_name="A",
            base_url="https://a.example/",
            normalized_domain="a.example",
            is_active=True,
            is_primary=True,
        )
    )
    site_b = site_repo.create(
        SEOSite(
            id=str(uuid4()),
            business_id=other_business.id,
            display_name="B",
            base_url="https://b.example/",
            normalized_domain="b.example",
            is_active=True,
            is_primary=True,
        )
    )
    db_session.commit()

    assert site_repo.get_for_business(seeded_business.id, site_a.id) is not None
    assert site_repo.get_for_business(seeded_business.id, site_b.id) is None
    assert len(site_repo.list_for_business(seeded_business.id)) == 1


def test_seo_audit_repository_scope_checks(db_session, seeded_business) -> None:
    other_business = Business(
        id=str(uuid4()),
        name="Other Tenant",
        notification_phone="+13035550199",
        notification_email="owner@other.example",
        sms_enabled=True,
        email_enabled=True,
        customer_auto_ack_enabled=True,
        contractor_alerts_enabled=True,
        timezone="America/Denver",
    )
    db_session.add(other_business)
    db_session.flush()

    site_repo = SEOSiteRepository(db_session)
    audit_repo = SEOAuditRepository(db_session)
    site_a = site_repo.create(
        SEOSite(
            id=str(uuid4()),
            business_id=seeded_business.id,
            display_name="A",
            base_url="https://a.example/",
            normalized_domain="a.example",
            is_active=True,
            is_primary=True,
        )
    )
    site_b = site_repo.create(
        SEOSite(
            id=str(uuid4()),
            business_id=other_business.id,
            display_name="B",
            base_url="https://b.example/",
            normalized_domain="b.example",
            is_active=True,
            is_primary=True,
        )
    )
    db_session.flush()

    run = audit_repo.create_run(
        SEOAuditRun(
            id=str(uuid4()),
            business_id=seeded_business.id,
            site_id=site_a.id,
            status="queued",
            max_pages=10,
            max_depth=2,
        )
    )
    db_session.flush()

    page = audit_repo.add_page(
        SEOAuditPage(
            id=str(uuid4()),
            business_id=seeded_business.id,
            site_id=site_a.id,
            audit_run_id=run.id,
            url="https://a.example/",
        )
    )
    audit_repo.add_finding(
        SEOAuditFinding(
            id=str(uuid4()),
            business_id=seeded_business.id,
            site_id=site_a.id,
            audit_run_id=run.id,
            page_id=page.id,
            finding_type="missing_title",
            category="metadata",
            severity="high",
            title="Missing title",
            details="No title tag",
            rule_key="missing_title",
        )
    )
    db_session.commit()

    assert audit_repo.get_run_for_business(seeded_business.id, run.id) is not None
    assert audit_repo.get_run_for_business(other_business.id, run.id) is None
    assert len(audit_repo.list_findings_for_business_run(seeded_business.id, run.id)) == 1
    assert len(audit_repo.list_findings_for_business_run(other_business.id, run.id)) == 0

    with pytest.raises(ValueError):
        audit_repo.add_page(
            SEOAuditPage(
                id=str(uuid4()),
                business_id=other_business.id,
                site_id=site_b.id,
                audit_run_id=run.id,
                url="https://b.example/",
            )
        )
