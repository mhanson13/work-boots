from __future__ import annotations

from dataclasses import dataclass

from app.models.seo_audit_page import SEOAuditPage


@dataclass(frozen=True)
class FindingDraft:
    page_id: str | None
    finding_type: str
    category: str
    severity: str
    title: str
    details: str
    rule_key: str
    suggested_fix: str | None


class SEOFindingRules:
    def __init__(self, *, thin_content_min_words: int = 150) -> None:
        self.thin_content_min_words = thin_content_min_words

    def evaluate(
        self,
        *,
        pages: list[SEOAuditPage],
        broken_internal_links_by_page_id: dict[str, int] | None = None,
    ) -> list[FindingDraft]:
        findings: list[FindingDraft] = []
        broken_map = broken_internal_links_by_page_id or {}

        title_to_pages: dict[str, list[SEOAuditPage]] = {}
        meta_to_pages: dict[str, list[SEOAuditPage]] = {}

        for page in pages:
            if not (page.title or "").strip():
                findings.append(
                    FindingDraft(
                        page_id=page.id,
                        finding_type="missing_title",
                        category="metadata",
                        severity="high",
                        title="Missing title tag",
                        details=f"Page {page.url} has no title tag.",
                        rule_key="missing_title",
                        suggested_fix="Add a unique title tag with service and location intent.",
                    )
                )
            else:
                key = page.title.strip().lower()
                title_to_pages.setdefault(key, []).append(page)

            if not (page.meta_description or "").strip():
                findings.append(
                    FindingDraft(
                        page_id=page.id,
                        finding_type="missing_meta_description",
                        category="metadata",
                        severity="medium",
                        title="Missing meta description",
                        details=f"Page {page.url} has no meta description.",
                        rule_key="missing_meta_description",
                        suggested_fix="Add a clear meta description with service and location context.",
                    )
                )
            else:
                meta_key = page.meta_description.strip().lower()
                meta_to_pages.setdefault(meta_key, []).append(page)

            h1_items = page.h1_json or []
            if len(h1_items) == 0:
                findings.append(
                    FindingDraft(
                        page_id=page.id,
                        finding_type="missing_h1",
                        category="content",
                        severity="medium",
                        title="Missing H1 heading",
                        details=f"Page {page.url} has no H1 heading.",
                        rule_key="missing_h1",
                        suggested_fix="Add one clear H1 that matches page intent.",
                    )
                )

            if not (page.canonical_url or "").strip():
                findings.append(
                    FindingDraft(
                        page_id=page.id,
                        finding_type="missing_canonical",
                        category="technical",
                        severity="low",
                        title="Missing canonical URL",
                        details=f"Page {page.url} has no canonical tag.",
                        rule_key="missing_canonical",
                        suggested_fix="Add a canonical link tag for preferred URL.",
                    )
                )

            if (page.word_count or 0) < self.thin_content_min_words:
                findings.append(
                    FindingDraft(
                        page_id=page.id,
                        finding_type="thin_content",
                        category="content",
                        severity="medium",
                        title="Thin content",
                        details=(
                            f"Page {page.url} has low word count ({page.word_count or 0}). "
                            f"Minimum target is {self.thin_content_min_words}."
                        ),
                        rule_key="thin_content",
                        suggested_fix="Expand page copy with service details, proof, and location context.",
                    )
                )

            broken_count = broken_map.get(page.id, 0)
            if broken_count > 0:
                findings.append(
                    FindingDraft(
                        page_id=page.id,
                        finding_type="broken_internal_links",
                        category="technical",
                        severity="high",
                        title="Broken internal links",
                        details=f"Page {page.url} contains {broken_count} broken internal links.",
                        rule_key="broken_internal_links",
                        suggested_fix="Update or remove broken internal links.",
                    )
                )

        for title_key, grouped_pages in title_to_pages.items():
            if len(grouped_pages) <= 1:
                continue
            for page in grouped_pages:
                findings.append(
                    FindingDraft(
                        page_id=page.id,
                        finding_type="duplicate_title",
                        category="metadata",
                        severity="high",
                        title="Duplicate title tag",
                        details=f"Title '{title_key}' appears on multiple pages in this run.",
                        rule_key="duplicate_title",
                        suggested_fix="Make each title unique per page intent.",
                    )
                )

        for meta_key, grouped_pages in meta_to_pages.items():
            if len(grouped_pages) <= 1:
                continue
            for page in grouped_pages:
                findings.append(
                    FindingDraft(
                        page_id=page.id,
                        finding_type="duplicate_meta_description",
                        category="metadata",
                        severity="medium",
                        title="Duplicate meta description",
                        details=f"Meta description '{meta_key}' appears on multiple pages in this run.",
                        rule_key="duplicate_meta_description",
                        suggested_fix="Write unique meta descriptions per page.",
                    )
                )

        return findings
