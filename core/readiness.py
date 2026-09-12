"""
Application readiness from the document checklist (P1-1).

The percentage here is a real one, and it is worth being explicit about why
this product shows it when it refuses to show a "profile match %":

    readiness = documents the user ticked / documents the record lists

Every term is something the user themselves asserted or the record states.
Nothing is inferred, and the number cannot drift from the checklist it is
computed from. A "match %" would instead be a guess at a decision made by an
awarding body - which is why V2-1 shows a count of conditions instead.

What this still is NOT: a prediction that the application will succeed, or a
claim that the ticked documents are valid, current or acceptable. It is a
progress bar over a list the user is filling in.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence, Set

from core.models import Opportunity


@dataclass
class Readiness:
    """Checklist state for one opportunity. Document names, not indices."""
    have: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.have) + len(self.missing)

    @property
    def percent(self) -> int:
        """
        Whole-number percent, floored so it can never round up to 100 while
        something is still missing - "100% ready" with an outstanding document
        is the one output this must never produce.
        """
        if not self.total:
            return 0
        if not self.missing:
            return 100
        return min(99, (len(self.have) * 100) // self.total)

    @property
    def is_complete(self) -> bool:
        return self.total > 0 and not self.missing

    def next_missing(self) -> str:
        """The first outstanding document, for the next-step line."""
        return self.missing[0] if self.missing else ""


def readiness(opportunity: Opportunity, ready_indices: Sequence[int] | Set[int] = ()) -> Readiness:
    """
    Split the record's required documents into have / still needed.

    `ready_indices` are positions the user ticked. Out-of-range values are
    ignored rather than raising: the checklist lives in UI state and a record
    can change under it, and a stale tick must not take the page down.
    """
    documents = list(opportunity.required_documents or [])
    ticked = {index for index in ready_indices if 0 <= index < len(documents)}
    return Readiness(
        have=[document for index, document in enumerate(documents) if index in ticked],
        missing=[document for index, document in enumerate(documents) if index not in ticked],
    )
