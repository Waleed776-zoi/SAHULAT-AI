"""
Public Assistance (DATA-07), and the two model additions it forced.

Assistance screens on a different axis from everything else in the catalogue.
A scholarship asks what you have achieved; assistance asks what has happened to
you. That difference exposed two things the model could not say:

1.  `required_groups` - a GATE on circumstance. `priority_groups` already
    existed but is advantage-only by design and never excludes anyone, which is
    correct for a scholarship that favours women and wrong for an orphans' home.
    Without a gate, the engine told every applicant they qualified.

2.  `enrolment_is_continuous` - a programme that never closes. With no date on
    record the UI said "no deadline on record - do not read as plenty of time",
    which is right when a date is missing and wrong when there is no date to
    miss. Opposite instructions to a user, so they cannot share a label.

The third theme has no code behind it and cannot have any: several of these
programmes turn on facts a non-identifying profile must never hold - a PMT
poverty score, a pregnancy, a religion. Those are asserted as prose that must
be present, because the honest handling is to say so on the card.
"""
from __future__ import annotations

import unittest

from core.data_loader import load_all_opportunities
from core.i18n import LANGUAGES, describe_check, describe_urgency, scorecard_row, t
from core.models import (CHECK_REQUIRED_GROUP, GATEABLE_GROUPS, GROUP_PROFILE_FIELD,
                         LISTING_ALWAYS_OPEN, LISTING_OPEN, LISTING_VERIFY,
                         MET, UNKNOWN, UNMET, MatchResult, Opportunity,
                         PRIORITY_GROUPS, UserProfile, sample_profile)
from core.rules_engine import evaluate
from core.timeliness import (URGENCY_CONTINUOUS, URGENCY_UNKNOWN, match_urgency)

ALL = load_all_opportunities()
ASSISTANCE = [o for o in ALL if o.category == "assistance"]
BY_ID = {o.opportunity_id: o for o in ALL}


def _group_check(profile, opportunity):
    return next(c for c in evaluate(profile, opportunity).checks
                if c.key == CHECK_REQUIRED_GROUP)


class TestRequiredGroupGate(unittest.TestCase):
    """`required_groups` excludes; `priority_groups` never does."""

    def test_membership_is_three_valued(self):
        """
        Unanswered is not "no". A profile that never said whether it is an
        orphan must produce a question, not a rejection - the difference
        between "you do not qualify" and "we need one more answer".
        """
        orphans_only = BY_ID["pbm_sweet_homes"]
        self.assertEqual(_group_check(UserProfile(age=16, is_orphan=True),
                                      orphans_only).status, MET)
        self.assertEqual(_group_check(UserProfile(age=16, is_orphan=False),
                                      orphans_only).status, UNMET)
        self.assertEqual(_group_check(UserProfile(age=16),
                                      orphans_only).status, UNKNOWN)

    def test_an_unanswered_gate_asks_for_the_field_behind_it(self):
        result = evaluate(UserProfile(age=16), BY_ID["pbm_sweet_homes"])
        self.assertIn("is_orphan", result.missing_profile_fields)

    def test_the_disability_gate_behaves_the_same_way(self):
        card = BY_ID["punjab_himmat_card"]
        self.assertEqual(_group_check(UserProfile(age=30, has_disability=True),
                                      card).status, MET)
        self.assertEqual(_group_check(UserProfile(age=30, has_disability=False),
                                      card).status, UNMET)
        self.assertEqual(_group_check(UserProfile(age=30), card).status, UNKNOWN)

    def test_several_groups_read_as_or_not_and(self):
        """
        "For orphans and persons with disabilities" admits either. AND would be
        the stricter reading, and stricter is the dangerous direction to guess
        in - it turns a wrongly-narrow record into a wrongly-refused person.
        """
        record = Opportunity.from_dict({
            "opportunity_id": "t", "name": "T", "category": "assistance",
            "provider": "T", "official_url": "https://example.gov.pk",
            "source_title": "T", "last_verified": "2026-09-12",
            "eligibility_conditions": {"required_groups": ["orphan", "disability"]},
        })
        either = UserProfile(age=30, is_orphan=True, has_disability=False)
        self.assertEqual(_group_check(either, record).status, MET)
        other = UserProfile(age=30, is_orphan=False, has_disability=True)
        self.assertEqual(_group_check(other, record).status, MET)
        neither = UserProfile(age=30, is_orphan=False, has_disability=False)
        self.assertEqual(_group_check(neither, record).status, UNMET)

    def test_priority_groups_still_never_exclude_anyone(self):
        """
        The whole point of adding a gate was to stop abusing the advantage. A
        record with priority groups and no required groups must still admit
        someone in none of them.
        """
        record = Opportunity.from_dict({
            "opportunity_id": "t", "name": "T", "category": "assistance",
            "provider": "T", "official_url": "https://example.gov.pk",
            "source_title": "T", "last_verified": "2026-09-12",
            "eligibility_conditions": {"priority_groups": ["orphan", "disability"]},
        })
        nobody = UserProfile(age=30, is_orphan=False, has_disability=False)
        self.assertEqual(evaluate(nobody, record).overall_status, "eligible")

    def test_only_gateable_groups_are_used_as_gates(self):
        """
        Nothing in a non-identifying profile establishes religion or district,
        so `minority` and `under_served_district` can never be screened. A
        record using one as a gate would produce a permanent UNKNOWN that no
        user could ever resolve.
        """
        for opportunity in ALL:
            for group in (opportunity.eligibility_conditions.required_groups or []):
                self.assertIn(group, GATEABLE_GROUPS,
                              f"{opportunity.opportunity_id} gates on {group!r}, which "
                              f"no profile answer can establish")

    def test_every_gateable_group_has_a_profile_field_that_exists(self):
        for group, field_name in GROUP_PROFILE_FIELD.items():
            self.assertIn(group, PRIORITY_GROUPS)
            self.assertTrue(hasattr(UserProfile(), field_name), field_name)

    def test_the_gate_is_rendered_in_every_language(self):
        check = _group_check(UserProfile(age=16, is_orphan=False),
                             BY_ID["pbm_sweet_homes"])
        for lang in LANGUAGES:
            title, detail = describe_check(check, lang)
            self.assertTrue(title.strip(), lang)
            self.assertTrue(detail.strip(), lang)
            self.assertEqual(len(scorecard_row(check, lang)), 4)
        # Urdu must actually be Urdu, not an English fallback.
        self.assertNotEqual(describe_check(check, "ur")[0],
                            describe_check(check, "en")[0])
        self.assertNotEqual(describe_check(check, "ur_roman")[0],
                            describe_check(check, "en")[0])


