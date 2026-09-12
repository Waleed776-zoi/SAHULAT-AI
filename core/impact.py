"""
Session impact figures (P2-2).

Every number here is counted from work this session actually did - records
screened, conditions evaluated, documents listed. Nothing is sampled,
extrapolated, or carried over between users.

THE ONE ESTIMATE, AND WHY IT IS FENCED OFF
    "Time saved" cannot be counted, only assumed. It is computed from a single
    visible constant, `MINUTES_PER_LOOKUP`, which stands for how long it takes
    a person to find one scheme's rules and read them on a government site.
    That constant is a guess. It is defined in one place, exposed through
    `estimate_basis()` so the UI can state it, and the result is labelled an
    estimate wherever it appears.

    The brief asks for these metrics "for presentations". That is exactly the
    context where an unlabelled invented number does the most damage: a judge
    who discovers the basis was never stated stops believing the numbers that
    *were* counted. Naming the assumption is what keeps the honest figures
    credible.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Sequence

from core.models import MatchResult

# How long we assume it takes someone to locate one scheme's official page and
# work out its eligibility rules unaided. A guess, and labelled as one.
MINUTES_PER_LOOKUP = 8


@dataclass
class Impact:
    """Counted work, plus one clearly-marked estimate."""
    opportunities_screened: int = 0
    requirements_checked: int = 0
    documents_identified: int = 0
    priority_matches: int = 0

    @property
    def estimated_minutes_saved(self) -> int:
        """The only estimate. See MINUTES_PER_LOOKUP."""
        return self.opportunities_screened * MINUTES_PER_LOOKUP

    def is_empty(self) -> bool:
        return self.opportunities_screened == 0


def measure(results: Sequence[MatchResult]) -> Impact:
    """
    Count what this screening run did.

    Conditions counted are the ones actually evaluated - `applicable_checks()`
    excludes conditions an opportunity does not use, so a record with two
    rules never contributes fourteen.
    """
    impact = Impact()
    for match in results:
        impact.opportunities_screened += 1
        impact.requirements_checked += len(match.applicable_checks())
        impact.documents_identified += len(match.opportunity.required_documents or [])
        impact.priority_matches += len(match.matched_priority_groups)
    return impact


def estimate_basis() -> Dict[str, int]:
    """The assumption behind the estimate, so the UI can state it outright."""
    return {"minutes_per_lookup": MINUTES_PER_LOOKUP}
