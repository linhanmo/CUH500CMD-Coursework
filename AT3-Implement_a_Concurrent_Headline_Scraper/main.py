import sys
import os
import concurrent.futures
import csv
import json
import random
import threading
import time
import timeit
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin
import newspaper
from newspaper import article as newspaper_article
import requests
from bs4 import BeautifulSoup

# Tunables
TOTAL_TIMEOUT = 450.0
NEWSPAPER_TIMEOUT = 300.0
BS4_TIMEOUT = 150.0


# Rate limiter
class DomainRateLimiter:
    def __init__(self, min_interval=1.0):
        self.min_interval = min_interval
        self._locks = defaultdict(threading.Lock)
        self._last = {}
        self._meta_lock = threading.Lock()

    def acquire(self, url):
        domain = urlparse(url).netloc
        with self._meta_lock:
            lock = self._locks[domain]
        with lock:
            now = time.monotonic()
            last = self._last.get(domain, 0.0)
            wait = self.min_interval - (now - last)
            if wait > 0:
                time.sleep(wait)
            self._last[domain] = time.monotonic()


# Retry with exponential backoff & jitter
def retry_with_backoff(fn, max_retries=2, base_delay=1.0, max_delay=8.0):
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return fn(), attempt + 1, None
        except Exception as exc:
            last_exc = exc
            if attempt == max_retries:
                break
            delay = min(base_delay * (2**attempt), max_delay)
            delay += random.uniform(0, 0.5)
            time.sleep(delay)
    return None, max_retries + 1, last_exc


# Timeout wrapper
class _UrlTimeout(Exception):
    pass


