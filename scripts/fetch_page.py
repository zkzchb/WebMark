#!/usr/bin/env python3
"""Optional HTTP fallback for WebMark.

Use only when the configured WorkBuddy fetch tools fail and
settings.fetch.allow_script_fallback is true.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import datetime
from typing import Any
from urllib.parse import urlsplit


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    value = unicodedata.normalize("NFKC", text)
    value = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    value = re.sub(r"[ \t]{2,}", " ", value)
    return value.strip()


def fetch_with_trafilatura(url: str) -> dict[str, Any] | None:
    try:
        import trafilatura
    except ImportError:
        return None

    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return None
        content = trafilatura.extract(
            downloaded,
            url=url,
            output_format="markdown",
            include_comments=False,
            include_links=True,
            include_images=True,
            include_tables=True,
            favor_precision=True,
            no_fallback=False,
        )
        if not content:
            return None
        metadata = trafilatura.extract_metadata(downloaded, default_url=url)
        return _result(
            url=url,
            title=getattr(metadata, "title", None) or url,
            author=getattr(metadata, "author", None),
            published=getattr(metadata, "date", None),
            content=content,
            method="trafilatura",
        )
    except Exception as exc:  # fallback script must return structured failure
        return {"url": url, "method": "trafilatura", "error": str(exc)}


def fetch_static(url: str, timeout: int = 30) -> dict[str, Any] | None:
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return None

    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; WebMark/0.2)",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
        )
        response.raise_for_status()
        if not response.encoding or response.encoding.lower() in {"iso-8859-1", "latin-1"}:
            response.encoding = response.apparent_encoding or "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        title = _title(soup) or response.url
        author = _meta(soup, "author")
        published = _meta(soup, "article:published_time") or _meta(soup, "datePublished")

        for tag in soup.find_all(["script", "style", "nav", "footer", "aside", "iframe", "noscript"]):
            tag.decompose()
        noise = re.compile(
            r"(comment|sidebar|footer|header|nav|advert|banner|recommend|related|share|follow|subscribe|copyright|icp)",
            re.I,
        )
        for element in soup.find_all(attrs={"class": True}):
            if noise.search(" ".join(element.get("class", []))):
                element.decompose()

        paragraphs = [
            node.get_text(" ", strip=True)
            for node in soup.find_all("p")
            if len(node.get_text(" ", strip=True)) >= 20
        ]
        content = "\n\n".join(paragraphs)
        if not content:
            content = soup.get_text("\n", strip=True)[:5000]
        return _result(
            url=response.url,
            title=title,
            author=author,
            published=published,
            content=content,
            method="static",
        )
    except Exception as exc:
        return {"url": url, "method": "static", "error": str(exc)}


def extract_page(url: str) -> dict[str, Any]:
    for fetcher in (fetch_with_trafilatura, fetch_static):
        result = fetcher(url)
        if result and not result.get("error") and result.get("content"):
            return result
    return {
        "url": url,
        "title": url,
        "author": None,
        "published": None,
        "content": None,
        "method": "failed",
        "error": "all_methods_failed",
        "paragraph_count": 0,
        "character_count": 0,
    }


def _result(
    *,
    url: str,
    title: str,
    author: str | None,
    published: str | None,
    content: str,
    method: str,
) -> dict[str, Any]:
    clean = normalize_text(content)
    return {
        "url": url,
        "title": normalize_text(title),
        "author": normalize_text(author),
        "published": normalize_text(published),
        "content": clean,
        "method": method,
        "paragraph_count": len([part for part in clean.split("\n\n") if part.strip()]),
        "character_count": len(clean),
        "collected_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def _title(soup) -> str | None:
    tag = soup.find("meta", property="og:title")
    if tag and tag.get("content"):
        return tag["content"].strip()
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    heading = soup.find("h1")
    return heading.get_text(" ", strip=True) if heading else None


def _meta(soup, name: str) -> str | None:
    for attrs in ({"property": name}, {"name": name}, {"itemprop": name}):
        tag = soup.find(attrs=attrs)
        if tag:
            value = tag.get("content") or tag.get_text(" ", strip=True)
            if value:
                return value.strip()
    return None


def main() -> int:
    if len(sys.argv) != 2:
        print(json.dumps({"status": "error", "error": "usage: fetch_page.py <URL>"}))
        return 2
    url = sys.argv[1].strip()
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        print(json.dumps({"status": "error", "error": "URL must use http or https"}))
        return 2
    print(json.dumps(extract_page(url), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
