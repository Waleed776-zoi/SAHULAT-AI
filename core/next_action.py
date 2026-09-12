"""
The single most useful next step for a given match (V2 P0-6).

DESIGN PRINCIPLE, same as the rules engine: this module DECIDES, it does not
describe. It emits a stable machine `key` plus structured `subject` values;
core/i18n.describe_next_action() turns that into English or Urdu. No prose
lives here, and no LLM is consulted - the next step is a function of the
result, so it is reproducible and testable.

The order below is a priority ladder, not a menu. Exactly one action comes
back, because a result that offers six equally-weighted things to do next is
the same as offering none.

WHAT THIS MUST NEVER DO
    Promise an outcome. "Fix your marks and you will be eligible" is a claim
    about a future decision this system has not made and cannot make. An
    action names the next *step*, never the result of taking it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.models import (
    MatchResult,
    STATUS_ELIGIBLE, STATUS_NEEDS_VERIFICATION, STATUS_NOT_ELIGIBLE,
)
from core.readiness import readiness

# Machine keys. i18n owns the wording for each.
ACTION_EXPLORE_OTHERS = "explore_others"       # this listing has closed
ACTION_REVIEW_BLOCKER = "review_blocker"       # a condition is demonstrably unmet
ACTION_ANSWER_MISSING = "answer_missing"       # we can settle it by asking the user
ACTION_CONFIRM_CONDITION = "confirm_condition"  # only the source can settle it
ACTION_PREPARE_DOCUMENTS = "prepare_documents"  # eligible, none ticked yet
ACTION_OBTAIN_DOCUMENT = "obtain_document"      # eligible, specific one missing
ACTION_APPLY = "apply"                          # eligible, official link known
ACTION_CHECK_SOURCE = "check_source"            # fallback: go to the source


@dataclass
class NextAction:
    """One action. `subject` carries structured detail for i18n to render."""
    key: str
    subject: Dict[str, Any] = field(default_factory=dict)
    url: Optional[str] = None
    # Conditions this action refers to, so the UI can point at the same rows
    # the scorecard already showed rather than restating them.
    check_keys: List[str] = field(default_factory=list)


def next_action(match: MatchResult, documents_ready=None) -> NextAction:
    """
    The one thing worth doing next about this result.

    Ladder, highest priority first:

    1. The listing has closed. Nothing about this record is actionable any
       more, whatever the profile says - so send the user to their other
       matches rather than to a dead application page (BUG-04: closed is a
       property of the listing, not a judgment about the user).
    2. A condition is demonstrably unmet. Name that condition. This is the
       decisive fact, and burying it under "prepare your documents" would be
       actively misleading.
    3. Something could not be checked. Two different situations:
         a. the user simply has not answered -> ask them, we can settle it
            immediately and for free;
         b. they answered and the *record* is incomplete -> only the official
            source can settle it.
       (a) is checked first because it is the cheaper fix.
    4. Eligible with documents outstanding -> name the next one to obtain.
       This is where the checklist feeds back in (P1-1): once the user has
       ticked things off, "prepare your documents" stops being useful and the
       step becomes the specific paper still missing.
    5. Eligible with everything ticked, or with a link -> apply.
    6. Anything else -> go and read the source.
    """
    opportunity = match.opportunity

    if match.listing_closed:
        return NextAction(ACTION_EXPLORE_OTHERS)

    blockers = match.blockers()
    if blockers:
        first = blockers[0]
        return NextAction(
            ACTION_REVIEW_BLOCKER,
            subject={"check": first.key, "required": first.required, "actual": first.actual},
            url=opportunity.official_url or None,
            check_keys=[c.key for c in blockers],
        )

    gaps = match.gaps()
    if gaps:
        if match.missing_profile_fields:
            return NextAction(
                ACTION_ANSWER_MISSING,
                subject={"fields": list(match.missing_profile_fields)},
                check_keys=[c.key for c in gaps],
            )
        first = gaps[0]
        return NextAction(
            ACTION_CONFIRM_CONDITION,
            subject={"check": first.key, "required": first.required},
            url=opportunity.official_url or None,
            check_keys=[c.key for c in gaps],
        )

    if match.overall_status == STATUS_ELIGIBLE and opportunity.required_documents:
        checklist = readiness(opportunity, documents_ready or set())
        if checklist.is_complete:
            # Everything gathered: the next step is the application itself.
            return NextAction(ACTION_APPLY, url=opportunity.official_url or None)
        if checklist.have:
            return NextAction(
                ACTION_OBTAIN_DOCUMENT,
                subject={"document": checklist.next_missing(),
                         "remaining": len(checklist.missing)},
                url=opportunity.official_url or None,
            )
        return NextAction(
            ACTION_PREPARE_DOCUMENTS,
            subject={"count": len(opportunity.required_documents)},
            url=opportunity.official_url or None,
        )

    if match.overall_status == STATUS_ELIGIBLE and opportunity.official_url:
        return NextAction(ACTION_APPLY, url=opportunity.official_url)

    return NextAction(ACTION_CHECK_SOURCE, url=opportunity.official_url or None)


def is_actionable_now(match: MatchResult, documents_ready=None) -> bool:
    """
    Whether the next step moves the user toward applying, rather than toward
    finding out more. Used only to decide visual emphasis - never to change
    an eligibility status.
    """
    return next_action(match, documents_ready).key in (
        ACTION_PREPARE_DOCUMENTS, ACTION_OBTAIN_DOCUMENT, ACTION_APPLY)
