from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.seo_audit_run import SEOAuditRun
from app.models.seo_competitor_domain import SEOCompetitorDomain
from app.models.seo_competitor_set import SEOCompetitorSet
from app.models.seo_competitor_snapshot_page import SEOCompetitorSnapshotPage
from app.models.seo_competitor_snapshot_run import SEOCompetitorSnapshotRun
from app.models.seo_site import SEOSite


class SEOCompetitorRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_set(self, competitor_set: SEOCompetitorSet) -> SEOCompetitorSet:
        site = self.session.scalar(
            select(SEOSite.id)
            .where(SEOSite.business_id == competitor_set.business_id)
            .where(SEOSite.id == competitor_set.site_id)
        )
        if site is None:
            raise ValueError("SEO site not found for business")
        self.session.add(competitor_set)
        self.session.flush()
        return competitor_set

    def save_set(self, competitor_set: SEOCompetitorSet) -> SEOCompetitorSet:
        self.session.add(competitor_set)
        self.session.flush()
        return competitor_set

    def get_set_for_business(self, business_id: str, competitor_set_id: str) -> SEOCompetitorSet | None:
        stmt: Select[tuple[SEOCompetitorSet]] = (
            select(SEOCompetitorSet)
            .where(SEOCompetitorSet.business_id == business_id)
            .where(SEOCompetitorSet.id == competitor_set_id)
        )
        return self.session.scalar(stmt)

    def list_sets_for_business_site(self, business_id: str, site_id: str) -> list[SEOCompetitorSet]:
        stmt: Select[tuple[SEOCompetitorSet]] = (
            select(SEOCompetitorSet)
            .where(SEOCompetitorSet.business_id == business_id)
            .where(SEOCompetitorSet.site_id == site_id)
            .order_by(SEOCompetitorSet.created_at.desc(), SEOCompetitorSet.id.desc())
        )
        return list(self.session.scalars(stmt))

    def create_domain(self, competitor_domain: SEOCompetitorDomain) -> SEOCompetitorDomain:
        competitor_set = self.session.scalar(
            select(SEOCompetitorSet).where(SEOCompetitorSet.id == competitor_domain.competitor_set_id)
        )
        if competitor_set is None:
            raise ValueError("Competitor set not found")
        if competitor_set.business_id != competitor_domain.business_id or competitor_set.site_id != competitor_domain.site_id:
            raise ValueError("Competitor domain scope mismatch")

        self.session.add(competitor_domain)
        self.session.flush()
        return competitor_domain

    def save_domain(self, competitor_domain: SEOCompetitorDomain) -> SEOCompetitorDomain:
        self.session.add(competitor_domain)
        self.session.flush()
        return competitor_domain

    def get_domain_for_business(
        self,
        business_id: str,
        competitor_set_id: str,
        domain_id: str,
    ) -> SEOCompetitorDomain | None:
        stmt: Select[tuple[SEOCompetitorDomain]] = (
            select(SEOCompetitorDomain)
            .where(SEOCompetitorDomain.business_id == business_id)
            .where(SEOCompetitorDomain.competitor_set_id == competitor_set_id)
            .where(SEOCompetitorDomain.id == domain_id)
        )
        return self.session.scalar(stmt)

    def list_domains_for_business_set(self, business_id: str, competitor_set_id: str) -> list[SEOCompetitorDomain]:
        stmt: Select[tuple[SEOCompetitorDomain]] = (
            select(SEOCompetitorDomain)
            .where(SEOCompetitorDomain.business_id == business_id)
            .where(SEOCompetitorDomain.competitor_set_id == competitor_set_id)
            .order_by(SEOCompetitorDomain.created_at.asc(), SEOCompetitorDomain.id.asc())
        )
        return list(self.session.scalars(stmt))

    def count_active_domains_for_set(self, business_id: str, competitor_set_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(SEOCompetitorDomain)
            .where(SEOCompetitorDomain.business_id == business_id)
            .where(SEOCompetitorDomain.competitor_set_id == competitor_set_id)
            .where(SEOCompetitorDomain.is_active.is_(True))
        )
        return int(self.session.scalar(stmt) or 0)

    def delete_domain(self, competitor_domain: SEOCompetitorDomain) -> None:
        self.session.delete(competitor_domain)
        self.session.flush()

    def create_snapshot_run(self, snapshot_run: SEOCompetitorSnapshotRun) -> SEOCompetitorSnapshotRun:
        competitor_set = self.session.scalar(
            select(SEOCompetitorSet).where(SEOCompetitorSet.id == snapshot_run.competitor_set_id)
        )
        if competitor_set is None:
            raise ValueError("Competitor set not found")
        if competitor_set.business_id != snapshot_run.business_id or competitor_set.site_id != snapshot_run.site_id:
            raise ValueError("Competitor snapshot run scope mismatch")

        if snapshot_run.client_audit_run_id is not None:
            client_run = self.session.scalar(
                select(SEOAuditRun).where(SEOAuditRun.id == snapshot_run.client_audit_run_id)
            )
            if client_run is None:
                raise ValueError("Client audit run not found")
            if client_run.business_id != snapshot_run.business_id or client_run.site_id != snapshot_run.site_id:
                raise ValueError("Client audit run scope mismatch")

        self.session.add(snapshot_run)
        self.session.flush()
        return snapshot_run

    def save_snapshot_run(self, snapshot_run: SEOCompetitorSnapshotRun) -> SEOCompetitorSnapshotRun:
        self.session.add(snapshot_run)
        self.session.flush()
        return snapshot_run

    def get_snapshot_run_for_business(self, business_id: str, snapshot_run_id: str) -> SEOCompetitorSnapshotRun | None:
        stmt: Select[tuple[SEOCompetitorSnapshotRun]] = (
            select(SEOCompetitorSnapshotRun)
            .where(SEOCompetitorSnapshotRun.business_id == business_id)
            .where(SEOCompetitorSnapshotRun.id == snapshot_run_id)
        )
        return self.session.scalar(stmt)

    def list_snapshot_runs_for_business_set(
        self,
        business_id: str,
        competitor_set_id: str,
    ) -> list[SEOCompetitorSnapshotRun]:
        stmt: Select[tuple[SEOCompetitorSnapshotRun]] = (
            select(SEOCompetitorSnapshotRun)
            .where(SEOCompetitorSnapshotRun.business_id == business_id)
            .where(SEOCompetitorSnapshotRun.competitor_set_id == competitor_set_id)
            .order_by(SEOCompetitorSnapshotRun.created_at.desc(), SEOCompetitorSnapshotRun.id.desc())
        )
        return list(self.session.scalars(stmt))

    def create_snapshot_page(self, snapshot_page: SEOCompetitorSnapshotPage) -> SEOCompetitorSnapshotPage:
        snapshot_run = self.session.scalar(
            select(SEOCompetitorSnapshotRun).where(SEOCompetitorSnapshotRun.id == snapshot_page.snapshot_run_id)
        )
        if snapshot_run is None:
            raise ValueError("Snapshot run not found")
        domain = self.session.scalar(
            select(SEOCompetitorDomain).where(SEOCompetitorDomain.id == snapshot_page.competitor_domain_id)
        )
        if domain is None:
            raise ValueError("Competitor domain not found")

        if (
            snapshot_run.business_id != snapshot_page.business_id
            or snapshot_run.site_id != snapshot_page.site_id
            or snapshot_run.competitor_set_id != snapshot_page.competitor_set_id
        ):
            raise ValueError("Snapshot page run scope mismatch")
        if (
            domain.business_id != snapshot_page.business_id
            or domain.site_id != snapshot_page.site_id
            or domain.competitor_set_id != snapshot_page.competitor_set_id
        ):
            raise ValueError("Snapshot page domain scope mismatch")

        self.session.add(snapshot_page)
        self.session.flush()
        return snapshot_page
