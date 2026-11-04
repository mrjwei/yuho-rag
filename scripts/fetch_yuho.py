"""Download the latest 有価証券報告書 (annual securities report) PDFs via EDINET API v2.

Usage:
    export EDINET_API_KEY=your_key
    uv run scripts/fetch_yuho.py                 # scan back 400 days (default)
    uv run scripts/fetch_yuho.py --days 500 --out data/raw

Output:
    data/raw/<sector>/<code>_<name>_<period_end>.pdf
    data/raw/manifest.json   (metadata for chunk tagging + README sources)
    data/raw/.cache/         (daily document lists; safe to delete, add to .gitignore)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API = "https://api.edinet-fsa.go.jp/api/v2"
DOC_TYPE_YUHO = "120"  # 有価証券報告書 (130 = 訂正有価証券報告書, ignored)

# 4-digit TSE code -> (sector, short name). EDINET's secCode is 5 digits (code + "0").
COMPANIES: dict[str, tuple[str, str]] = {
    # retail
    "3382": ("retail", "seven-and-i"),
    "8267": ("retail", "aeon"),
    "9983": ("retail", "fast-retailing"),
    # electronics
    "6758": ("electronics", "sony"),
    "6752": ("electronics", "panasonic"),
    "6501": ("electronics", "hitachi"),
    "6861": ("electronics", "keyence"),
    # banking
    "8306": ("banking", "mufg"),
    "8316": ("banking", "smfg"),
    "8411": ("banking", "mizuho"),
}


def make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers["User-Agent"] = "yuho-rag/0.1"
    return session


def list_documents(
    session: requests.Session, day: date, key: str, cache_dir: Path
) -> tuple[list[dict], bool]:
    """Return (filings submitted on `day`, came_from_cache)."""
    cache_file = cache_dir / f"{day.isoformat()}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text("utf-8")), True

    resp = session.get(
        f"{API}/documents.json",
        params={"date": day.isoformat(), "type": 2, "Subscription-Key": key},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()

    # EDINET reports errors in the JSON body, often with HTTP 200.
    meta = payload.get("metadata", {})
    status = str(meta.get("status") or payload.get("StatusCode") or "")
    if status != "200":
        message = meta.get("message") or payload.get("message") or payload
        raise RuntimeError(f"{day}: EDINET status {status}: {message}")

    results = payload.get("results") or []
    if day < date.today():  # today's list can still grow, so don't cache it
        cache_file.write_text(json.dumps(results, ensure_ascii=False), "utf-8")
    return results, False


def is_target_yuho(doc: dict) -> bool:
    return (
        doc.get("docTypeCode") == DOC_TYPE_YUHO
        and doc.get("withdrawalStatus") == "0"  # not withdrawn
        and doc.get("pdfFlag") == "1"  # PDF available
    )


def find_latest_filings(
    session: requests.Session, key: str, days: int, cache_dir: Path, sleep: float
) -> dict[str, dict]:
    """Walk back day by day; the first 有報 seen per company is its latest."""
    targets = {code + "0" for code in COMPANIES}
    found: dict[str, dict] = {}
    today = date.today()

    for offset in range(days):
        day = today - timedelta(days=offset)
        if day.weekday() >= 5:  # EDINET doesn't take filings on weekends
            continue
        remaining = targets - found.keys()
        if not remaining:
            break

        docs, cached = list_documents(session, day, key, cache_dir)
        for doc in docs:
            sec = doc.get("secCode")
            if sec in remaining and is_target_yuho(doc):
                prev = found.get(sec)
                if prev is None or doc["submitDateTime"] > prev["submitDateTime"]:
                    found[sec] = doc
                    print(f"  found {sec[:4]} {doc['filerName']} ({day}) {doc['docID']}")

        if not cached:
            time.sleep(sleep)

    return found


def download_pdf(session: requests.Session, doc_id: str, key: str, dest: Path) -> str:
    if dest.exists() and dest.stat().st_size > 0:
        return "exists"

    resp = session.get(
        f"{API}/documents/{doc_id}",
        params={"type": 2, "Subscription-Key": key},
        timeout=180,
    )
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "")
    if "application/pdf" not in content_type:
        raise RuntimeError(f"{doc_id}: expected PDF, got {content_type}: {resp.text[:200]}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")
    tmp.write_bytes(resp.content)
    tmp.replace(dest)
    return "downloaded"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=Path("data/raw"))
    parser.add_argument("--days", type=int, default=400, help="how far back to scan (default 400)")
    parser.add_argument("--sleep", type=float, default=0.3, help="pause between API calls in seconds")
    args = parser.parse_args()

    key = os.environ.get("EDINET_API_KEY")
    if not key:
        sys.exit("Set EDINET_API_KEY first (export EDINET_API_KEY=...).")

    cache_dir = args.out / ".cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    session = make_session()

    print(f"Scanning the last {args.days} days of EDINET filings...")
    found = find_latest_filings(session, key, args.days, cache_dir, args.sleep)

    manifest = []
    for code, (sector, name) in COMPANIES.items():
        doc = found.get(code + "0")
        if doc is None:
            print(f"  MISSING {code} {name}: no 有報 in the last {args.days} days (try --days 500)")
            continue

        period_end = doc.get("periodEnd") or "unknown"
        dest = args.out / sector / f"{code}_{name}_{period_end}.pdf"
        status = download_pdf(session, doc["docID"], key, dest)
        print(f"  {status:<10} {dest}")
        time.sleep(args.sleep)

        manifest.append(
            {
                "sector": sector,
                "name": name,
                "sec_code": code,
                "edinet_code": doc.get("edinetCode"),
                "filer_name": doc.get("filerName"),
                "doc_id": doc["docID"],
                "doc_description": doc.get("docDescription"),
                "period_start": doc.get("periodStart"),
                "period_end": doc.get("periodEnd"),
                "submitted_at": doc.get("submitDateTime"),
                "path": dest.as_posix(),
                "source": f"{API}/documents/{doc['docID']}?type=2",
            }
        )

    manifest_path = args.out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), "utf-8")
    print(f"\n{len(manifest)}/{len(COMPANIES)} reports saved. Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