class TestAlwaysOpenEnrolment(unittest.TestCase):
    """"Never closes" and "we have no date" are opposite states."""

    def _result(self, **kwargs) -> MatchResult:
        return MatchResult(opportunity=ASSISTANCE[0], overall_status="eligible", **kwargs)

    def test_continuous_is_not_the_same_as_unknown(self):
        self.assertEqual(match_urgency(self._result(always_open=True)),
                         URGENCY_CONTINUOUS)
        self.assertEqual(match_urgency(self._result(always_open=False)),
                         URGENCY_UNKNOWN)

    def test_listing_state_separates_them_too(self):
        self.assertEqual(self._result(always_open=True).listing_state(),
                         LISTING_ALWAYS_OPEN)
        self.assertEqual(self._result(always_open=False).listing_state(),
                         LISTING_VERIFY)

    def test_a_real_deadline_outranks_the_flag(self):
        """
        A record carrying both a date and the flag is contradictory. The date
        is the more specific claim, so it wins - and a user is shown the
        countdown rather than being told there is nothing to miss.
        """
        both = self._result(always_open=True, deadline="2026-12-01")
        self.assertEqual(both.listing_state(), LISTING_OPEN)
        self.assertNotEqual(match_urgency(both), URGENCY_CONTINUOUS)

    def test_a_closed_deadline_still_wins(self):
        closed = self._result(always_open=True, listing_closed=True,
                              deadline="2020-01-01")
        self.assertEqual(closed.listing_state(), "closed")

    def test_continuous_is_described_in_every_language(self):
        for lang in LANGUAGES:
            label, detail = describe_urgency(URGENCY_CONTINUOUS, None, lang)
            self.assertTrue(label.strip(), lang)
            self.assertTrue(detail.strip(),
                            f"{lang}: an always-open programme says nothing")
            self.assertTrue(t("listing_always_open", lang).strip(), lang)
        self.assertNotEqual(describe_urgency(URGENCY_CONTINUOUS, None, "ur")[0],
                            describe_urgency(URGENCY_CONTINUOUS, None, "en")[0])

    def test_assistance_records_use_the_flag(self):
        """
        Assistance is overwhelmingly rolling. If none of these records set the
        flag, the field was added for nothing and the category will render as
        ten unknowns.
        """
        continuous = [o for o in ASSISTANCE
                      if o.eligibility_conditions.enrolment_is_continuous]
        self.assertGreaterEqual(len(continuous), len(ASSISTANCE) - 1)

    def test_no_assistance_record_carries_a_provisional_deadline(self):
        """
        An always-open programme has no cycle to place a provisional date in.
        Setting both would put a countdown on something that never closes.
        """
        for opportunity in ASSISTANCE:
            conditions = opportunity.eligibility_conditions
            if conditions.enrolment_is_continuous:
                self.assertIsNone(conditions.application_deadline,
                                  opportunity.opportunity_id)
                self.assertFalse(conditions.deadline_is_provisional,
                                 opportunity.opportunity_id)


