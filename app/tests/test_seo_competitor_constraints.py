from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.business import Business
from app.models.seo_competitor_domain import SEOCompetitorDomain
from app.models.seo_competitor_comparison_finding import SEOCompetitorComparisonFinding
from app.models.seo_competitor_comparison_run import SEOCompetitorComparisonRun
from app.models.seo_competitor_set import SEOCompetitorSet
from app.models.seo_competitor_snapshot_page import SEOCompetitorSnapshotPage
from app.models.seo_competitor_snapshot_run import SEOCompetitorSnapshotRun
from app.models.seo_site import SEOSite
from app.repositories.seo_competitor_repository import SEOCompetitorRepository


def _seed_other_business(db_session) -> Business:
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
    return other_business


def _seed_site(db_session, *, business_id: str, domain: str) -> SEOSite:
    site = SEOSite(
        id=str(uuid4()),
        business_id=business_id,
        display_name=f"Site {domain}",
        base_url=f"https://{domain}/",
        normalized_domain=domain,
        is_active=True,
        is_primary=False,
    )
    db_session.add(site)
    db_session.flush()
    return site


def test_competitor_set_name_unique_per_business_site(db_session, seeded_business) -> None:
    site = _seed_site(db_session, business_id=seeded_business.id, domain="client.example")

    db_session.add(
        SEOCompetitorSet(
            id=str(uuid4()),
            business_id=seeded_business.id,
            site_id=site.id,
            name="Denver Competitors",
            is_active=True,
        )
    )
    db_session.flush()

    db_session.add(
        SEOCompetitorSet(
            id=str(uuid4()),
            business_id=seeded_business.id,
            site_id=site.id,
            name="Denver Competitors",
            is_active=True,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_competitor_domain_unique_within_set(db_session, seeded_business) -> None:
    site = _seed_site(db_session, business_id=seeded_business.id, domain="client.example")
    competitor_set = SEOCompetitorSet(
        id=str(uuid4()),
        business_id=seeded_business.id,
        site_id=site.id,
        name="Set A",
        is_active=True,
    )
    db_session.add(competitor_set)
    db_session.flush()

    db_session.add(
        SEOCompetitorDomain(
            id=str(uuid4()),
            business_id=seeded_business.id,
            site_id=site.id,
            competitor_set_id=competitor_set.id,
            domain="competitor.com",
            base_url="https://competitor.com/",
            source="manual",
            is_active=True,
        )
    )
    db_session.flush()

    db_session.add(
        SEOCompetitorDomain(
            id=str(uuid4()),
            business_id=seeded_business.id,
            site_id=site.id,
            competitor_set_id=competitor_set.id,
            domain="competitor.com",
            base_url="https://competitor.com/services",
            source="manual",
            is_active=True,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_competitor_domain_scope_mismatch_rejected_in_repository(db_session, seeded_business) -> None:
    other_business = _seed_other_business(db_session)
    site_a = _seed_site(db_session, business_id=seeded_business.id, domain="client-a.example")
    site_b = _seed_site(db_session, business_id=other_business.id, domain="client-b.example")

    competitor_set = SEOCompetitorSet(
        id=str(uuid4()),
        business_id=seeded_business.id,
        site_id=site_a.id,
        name="Set A",
        is_active=True,
    )
    db_session.add(competitor_set)
    db_session.flush()

    repo = SEOCompetitorRepository(db_session)
    with pytest.raises(ValueError, match="scope mismatch"):
        repo.create_domain(
            SEOCompetitorDomain(
                id=str(uuid4()),
                business_id=other_business.id,
                site_id=site_b.id,
                competitor_set_id=competitor_set.id,
                domain="mismatch.example",
                base_url="https://mismatch.example/",
                source="manual",
                is_active=True,
            )
        )


def test_snapshot_page_scope_mismatch_rejected_in_repository(db_session, seeded_business) -> None:
    site = _seed_site(db_session, business_id=seeded_business.id, domain="client.example")
    set_a = SEOCompetitorSet(
        id=str(uuid4()),
        business_id=seeded_business.id,
        site_id=site.id,
        name="Set A",
        is_active=True,
    )
    set_b = SEOCompetitorSet(
        id=str(uuid4()),
        business_id=seeded_business.id,
        site_id=site.id,
        name="Set B",
        is_active=True,
    )
    db_session.add_all([set_a, set_b])
    db_session.flush()

    domain_a = SEOCompetitorDomain(
        id=str(uuid4()),
        business_id=seeded_business.id,
        site_id=site.id,
        competitor_set_id=set_a.id,
        domain="a.example",
        base_url="https://a.example/",
        source="manual",
        is_active=True,
    )
    domain_b = SEOCompetitorDomain(
        id=str(uuid4()),
        business_id=seeded_business.id,
        site_id=site.id,
        competitor_set_id=set_b.id,
        domain="b.example",
        base_url="https://b.example/",
        source="manual",
        is_active=True,
    )
    db_session.add_all([domain_a, domain_b])
    db_session.flush()

    run = SEOCompetitorSnapshotRun(
        id=str(uuid4()),
        business_id=seeded_business.id,
        site_id=site.id,
        competitor_set_id=set_a.id,
        status="queued",
        max_domains=5,
        max_pages_per_domain=3,
        max_depth=1,
        same_domain_only=True,
    )
    db_session.add(run)
    db_session.flush()

    repo = SEOCompetitorRepository(db_session)
    with pytest.raises(ValueError, match="domain scope mismatch"):
        repo.create_snapshot_page(
            SEOCompetitorSnapshotPage(
                id=str(uuid4()),
                business_id=seeded_business.id,
                site_id=site.id,
                competitor_set_id=set_a.id,
                snapshot_run_id=run.id,
                competitor_domain_id=domain_b.id,
                url="https://b.example/",
            )
        )


def test_comparison_finding_scope_mismatch_rejected_in_repository(db_session, seeded_business) -> None:
    site = _seed_site(db_session, business_id=seeded_business.id, domain="client.example")
    competitor_set = SEOCompetitorSet(
        id=str(uuid4()),
        business_id=seeded_business.id,
        site_id=site.id,
        name="Set A",
        is_active=True,
    )
    db_session.add(competitor_set)
    db_session.flush()

    snapshot_run = SEOCompetitorSnapshotRun(
        id=str(uuid4()),
        business_id=seeded_business.id,
        site_id=site.id,
        competitor_set_id=competitor_set.id,
        status="completed",
        max_domains=5,
        max_pages_per_domain=5,
        max_depth=1,
        same_domain_only=True,
    )
    db_session.add(snapshot_run)
    db_session.flush()

    comparison_run = SEOCompetitorComparisonRun(
        id=str(uuid4()),
        business_id=seeded_business.id,
        site_id=site.id,
        competitor_set_id=competitor_set.id,
        snapshot_run_id=snapshot_run.id,
        status="completed",
    )
    db_session.add(comparison_run)
    db_session.flush()

    other_business = _seed_other_business(db_session)
    repo = SEOCompetitorRepository(db_session)
    with pytest.raises(ValueError, match="scope mismatch"):
        repo.add_comparison_finding(
            SEOCompetitorComparisonFinding(
                id=str(uuid4()),
                business_id=other_business.id,
                site_id=site.id,
                competitor_set_id=competitor_set.id,
                comparison_run_id=comparison_run.id,
                finding_type="page_count_gap",
                category="STRUCTURE",
                severity="WARNING",
                title="Page coverage gap",
                details="details",
                rule_key="comparison_page_count",
            )
        )
