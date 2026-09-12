"""
How current something is: deadline urgency (P1-2) and record freshness (P1-6).

Both answer a question the product cannot dodge - "is this still true?" - and
both are computed from dates, never guessed. Like the rules engine, this module
emits machine keys only; core/i18n.py renders them.

THE RULE THAT SHAPES THIS MODULE
    Absence of a date is its own state, never the benign one. A record with no
    deadline is not "plenty of time", and a record never verified is not
    "recently verified". Most curated records legitimately carry no deadline,
    so the state they fall into is the one the user sees most often - making it
    exactly the wrong place to be reassuring.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from core.models import Opportunity, parse_iso_date

# -- deadline urgency (P1-2) ------------------------------------------------
URGENCY_PASSED = "passed"        # the date is behind us
URGENCY_IMMINENT = "imminent"    # days left, and few of them
URGENCY_SOON = "soon"            # inside a fortnight
URGENCY_PLENTY = "plenty"        # further out
URGENCY_UNKNOWN = "unknown"      # no deadline on record - do NOT read as "plenty"
URGENCY_CONTINUOUS = "continuous"  # enrolment never closes - nothing to miss

IMMINENT_DAYS = 3
SOON_DAYS = 14

# -- record freshness (P1-6) ------------------------------------------------
FRESH_RECENT = "recent"          # checked against the source lately
FRESH_AGING = "aging"            # worth re-checking
FRESH_STALE = "stale"            # old enough that it should not be relied on
FRESH_NEVER = "never"            # nobody on the team has ever verified it

RECENT_DAYS = 30
AGING_DAYS = 180


def deadline_urgency(deadline: Optional[str], today: Optional[date] = None) -> str:
    """
    Classify a deadline. Unparseable and missing both mean UNKNOWN.

    A malformed date is deliberately not treated as "no deadline": both end up
    UNKNOWN, which is the state that prompts the user to check the source,
    rather than either extreme.
    """
    parsed = parse_iso_date(deadline)
    if parsed is None:
        return URGENCY_UNKNOWN
    days = (parsed - (today or date.today())).days
    if days < 0:
        return URGENCY_PASSED
    if days <= IMMINENT_DAYS:
        return URGENCY_IMMINENT
    if days <= SOON_DAYS:
        return URGENCY_SOON
    return URGENCY_PLENTY


def days_remaining(deadline: Optional[str], today: Optional[date] = None) -> Optional[int]:
    """Days left, or None when there is no usable date. Negative once passed."""
    parsed = parse_iso_date(deadline)
    if parsed is None:
        return None
    return (parsed - (today or date.today())).days


def is_expired(deadline: Optional[str], today: Optional[date] = None) -> bool:
    """True only when a real date has passed. Unknown is never 'expired'."""
    return deadline_urgency(deadline, today) == URGENCY_PASSED


def match_urgency(match, today: Optional[date] = None) -> str:
    """
    Deadline state for a whole result, which is where "always open" lives.

    deadline_urgency() sees only a date string, so it cannot separate a
    programme that never closes from one whose date we simply do not have.
    Both arrive as "no date", and they are opposite instructions: the first
    needs nothing from the user today, the second needs them to go and check.

    A real deadline still wins. If a record carries both a date and the
    continuous flag, the date is the more specific claim.
    """
    if getattr(match, "deadline", None) and parse_iso_date(match.deadline):
        return deadline_urgency(match.deadline, today)
    if getattr(match, "always_open", False):
        return URGENCY_CONTINUOUS
    return deadline_urgency(match.deadline, today)


def record_freshness(opportunity: Opportunity, today: Optional[date] = None) -> str:
    """
    How recently a human checked this record against its official source.

    An unverified record is FRESH_NEVER whatever date it carries: a date in
    `last_verified` that was never backed by a real check is not evidence of
    anything, and Opportunity.is_verified() is the single place that decides
    whether such a check happened (DATA-01).

    An uploaded record is also FRESH_NEVER - reading a document is not the
    same as verifying it, however clearly the model read it.
    """
    if not opportunity.is_verified():
        return FRESH_NEVER
    verified = opportunity.verified_date()
    if verified is None:
        return FRESH_NEVER
    age = ((today or date.today()) - verified).days
    if age <= RECENT_DAYS:
        return FRESH_RECENT
    if age <= AGING_DAYS:
        return FRESH_AGING
    return FRESH_STALE


def days_since_verified(opportunity: Opportunity,
                        today: Optional[date] = None) -> Optional[int]:
    """Age of the last real verification, or None if there has never been one."""
    if not opportunity.is_verified():
        return None
    verified = opportunity.verified_date()
    if verified is None:
        return None
    return ((today or date.today()) - verified).days


def should_prompt_verification(opportunity: Opportunity,
                               today: Optional[date] = None) -> bool:
    """
    Whether to actively ask the user to check the source.

    True for everything except a recently verified record - which is to say,
    true by default. Existing in the database is not evidence of currency.
    """
    return record_freshness(opportunity, today) != FRESH_RECENT