class TestAssistanceCatalogue(unittest.TestCase):
    """DATA-07: the last empty category."""

    def test_the_category_has_records(self):
        self.assertGreaterEqual(len(ASSISTANCE), 8)

    def test_no_category_is_empty_any_more(self):
        from core.data_loader import KNOWN_CATEGORIES, category_counts
        counts = category_counts(ALL)
        for category in KNOWN_CATEGORIES:
            self.assertGreater(counts[category], 0,
                               f"{category} is still empty")

    def test_the_gates_actually_gate(self):
        """
        Both restricted records must reject the demo profile, who is neither an
        orphan nor disabled. Before `required_groups` existed, both told her
        she qualified.
        """
        profile = sample_profile()
        for record_id in ("pbm_sweet_homes", "punjab_himmat_card"):
            result = evaluate(profile, BY_ID[record_id])
            self.assertEqual(result.overall_status, "not_eligible", record_id)
            self.assertIn(CHECK_REQUIRED_GROUP,
                          [c.key for c in result.blockers()], record_id)

    def test_the_category_still_helps_the_demo_profile(self):
        """
        A category that rejects everyone is not screening, it is a wall. A
        low-income young woman should genuinely reach several of these.
        """
        eligible = [o for o in ASSISTANCE
                    if evaluate(sample_profile(), o).overall_status == "eligible"]
        self.assertGreaterEqual(len(eligible), 3)
        self.assertLess(len(eligible), len(ASSISTANCE),
                        "every assistance record accepts her - nothing is screening")

    def test_means_tested_records_screen_on_circumstance_not_qualification(self):
        """
        Assistance asks what happened to you, not what you achieved. A record
        here demanding a degree or work experience is almost certainly a
        miscategorised job or scholarship - EOBI is the deliberate exception,
        being a contributory pension rather than aid.
        """
        for opportunity in ASSISTANCE:
            conditions = opportunity.eligibility_conditions
            self.assertIsNone(conditions.min_education_level,
                              f"{opportunity.opportunity_id} screens on education")
            self.assertIsNone(conditions.min_marks_percentage,
                              f"{opportunity.opportunity_id} screens on marks")
            if opportunity.opportunity_id != "eobi_old_age_pension":
                self.assertIsNone(conditions.min_experience_years,
                                  f"{opportunity.opportunity_id} screens on experience")

    def test_records_screening_on_something_they_cannot_ask_say_so(self):
        """
        The honest handling of an unaskable condition.

        BISP turns on a PMT poverty score, Nashonuma on pregnancy, Zakat on
        religion. None can live in a non-identifying profile, and none may be
        silently dropped either - a green result that ignores the real gate is
        worse than no result. Each of these records must state the condition in
        prose the card displays.
        """
        unaskable = {
            "bisp_kafaalat": ("pmt", "8171"),
            "bisp_nashonuma": ("pregnan",),
            "zakat_guzara_allowance": ("muslim",),
            "eobi_old_age_pension": ("contribut",),
        }
        for record_id, needles in unaskable.items():
            record = BY_ID[record_id]
            prose = " ".join(filter(None, [
                record.summary_en,
                record.eligibility_conditions.special_quota_note,
                record.disclaimer,
            ])).lower()
            for needle in needles:
                self.assertIn(needle, prose,
                              f"{record_id} screens on something it never mentions")

    def test_the_loan_is_marked_as_a_loan(self):
        """
        One record in this category creates a debt. Presenting it beside nine
        grants without saying so would be the most consequential omission in
        the catalogue.
        """
        record = BY_ID["interest_free_loan_scheme"]
        prose = (record.eligibility_conditions.special_quota_note + " "
                 + record.disclaimer).lower()
        self.assertIn("repaid", prose)
        self.assertIn("loan, not a grant", record.disclaimer.lower())

    def test_provincial_records_name_their_province(self):
        for opportunity in ASSISTANCE:
            provinces = opportunity.eligibility_conditions.domicile_provinces
            if provinces:
                self.assertTrue(
                    any(p.lower() in opportunity.province_scope.lower() for p in provinces),
                    f"{opportunity.opportunity_id} gates on {provinces} but its scope "
                    f"reads {opportunity.province_scope!r}")

    def test_every_assistance_record_is_complete(self):
        for opportunity in ASSISTANCE:
            self.assertTrue(opportunity.is_verified(), opportunity.opportunity_id)
            self.assertTrue(opportunity.official_url.startswith("https://"),
                            opportunity.opportunity_id)
            self.assertTrue(opportunity.required_documents, opportunity.opportunity_id)
            self.assertTrue(opportunity.application_steps, opportunity.opportunity_id)
            self.assertTrue(opportunity.disclaimer, opportunity.opportunity_id)
            self.assertNotEqual(opportunity.display_name("ur"), opportunity.name,
                                f"{opportunity.opportunity_id} has no Urdu name")
            self.assertNotEqual(opportunity.display_summary("ur"), opportunity.summary_en,
                                f"{opportunity.opportunity_id} has no Urdu summary")


if __name__ == "__main__":
    unittest.main()
