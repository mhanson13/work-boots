from __future__ import annotations

from dataclasses import dataclass
import logging
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models.seo_audit_finding import SEOAuditFinding
from app.models.seo_audit_page import SEOAuditPage
from app.models.seo_audit_run import SEOAuditRun, SEOAuditRunStatus
from app.repositories.business_repository import BusinessRepository
from app.repositories.seo_audit_repository import SEOAuditRepository
from app.repositories.seo_site_repository import SEOSiteRepository
from app.schemas.seo_audit import SEOAuditRunCreateRequest
from app.services.seo_crawler import CrawlPageResult, SEOCrawler, SEOCrawlerValidationError
from app.services.seo_extractor import SEOExtractor
from app.services.seo_finding_rules import SEOFindingRules


logger = logging.getLogger(__name__)


class SEOAuditNotFoundError(ValueError):
    pass


class SEOAuditValidationError(ValueError):
    pass


@dataclass(frozen=True)
class AuditRunResult:
    run: SEOAuditRun
    pages: list[SEOAuditPage]
    findings: list[SEOAuditFinding]


class SEOAuditService:
    def __init__(
        self,
        *,
        session: Session,
        business_repository: BusinessRepository,
        seo_site_repository: SEOSiteRepository,
        seo_audit_repository: SEOAuditRepository,
        crawler: SEOCrawler,
        extractor: SEOExtractor,
        finding_rules: SEOFindingRules,
    ) -> None:
        self.session = session
        self.business_repository = business_repository
        self.seo_site_repository = seo_site_repository
        self.seo_audit_repository = seo_audit_repository
        self.crawler = crawler
        self.extractor = extractor
        self.finding_rules = finding_rules

    def run_audit(
        self,
        *,
        business_id: str,
        site_id: str,
        payload: SEOAuditRunCreateRequest,
        created_by_principal_id: str | None,
    ) -> AuditRunResult:
        self._require_business(business_id)
        site = self.seo_site_repository.get_for_business(business_id, site_id)
        if site is None:
            raise SEOAuditNotFoundError("SEO site not found")

        run = SEOAuditRun(
            id=str(uuid4()),
            business_id=business_id,
            site_id=site_id,
            status=SEOAuditRunStatus.QUEUED.value,
            max_pages=payload.max_pages,
            max_depth=payload.max_depth,
            created_by_principal_id=created_by_principal_id,
        )
        self.seo_audit_repository.create_run(run)
        self.session.commit()

        run.status = SEOAuditRunStatus.RUNNING.value
        run.started_at = utc_now()
        self.seo_audit_repository.save_run(run)
        self.session.commit()
        logger.info(
            "SEO audit run started business_id=%s site_id=%s audit_run_id=%s status=%s",
            business_id,
            site_id,
            run.id,
            run.status,
        )

        try:
            crawl_pages = self.crawler.crawl(
                base_url=site.base_url,
                max_pages=payload.max_pages,
                max_depth=payload.max_depth,
                same_domain_only=True,
            )
            persisted_pages, broken_links_by_page_id = self._persist_pages(
                run=run,
                crawl_pages=crawl_pages,
            )
            persisted_findings = self._persist_findings(
                run=run,
                pages=persisted_pages,
                broken_links_by_page_id=broken_links_by_page_id,
            )

            run.pages_discovered = len(crawl_pages)
            run.pages_crawled = len(persisted_pages)
            run.status = SEOAuditRunStatus.COMPLETED.value
            run.completed_at = utc_now()
            run.error_summary = None
            self.seo_audit_repository.save_run(run)
            self.session.commit()
            logger.info(
                "SEO audit run completed business_id=%s site_id=%s audit_run_id=%s status=%s pages_discovered=%s pages_crawled=%s findings=%s",
                business_id,
                site_id,
                run.id,
                run.status,
                run.pages_discovered,
                run.pages_crawled,
                len(persisted_findings),
            )
            return AuditRunResult(run=run, pages=persisted_pages, findings=persisted_findings)
        except SEOCrawlerValidationError as exc:
            return self._fail_run(run=run, reason=str(exc))
        except Exception as exc:  # noqa: BLE001
            return self._fail_run(run=run, reason=str(exc))

    def get_run(self, *, business_id: str, run_id: str) -> SEOAuditRun:
        self._require_business(business_id)
        run = self.seo_audit_repository.get_run_for_business(business_id, run_id)
        if run is None:
            raise SEOAuditNotFoundError("SEO audit run not found")
        return run

    def list_runs_for_site(self, *, business_id: str, site_id: str) -> list[SEOAuditRun]:
        self._require_business(business_id)
        site = self.seo_site_repository.get_for_business(business_id, site_id)
        if site is None:
            raise SEOAuditNotFoundError("SEO site not found")
        return self.seo_audit_repository.list_runs_for_business_site(business_id, site_id)

    def list_findings_for_run(self, *, business_id: str, run_id: str) -> list[SEOAuditFinding]:
        self._require_business(business_id)
        run = self.seo_audit_repository.get_run_for_business(business_id, run_id)
        if run is None:
            raise SEOAuditNotFoundError("SEO audit run not found")
        return self.seo_audit_repository.list_findings_for_business_run(business_id, run_id)

    def _persist_pages(
        self,
        *,
        run: SEOAuditRun,
        crawl_pages: list[CrawlPageResult],
    ) -> tuple[list[SEOAuditPage], dict[str, int]]:
        status_by_url: dict[str, int] = {page.final_url: page.status_code for page in crawl_pages}
        persisted_pages: list[SEOAuditPage] = []
        broken_links_by_page_id: dict[str, int] = {}

        for crawl_page in crawl_pages:
            extracted = (
                self.extractor.extract(crawl_page.body_text) if crawl_page.body_text is not None else None
            )
            page = SEOAuditPage(
                id=str(uuid4()),
                business_id=run.business_id,
                site_id=run.site_id,
                audit_run_id=run.id,
                url=crawl_page.final_url,
                status_code=crawl_page.status_code,
                title=extracted.title if extracted else None,
                meta_description=extracted.meta_description if extracted else None,
                canonical_url=extracted.canonical_url if extracted else None,
                h1_json=extracted.h1_list if extracted else [],
                h2_json=extracted.h2_list if extracted else [],
                word_count=extracted.word_count if extracted else 0,
                internal_link_count=len(crawl_page.outgoing_internal_links),
                image_count=extracted.image_count if extracted else 0,
                missing_alt_count=extracted.missing_alt_count if extracted else 0,
                fetched_at=utc_now(),
            )
            self.seo_audit_repository.add_page(page)
            persisted_pages.append(page)

            broken = 0
            for target in crawl_page.outgoing_internal_links:
                if status_by_url.get(target, 200) >= 400:
                    broken += 1
            broken_links_by_page_id[page.id] = broken

        self.session.flush()
        return persisted_pages, broken_links_by_page_id

    def _persist_findings(
        self,
        *,
        run: SEOAuditRun,
        pages: list[SEOAuditPage],
        broken_links_by_page_id: dict[str, int],
    ) -> list[SEOAuditFinding]:
        finding_drafts = self.finding_rules.evaluate(
            pages=pages,
            broken_internal_links_by_page_id=broken_links_by_page_id,
        )
        persisted: list[SEOAuditFinding] = []
        for finding in finding_drafts:
            item = SEOAuditFinding(
                id=str(uuid4()),
                business_id=run.business_id,
                site_id=run.site_id,
                audit_run_id=run.id,
                page_id=finding.page_id,
                finding_type=finding.finding_type,
                category=finding.category,
                severity=finding.severity,
                title=finding.title,
                details=finding.details,
                rule_key=finding.rule_key,
                suggested_fix=finding.suggested_fix,
            )
            self.seo_audit_repository.add_finding(item)
            persisted.append(item)
        self.session.flush()
        return persisted

    def _require_business(self, business_id: str) -> None:
        business = self.business_repository.get(business_id)
        if business is None:
            raise SEOAuditNotFoundError("Business not found")

    def _fail_run(self, *, run: SEOAuditRun, reason: str) -> AuditRunResult:
        logger.warning(
            "SEO audit run failed business_id=%s site_id=%s audit_run_id=%s status=failed reason=%s",
            run.business_id,
            run.site_id,
            run.id,
            reason,
        )
        run.status = SEOAuditRunStatus.FAILED.value
        run.completed_at = utc_now()
        run.error_summary = reason[:1000]
        self.seo_audit_repository.save_run(run)
        self.session.commit()
        return AuditRunResult(run=run, pages=[], findings=[])
