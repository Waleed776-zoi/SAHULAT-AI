"""
Loads curated opportunity records from data/opportunities/*.json into
Opportunity objects. Skips schema.json (documentation only) and any file
starting with an underscore.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from core.models import Opportunity

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "opportunities"


def load_all_opportunities() -> List[Opportunity]:
    opportunities: List[Opportunity] = []

    for path in sorted(DATA_DIR.glob("*.json")):
        if path.name in ("schema.json",) or path.name.startswith("_"):
            continue

        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        # njp_jobs_sample.json wraps multiple jobs under a "jobs" key;
        # every other file is a single opportunity record.
        if "jobs" in payload and isinstance(payload["jobs"], list):
            for job_dict in payload["jobs"]:
                if job_dict.get("name", "").startswith("REPLACE ME"):
                    # Skip unfilled placeholder entries so they never
                    # silently show up in a live demo.
                    continue
                opportunities.append(Opportunity.from_dict(job_dict))
        else:
            opportunities.append(Opportunity.from_dict(payload))

    return opportunities


def load_by_category(category: str) -> List[Opportunity]:
    return [o for o in load_all_opportunities() if o.category == category]
