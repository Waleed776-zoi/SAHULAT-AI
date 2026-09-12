"""
Side-by-side comparison of opportunities (P1-5).

Machine values only; core/i18n.py renders them.

WHAT "EASIER TO PURSUE" MEANS HERE
    The brief asks for a summary line such as "Opportunity A appears easier to
    pursue". That is a claim about *effort*, and it is the only claim this
    module makes. It is computed from four countable things - unmet conditions,
    open questions, outstanding documents, and whether a deadline is actually
    on record - and it deliberately says nothing about which is worth more,
    which is more likely to be awarded, or which the user should choose. A
    smaller scholarship with a short form is "easier"; that does not make it
    better, and the UI must not present it as a recommendation to apply.

    Where two options are genuinely close, this returns no leader rather than
    manufacturing one.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Sequence

from core.models import MatchResult, STATUS_ELIGIBLE, STATUS_NEEDS_VERIFICATION
from core.readiness import readiness
from core.timeliness import URGENCY_PASSED, deadline_urgency, days_remaining

# How much each unresolved thing counts toward "effort left". These are
# weights, not truths: one blocked condition outweighs any amount of
# paperwork, because paperwork can be obtained and a failed condition cannot.
WEIGHT_BLOCKER = 100
WEIGHT_GAP = 10
WEIGHT_DOCUMENT = 1

# Below this gap the two are treated as equally easy and no leader is named.
MEANINGFUL_MARGIN = 5


@dataclass
class ComparisonRow:
    """One opportunity's comparable facts."""
    opportunity_id: str
    name: str
    status: str
    met: int
    total: int
    blockers: int
    gaps: int
    documents_total: int
    documents_missing: int
    deadline: Optional[str]
    days_remaining: Optional[int]
    urgency: str
    effort: int
    category: str
    has_official_url: bool


@dataclass
class Comparison:
    rows: List[ComparisonRow] = field(default_factory=list)
    # The id of the lowest-effort option, or None when it is too close to call
    # or nothing is actionable.
    easiest_id: Optional[str] = None
    # Machine reasons behind that call, for i18n to render.
    reasons: List[Dict] = field(default_factory=list)


def _effort(row_blockers: int, row_gaps: int, documents_missing: int) -> int:
    return (row_blockers * WEIGHT_BLOCKER
            + row_gaps * WEIGHT_GAP
            + documents_missing * WEIGHT_DOCUMENT)


def compare(matches: Sequence[MatchResult],
            documents_ready: Optional[Dict[str, set]] = None,
            today: Optional[date] = None) -> Comparison:
    """
    Build a comparison of two or more results.

    `documents_ready` maps opportunity_id -> ticked checklist indices, so the
    comparison reflects what the user has actually gathered rather than
    assuming they hold nothing.
    """
    ticked = documents_ready or {}
    rows: List[ComparisonRow] = []

    for match in matches:
        opportunity = match.opportunity
        score = match.scorecard()
        docs = readiness(opportunity, ticked.get(opportunity.opportunity_id, set()))
        rows.append(ComparisonRow(
            opportunity_id=opportunity.opportunity_id,
            name=opportunity.name,
            status=match.overall_status,
            met=score["met"],
            total=score["total"],
            blockers=score["unmet"],
            gaps=score["unknown"],
            documents_total=docs.total,
            documents_missing=len(docs.missing),
            deadline=match.deadline,
            days_remaining=days_remaining(match.deadline, today),
            urgency=deadline_urgency(match.deadline, today),
            effort=_effort(score["unmet"], score["unknown"], len(docs.missing)),
            category=opportunity.category,
            has_official_url=bool(opportunity.official_url),
        ))

    comparison = Comparison(rows=rows)

    # Only options the user could actually pursue can be "easiest": an expired
    # listing with nothing left to do is not a low-effort option, it is a dead
    # one (BUG-04).
    candidates = [row for row in rows
                  if row.urgency != URGENCY_PASSED
                  and row.status in (STATUS_ELIGIBLE, STATUS_NEEDS_VERIFICATION)]
    if len(candidates) < 2:
        return comparison

    ranked = sorted(candidates, key=lambda r: (r.effort, r.name.lower()))
    best, runner_up = ranked[0], ranked[1]
    if runner_up.effort - best.effort < MEANINGFUL_MARGIN:
        return comparison          # too close to call - say nothing

    comparison.easiest_id = best.opportunity_id
    if best.blockers < runner_up.blockers:
        comparison.reasons.append({"key": "fewer_blockers", "value": best.blockers})
    if best.gaps < runner_up.gaps:
        comparison.reasons.append({"key": "fewer_gaps", "value": best.gaps})
    if best.documents_missing < runner_up.documents_missing:
        comparison.reasons.append({"key": "fewer_documents",
                                   "value": best.documents_missing})
    return comparison