def _run_with_timeout(fn, timeout):
    result_box = {}

    def runner():
        try:
            result_box["value"] = fn()
        except Exception as exc:
            result_box["error"] = exc

    t = threading.Thread(target=runner, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        raise _UrlTimeout(f"timed out after {timeout}s")
    if "error" in result_box:
        raise result_box["error"]
    return result_box.get("value")


# URL path segments that are not articles
_NEWSPAPER_NON_ARTICLE_URL_HINTS = (
    "/video/",
    "/videos/",
    "/shows/",
    "/programmes/",
    "/gallery/",
    "/photos/",
    "/tag/",
    "/category/",
)

# Generic titles that newspaper sometimes assigns to hub pages
_NEWSPAPER_REJECT_TITLES = {
    "untitled article",
    "home",
    "news",
    "videos",
    "shows",
    "latest news",
    "watch live",
    "live tv",
}


# Scraper backends
def _fetch_with_newspaper(url):
    try:
        paper = newspaper.build(url, memoize_articles=False)
    except Exception:
        return []

    articles = list(getattr(paper, "articles", []) or [])
    titles = []

    for art in articles:
        if len(titles) >= 5:
            break

        # Move all attribute access inside the try block
        try:
            art.download()
            art.parse()
            title = (art.title or "").strip()
            body = (art.text or "").strip()
            url_ = (art.url or "").lower()
        except newspaper_article.ArticleException:
            continue
        except Exception:
            continue

        if not title or len(title) < 15:
            continue
        if len(body) < 100:
            continue
        if any(seg in url_ for seg in _NEWSPAPER_NON_ARTICLE_URL_HINTS):
            continue
        if title.lower() in _NEWSPAPER_REJECT_TITLES:
            continue

        titles.append(title)

    return titles


# Structural containers and non-content tags to strip before scanning anchors
_BS4_STRIP_TAGS = [
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "script",
    "style",
    "noscript",
    "button",
    "select",
    "option",
]

# Substrings that almost always indicate navigation or chrome
_BS4_NAV_HINTS = (
    "nav",
    "menu",
    "sidebar",
    "footer",
    "header",
    "topbar",
    "breadcrumb",
    "social",
    "share",
    "comment",
    "cookie",
    "banner",
    "promo",
    "subscribe",
    "newsletter",
)

# URL path segments that indicate non-article pages
_BS4_NON_ARTICLE_URL_HINTS = (
    "/tag/",
    "/tags/",
    "/category/",
    "/categories/",
    "/author/",
    "/authors/",
    "/about",
    "/contact",
    "/privacy",
    "/terms",
    "/login",
    "/signin",
    "/signup",
    "/subscribe",
    "/newsletter",
    "/rss",
    "/feed",
    "/video/",
    "/videos/",
    "/photo/",
    "/photos/",
    "/gallery/",
    "/search",
    "/index",
    "/home",
)

# Titles that are clearly not headlines
_BS4_REJECT_TITLES = {
    "home",
    "menu",
    "more",
    "next",
    "previous",
    "back",
    "top",
    "skip to content",
    "skip to main content",
    "skip to navigation",
    "login",
    "sign in",
    "sign up",
    "subscribe",
    "newsletter",
    "news headlines",
    "international edition",
    "print subscriptions",
}

# Attribution prefixes that are not headlines
_BS4_REJECT_PREFIXES = (
    "animation by",
    "illustration by",
    "photo by",
    "image by",
    "video by",
    "graphic by",
    "credit:",
    "getty images",
)

# Site-chrome phrases that are not headlines
_BS4_REJECT_SUBSTRINGS = (
    "fehler melden",
    "contact us",
    "report an error",
    "cookie",
    "privacy policy",
    "terms of service",
    "subscribe to",
    "sign up for",
)

_ARTICLE_PATH_MIN_LEN = 30  # most news article paths are longer than this
_ARTICLE_PATH_EXTENSIONS = (".html", ".htm", ".shtml", ".amp")

# Path segments that never indicate an article
_HREF_REJECT_SEGMENTS = (
    "/tag/",
    "/tags/",
    "/category/",
    "/categories/",
    "/author/",
    "/authors/",
    "/about",
    "/contact",
    "/privacy",
    "/terms",
    "/login",
    "/signin",
    "/signup",
    "/subscribe",
    "/newsletter",
    "/rss",
    "/feed",
    "/video/",
    "/videos/",
    "/photo/",
    "/photos/",
    "/gallery/",
    "/search",
    "/index",
    "/home",
    "/shows/",
    "/programmes/",
    "/live",
)


def _href_looks_like_article(href, base_url):
    if not href:
        return False

    stripped = href.strip().lower()
    if stripped.startswith(("#", "javascript:", "mailto:", "tel:")):
        return False

    # Resolve relative URLs against the page URL
    try:
        absolute = urljoin(base_url, href)
    except Exception:
        return False

    parsed = urlparse(absolute)

    # Must stay on the same site
    base_host = urlparse(base_url).netloc.lower()
    if parsed.netloc and parsed.netloc.lower() != base_host:
        return False

    path = parsed.path or "/"

    # Reject known non-article segments
    path_lower = path.lower()
    if any(seg in path_lower for seg in _HREF_REJECT_SEGMENTS):
        return False

    # Article-like signals
    has_digits = any(ch.isdigit() for ch in path)
    has_ext = path_lower.endswith(_ARTICLE_PATH_EXTENSIONS)
    long_path = len(path) > _ARTICLE_PATH_MIN_LEN

    return has_digits or has_ext or long_path


# BeautifulSoup fallback scraper
def _fetch_with_bs4(url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; HeadlineScraper/1.0)"}
    resp = requests.get(url, timeout=BS4_TIMEOUT, headers=headers)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding
    soup = BeautifulSoup(resp.text, "html.parser")

    # Collect structural or chrome tags
    to_remove = []
    for name in _BS4_STRIP_TAGS:
        to_remove.extend(soup.find_all(name))

    for tag in soup.find_all(True):
        try:
            classes = " ".join(tag.get("class") or [])
            ident = tag.get("id") or ""
        except AttributeError:
            continue
        attrs = f"{classes} {ident}".lower()
        if any(h in attrs for h in _BS4_NAV_HINTS):
            to_remove.append(tag)

    for tag in to_remove:
        try:
            tag.decompose()
        except Exception:
            pass

    # Scan anchors with href-structure filter
    titles, seen = [], set()
    for a in soup.find_all("a", href=True):
        try:
            href = (a.get("href") or "").strip()
            text = a.get_text(" ", strip=True)
        except AttributeError:
            continue

        # Skip if the href does not look like an article URL
        if not _href_looks_like_article(href, url):
            continue

        # Text quality checks
        if len(text) < 20 or len(text) > 200:
            continue
        lower = text.lower()
        if lower in _BS4_REJECT_TITLES:
            continue
        if lower.startswith(_BS4_REJECT_PREFIXES):
            continue
        if any(s in lower for s in _BS4_REJECT_SUBSTRINGS):
            continue
        if " " not in text and len(text) < 30:
            continue

        if text in seen:
            continue
        seen.add(text)
        titles.append(text)
        if len(titles) >= 5:
            break

    return titles


# Core URL scraper
def scrape_one(url, timeout=TOTAL_TIMEOUT, max_retries=2, rate_limiter=None):
    started = time.monotonic()
    outcome = {
        "url": url,
        "headlines": [],
        "count": 0,
        "shortage": False,
        "error": None,
        "elapsed": 0.0,
        "fetch_method": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    def fetch_and_parse():
        if rate_limiter is not None:
            rate_limiter.acquire(url)

        # Newspaper
        try:
            result = _run_with_timeout(
                lambda: _fetch_with_newspaper(url), NEWSPAPER_TIMEOUT
            )
            if result:
                outcome["fetch_method"] = "newspaper"
                return result
        except _UrlTimeout:
            outcome["fetch_method"] = "newspaper_timeout"
        except Exception:
            outcome["fetch_method"] = "newspaper_error"

        # Fallback to fast BS4 fetch
        result = _run_with_timeout(lambda: _fetch_with_bs4(url), BS4_TIMEOUT)
        outcome["fetch_method"] = (
            outcome["fetch_method"] + "->bs4" if outcome["fetch_method"] else "bs4"
        )
        return result

    try:
        titles, attempts, last_exc = retry_with_backoff(
            lambda: _run_with_timeout(fetch_and_parse, timeout),
            max_retries=max_retries,
        )
    except _UrlTimeout as exc:
        outcome["error"] = f"timeout: {exc}"
        outcome["elapsed"] = round(time.monotonic() - started, 3)
        return outcome
    except Exception as exc:
        outcome["error"] = f"{type(exc).__name__}: {exc}"
        outcome["elapsed"] = round(time.monotonic() - started, 3)
        return outcome

    if titles is None:
        outcome["error"] = f"{type(last_exc).__name__}: {last_exc}"
        outcome["elapsed"] = round(time.monotonic() - started, 3)
        return outcome

    if not titles:
        titles = ["Untitled Article"]

    outcome["headlines"] = titles
    outcome["count"] = len(titles)
    outcome["shortage"] = len(titles) < 5
    outcome["elapsed"] = round(time.monotonic() - started, 3)
    return outcome


# Scraper orchestrator
class HeadlineScraper:
    DEFAULT_URLS = [
        # Mainland-China accessible sources
        "https://news.sina.com.cn/",
        "https://news.163.com/",
        # International sources
        "http://www.foxnews.com/",
        "http://www.cnn.com/",
        "http://www.derspiegel.de/",
        "http://www.bbc.co.uk/",
        "https://theguardian.com",
    ]

    def __init__(
        self,
        urls=None,
        timeout=TOTAL_TIMEOUT,
        max_workers=8,
        max_retries=2,
        rate_limit_interval=1.0,
    ):
        self.urls = list(urls) if urls else list(self.DEFAULT_URLS)
        self.timeout = timeout
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.rate_limiter = DomainRateLimiter(rate_limit_interval)

    def scrape_serial(self):
        return [
            scrape_one(
                u,
                timeout=self.timeout,
                max_retries=self.max_retries,
                rate_limiter=self.rate_limiter,
            )
            for u in self.urls
        ]

    def scrape_thread(self):
        # Using ThreadPoolExecutor
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            futures = {
                ex.submit(
                    scrape_one, u, self.timeout, self.max_retries, self.rate_limiter
                ): u
                for u in self.urls
            }
            for fut in concurrent.futures.as_completed(futures):
                url = futures[fut]
                try:
                    results.append(fut.result())
                except Exception as exc:
                    results.append(self._error_result(url, exc))
        results.sort(key=lambda r: self.urls.index(r["url"]))
        return results

    @staticmethod
    def _error_result(url, exc):
        return {
            "url": url,
            "headlines": [],
            "count": 0,
            "shortage": False,
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed": 0.0,
            "fetch_method": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Statistics
def compute_stats(results, wall_time=None):
    total = len(results)
    ok = sum(1 for r in results if r["error"] is None)
    timeouts = sum(1 for r in results if r["error"] and "timeout" in r["error"].lower())
    shortages = sum(1 for r in results if r["shortage"])
    total_headlines = sum(r["count"] for r in results)
    elapsed_values = [r["elapsed"] for r in results if r["elapsed"] > 0]

    methods = defaultdict(int)
    for r in results:
        methods[r.get("fetch_method") or "unknown"] += 1

    return {
        "total_urls": total,
        "successful": ok,
        "failed": total - ok,
        "timeouts": timeouts,
        "shortages": shortages,
        "total_headlines": total_headlines,
        "avg_headlines_per_url": round(total_headlines / total, 2) if total else 0.0,
        "min_url_time": round(min(elapsed_values), 3) if elapsed_values else 0.0,
        "max_url_time": round(max(elapsed_values), 3) if elapsed_values else 0.0,
        "avg_url_time": (
            round(sum(elapsed_values) / len(elapsed_values), 3)
            if elapsed_values
            else 0.0
        ),
        "wall_time": round(wall_time, 3) if wall_time is not None else None,
        "throughput": (
            round(total / wall_time, 3) if wall_time and wall_time > 0 else None
        ),
        "fetch_methods": dict(methods),
    }


def print_results(label, results, stats):
    print(f"{label}")
    for r in results:
        status = "OK" if r["error"] is None else f"ERR({r['error']})"
        short = " [shortage]" if r["shortage"] else ""
        method = r.get("fetch_method") or "-"
        print(
            f"\n{r['url']}  ({r['elapsed']} s, count={r['count']}, "
            f"via {method}, {status}){short}"
        )
        for h in r["headlines"]:
            print(f"   - {h}")
    print(f"  Summary statistics — {label}")
    for k, v in stats.items():
        print(f"  {k:<24}: {v}")
    print()


# Benchmark: serial vs thread
def _run_serial_once():
    HeadlineScraper(max_workers=1).scrape_serial()


def _run_thread_once():
    HeadlineScraper(max_workers=8).scrape_thread()


def benchmark(iterations=10):
    print(f"Benchmark: {iterations} iterations per mode")
    setup = "from __main__ import _run_serial_once, _run_thread_once"
    serial = (
        timeit.timeit("_run_serial_once()", setup=setup, number=iterations) / iterations
    )
    thread = (
        timeit.timeit("_run_thread_once()", setup=setup, number=iterations) / iterations
    )
    print(f"  Serial          : {serial:.3f} s per run")
    print(f"  ThreadPool (8)  : {thread:.3f} s per run")
    if thread > 0:
        print(f"  Speedup (serial / thread): {serial / thread:.2f}x")
    print()


def export_json(results, path, meta=None):
    payload = {"meta": meta or {}, "results": results}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


def export_csv(results, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "url",
                "count",
                "shortage",
                "error",
                "elapsed",
                "fetch_method",
                "timestamp",
                "headlines",
            ],
        )
        writer.writeheader()
        for r in results:
            row = dict(r)
            row["headlines"] = " | ".join(r["headlines"])
            writer.writerow(row)
    return path


if __name__ == "__main__":
    WORKERS = 8

    print(f"Launching ThreadPoolExecutor run ({WORKERS} workers)...")
    scraper = HeadlineScraper(max_workers=WORKERS)
    t0 = time.monotonic()
    results = scraper.scrape_thread()
    wall = time.monotonic() - t0
    stats = compute_stats(results, wall)
    print_results(f"ThreadPoolExecutor ({WORKERS} workers)", results, stats)

    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timeout": scraper.timeout,
        "max_retries": scraper.max_retries,
        "workers": WORKERS,
        "stats": stats,
    }
    export_json(results, "headlines.json", meta=meta)
    export_csv(results, "headlines.csv")
    print("Exported headlines.json and headlines.csv\n")

    # Benchmark
    benchmark(iterations=10)


# Environment setup: pip install newspaper3k pillow lxml_html_clean requests beautifulsoup4
