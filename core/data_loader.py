"""
Loads curated opportunity records from data/opportunities/*.json into
Opportunity objects. Skips schema.json (documentation only) and any file
starting with an underscore.

Placeholder entries (name still starting with "REPLACE ME") are skipped so an
uncurated record can never silently appear in a live demo. A category that
ends up with no records is still reported with a count of zero: the UI reads
the category counts below and labels an empty category honestly instead of
showing an unexplained blank result set (DATA-03).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List

from core.models import Opportunity

log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "opportunities"

# Every category the product intends to support, in display order. A category
# with zero loaded records is shown as "coming soon" rather than hidden, so the
# roadmap stays visible and the gap stays honest.
KNOWN_CATEGORIES = ("scholarship", "job", "skills", "assistance")

_PLACEHOLDER_PREFIXES = ("REPLACE ME", "TODO")


def _is_placeholder_record(record: dict) -> bool:
    name = str(record.get("name", "")).strip().upper()
    return any(name.startswith(p) for p in _PLACEHOLDER_PREFIXES)


def load_all_opportunities() -> List[Opportunity]:
    opportunities: List[Opportunity] = []

    if not DATA_DIR.exists():
        log.warning("Opportunity data directory not found: %s", DATA_DIR)
        return opportunities

    for path in sorted(DATA_DIR.glob("*.json")):
        if path.name in ("schema.json",) or path.name.startswith("_"):
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            # One malformed file must not take down the whole catalogue.
            log.error("Skipping unreadable opportunity file %s: %s", path.name, exc)
            continue

        # A file may hold one record, a list of records, or a list wrapped
        # under a "jobs" / "records" key. Supporting the bare
        # list matters: several records concatenated into one file is the
        # natural way to paste curated data in, and before this the whole
        # file failed to parse and was skipped with only a log line - eight
        # records vanished from the catalogue without anything on screen
        # saying so.
        if isinstance(payload, list):
            records = payload
        elif isinstance(payload.get("jobs"), list):
            records = payload["jobs"]
        elif isinstance(payload.get("records"), list):
            records = payload["records"]
        else:
            records = [payload]

        for record in records:
            if not isinstance(record, dict) or _is_placeholder_record(record):
                continue
            try:
                opportunities.append(Opportunity.from_dict(record))
            except KeyError as exc:
                log.error("Skipping record in %s - missing required field %s", path.name, exc)

    return opportunities


def load_by_category(category: str) -> List[Opportunity]:
    return [o for o in load_all_opportunities() if o.category == category]


def category_counts(opportunities: List[Opportunity]) -> Dict[str, int]:
    """How many records loaded per category, including the empty ones (DATA-03)."""
    counts = {c: 0 for c in KNOWN_CATEGORIES}
    for o in opportunities:
        counts[o.category] = counts.get(o.category, 0) + 1
    return counts


def catalogue_health(opportunities: List[Opportunity]) -> Dict[str, int]:
    """Verification summary for the sidebar (DATA-01/DATA-02 visibility)."""
    verified = sum(1 for o in opportunities if o.is_verified())
    return {
        "total": len(opportunities),
        "verified": verified,
        "unverified": len(opportunities) - verified,
    }
