from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ExtractedPageData:
    title: str | None
    meta_description: str | None
    canonical_url: str | None
    h1_list: list[str]
    h2_list: list[str]
    word_count: int
    image_count: int
    missing_alt_count: int


class SEOExtractor:
    _title_pattern = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
    _meta_description_pattern = re.compile(
        r"""<meta[^>]*name=["']description["'][^>]*content=["'](.*?)["'][^>]*>""",
        re.IGNORECASE | re.DOTALL,
    )
    _canonical_pattern = re.compile(
        r"""<link[^>]*rel=["']canonical["'][^>]*href=["'](.*?)["'][^>]*>""",
        re.IGNORECASE | re.DOTALL,
    )
    _h1_pattern = re.compile(r"<h1[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
    _h2_pattern = re.compile(r"<h2[^>]*>(.*?)</h2>", re.IGNORECASE | re.DOTALL)
    _img_pattern = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
    _img_alt_pattern = re.compile(r"""\balt=["'][^"']*["']""", re.IGNORECASE)
    _tags_pattern = re.compile(r"<[^>]+>")
    _word_pattern = re.compile(r"[A-Za-z0-9]+")

    def extract(self, html: str) -> ExtractedPageData:
        title = self._first_clean(self._title_pattern.findall(html))
        meta_description = self._first_clean(self._meta_description_pattern.findall(html))
        canonical_url = self._first_clean(self._canonical_pattern.findall(html))
        h1_list = self._clean_many(self._h1_pattern.findall(html))
        h2_list = self._clean_many(self._h2_pattern.findall(html))

        images = self._img_pattern.findall(html)
        image_count = len(images)
        missing_alt_count = 0
        for image_tag in images:
            if self._img_alt_pattern.search(image_tag) is None:
                missing_alt_count += 1

        text = self._tags_pattern.sub(" ", html)
        word_count = len(self._word_pattern.findall(text))

        return ExtractedPageData(
            title=title,
            meta_description=meta_description,
            canonical_url=canonical_url,
            h1_list=h1_list,
            h2_list=h2_list,
            word_count=word_count,
            image_count=image_count,
            missing_alt_count=missing_alt_count,
        )

    @staticmethod
    def _first_clean(values: list[str]) -> str | None:
        for value in values:
            cleaned = SEOExtractor._clean_text(value)
            if cleaned:
                return cleaned
        return None

    @staticmethod
    def _clean_many(values: list[str]) -> list[str]:
        cleaned_values: list[str] = []
        for value in values:
            cleaned = SEOExtractor._clean_text(value)
            if cleaned:
                cleaned_values.append(cleaned)
        return cleaned_values

    @staticmethod
    def _clean_text(value: str) -> str:
        without_tags = SEOExtractor._tags_pattern.sub(" ", value)
        collapsed = " ".join(without_tags.split())
        return collapsed.strip()
