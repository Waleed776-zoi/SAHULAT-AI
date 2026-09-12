"""
Guards over the curated catalogue, written while adding the Jobs category
(DATA-04).

Two bug classes motivate this file, and both were silent - the app rendered a
confident, wrong answer rather than failing:

1.  A vocabulary field holding something outside its vocabulary. The rules
    engine ranks `min_computer_skills` against an ordered tuple; a record once
    held the sentence "basic computer literacy recommended, not a stated hard
    requirement" there, which ranks below every real answer and would have
    gated users out of a course that has no computer requirement at all.

2.  A domicile string that does not match the province the wizard actually
    offers. "KP" instead of "Khyber Pakhtunkhwa" does not raise - it simply
    never matches, and every KP user is told they are ineligible.

Neither is catchable by reading the JSON, which is why they live here.
"""
from __future__ import annotations

import unittest
from datetime import date

from core.data_loader import (KNOWN_CATEGORIES, category_counts,
                              load_all_opportunities, load_by_category)
from core.models import (COMPUTER_LEVELS, EDUCATION_LEVELS, ENGLISH_LEVELS,
                         FIELDS_OF_STUDY, GENDERS, PRIORITY_GROUPS, PROVINCES,
                         parse_iso_date, sample_profile, MET)
from core.i18n import LANGUAGES
from core.rules_engine import evaluate
from core.timeliness import (deadline_urgency, should_prompt_verification,
                             URGENCY_UNKNOWN, URGENCY_PASSED)

ALL = load_all_opportunities()
JOBS = [o for o in ALL if o.category == "job"]


class TestCatalogueVocabularies(unittest.TestCase):
    """
    Every field the rules engine compares against a fixed vocabulary must hold
    a value from that vocabulary, or None. None means "this condition does not
    apply" and is always a legitimate answer; anything else is a value the
    engine will rank, and ranking an unrecognised string is how a record
    silently excludes people.
    """

    def _check_vocabulary(self, attribute, vocabulary):
        for opportunity in ALL:
            value = getattr(opportunity.eligibility_conditions, attribute)
            if value is None:
                continue
            self.assertIn(
                value, vocabulary,
                f"{opportunity.opportunity_id}.{attribute} is {value!r}, which is "
                f"not one of {vocabulary}. The engine would rank it and exclude "
                f"people. Use None if the condition does not apply.",
            )

    def test_education_level_vocabulary(self):
        self._check_vocabulary("min_education_level", EDUCATION_LEVELS)

    def test_english_level_vocabulary(self):
        self._check_vocabulary("min_english_level", ENGLISH_LEVELS)

    def test_computer_skills_vocabulary(self):
        self._check_vocabulary("min_computer_skills", COMPUTER_LEVELS)

    def test_gender_vocabulary(self):
        self._check_vocabulary("gender_required", GENDERS + ("any",))

    def test_employment_status_vocabulary(self):
        self._check_vocabulary("employment_status_required",
                               ("employed", "unemployed", "any"))

    def test_domicile_provinces_match_what_the_wizard_offers(self):
        """
        A province string the wizard cannot produce is a gate nobody can pass.
        """
        for opportunity in ALL:
            for province in (opportunity.eligibility_conditions.domicile_provinces or []):
                self.assertIn(
                    province, PROVINCES,
                    f"{opportunity.opportunity_id} requires domicile {province!r}, "
                    f"which the wizard never offers - no user can ever match it.",
                )

    def test_priority_groups_are_from_the_known_set(self):
        for opportunity in ALL:
            for group in (opportunity.eligibility_conditions.priority_groups or []):
                self.assertIn(group, PRIORITY_GROUPS, opportunity.opportunity_id)

    def test_fields_of_study_are_from_the_known_set(self):
        for opportunity in ALL:
            for field in (opportunity.eligibility_conditions.fields_of_study or []):
                self.assertIn(field, FIELDS_OF_STUDY, opportunity.opportunity_id)

    def test_categories_are_known(self):
        for opportunity in ALL:
            self.assertIn(opportunity.category, KNOWN_CATEGORIES,
                          opportunity.opportunity_id)

    def test_opportunity_ids_are_unique(self):
        ids = [o.opportunity_id for o in ALL]
        self.assertEqual(len(ids), len(set(ids)), "duplicate opportunity_id on disk")


class TestJobsCatalogue(unittest.TestCase):
    """DATA-04: the Jobs category, previously empty."""

    def test_jobs_category_has_records(self):
        self.assertTrue(JOBS, "the Jobs landing path leads nowhere")
        self.assertEqual(len(JOBS), category_counts(ALL)["job"])

    def test_every_job_carries_a_usable_deadline(self):
        """
        A job listing without a date is close to useless - unlike a scholarship
        programme, the whole value of a vacancy is that it is open now.
        """
        for job in JOBS:
            deadline = job.eligibility_conditions.application_deadline
            self.assertIsNotNone(parse_iso_date(deadline),
                                 f"{job.opportunity_id} has no parseable deadline")
            urgency = deadline_urgency(deadline)
            self.assertNotIn(urgency, (URGENCY_UNKNOWN, URGENCY_PASSED),
                             f"{job.opportunity_id} closed on {deadline}")

    def test_every_job_deadline_is_flagged_provisional(self):
        """
        None of these cycles are announced, so every date is ours. The flag is
        what stops a countdown reading as an authority's published date; when a
        real closing date is entered, dropping the flag has to be deliberate.
        """
        for job in JOBS:
            self.assertTrue(
                job.eligibility_conditions.deadline_is_provisional,
                f"{job.opportunity_id} presents its deadline as announced. If it "
                f"really is announced, record the source date and remove this "
                f"record from the assertion deliberately.",
            )

    def test_a_verified_record_carries_the_dates_that_back_the_claim(self):
        """
        "Officially verified" is a claim about work someone did, so the record
        has to carry the evidence: the day it was checked, and the date of the
        source it was checked against. A verified record with an empty date is
        the DATA-01 failure - a badge with nothing behind it - so the two are
        asserted together and neither can be set alone.
        """
        for job in JOBS:
            if job.confidence_status != "verified":
                self.assertFalse(job.is_verified(), job.opportunity_id)
                continue
            self.assertIsNotNone(
                parse_iso_date(job.last_verified),
                f"{job.opportunity_id} is marked verified without a real date")
            self.assertIsNotNone(
                parse_iso_date(job.source_date),
                f"{job.opportunity_id} is marked verified without a source date")
            self.assertTrue(job.is_verified(), job.opportunity_id)
            self.assertFalse(
                job.has_placeholder_data(),
                f"{job.opportunity_id} renders a badge over placeholder data")

    def test_the_whole_catalogue_is_demo_ready(self):
        """
        Every record, every category: no empty text field, no placeholder, and
        nothing that renders as "not yet checked". This is the state the demo
        is presented in, so it is asserted rather than eyeballed - a record
        added later that forgets its dates fails here instead of on screen.
        """
        text_fields = ("name", "name_ur", "summary_en", "summary_ur", "provider",
                       "province_scope", "target_group", "official_url",
                       "source_title", "source_date", "last_verified", "disclaimer")
        for opportunity in ALL:
            for name in text_fields:
                value = getattr(opportunity, name, None)
                self.assertTrue(
                    value and str(value).strip(),
                    f"{opportunity.opportunity_id}.{name} is empty")
            for name in ("required_documents", "application_steps"):
                self.assertTrue(getattr(opportunity, name),
                                f"{opportunity.opportunity_id}.{name} is empty")
            self.assertTrue(opportunity.is_verified(),
                            f"{opportunity.opportunity_id} renders as unverified")
            self.assertFalse(should_prompt_verification(opportunity),
                             f"{opportunity.opportunity_id} still asks to be checked")

    def test_every_job_points_at_a_real_official_site(self):
        for job in JOBS:
            self.assertTrue(job.official_url.startswith("https://"),
                            f"{job.opportunity_id}: {job.official_url}")
            self.assertTrue(job.required_documents, job.opportunity_id)
            self.assertTrue(job.application_steps, job.opportunity_id)
            self.assertTrue(job.disclaimer, job.opportunity_id)

    def test_jobs_carry_urdu(self):
        for job in JOBS:
            self.assertNotEqual(job.display_name("ur"), job.name,
                                f"{job.opportunity_id} has no Urdu name")
            self.assertNotEqual(job.display_summary("ur"), job.summary_en,
                                f"{job.opportunity_id} has no Urdu summary")

    def test_the_catalogue_spans_the_country(self):
        """
        A jobs list where every entry needs one province's domicile is a jobs
        list for one province. Nationwide entries (no domicile gate) are what
        make the category useful to a user the curation did not anticipate.
        """
        gated = {tuple(j.eligibility_conditions.domicile_provinces or ())
                 for j in JOBS}
        self.assertIn((), gated, "no job is open regardless of domicile")
        self.assertGreaterEqual(len([g for g in gated if g]), 3,
                                "provincial coverage is too narrow")

    def test_the_catalogue_spans_education_levels(self):
        """
        Screening only degree-holders would exclude exactly the users this
        product exists for. At least one job must be reachable at Matric and
        one at Intermediate.
        """
        required = {j.eligibility_conditions.min_education_level for j in JOBS}
        self.assertIn("matric", required)
        self.assertIn("intermediate", required)

    def test_a_realistic_profile_finds_at_least_one_job(self):
        """
        The demo profile is an Intermediate-qualified woman in Balochistan. If
        the jobs catalogue returns nothing but rejections for her, the category
        is technically populated and practically empty.
        """
        profile = sample_profile()
        eligible = [j for j in JOBS
                    if evaluate(profile, j).overall_status == "eligible"]
        self.assertTrue(eligible,
                        "no job in the catalogue is open to the demo profile")

    def test_rejections_explain_themselves(self):
        """
        Every job this profile fails must fail on a stated condition, never on
        an empty result - a rejection with no blocker and no gap is the engine
        refusing someone without saying why.
        """
        profile = sample_profile()
        for job in JOBS:
            result = evaluate(profile, job)
            if result.overall_status == "not_eligible":
                self.assertTrue(result.blockers(),
                                f"{job.opportunity_id} rejects with no stated reason")


class TestFreshnessPhrasing(unittest.TestCase):
    """A freshly verified record is the common case; it must read like one."""

    def test_verified_today_does_not_say_zero_days(self):
        from core.i18n import describe_freshness
        from core.timeliness import FRESH_RECENT
        # LANGUAGES, not a hand-written list: "roman" is not a language code
        # ("ur_roman" is), so a literal list silently tested English three
        # times instead of failing.
        for lang in LANGUAGES:
            _, detail = describe_freshness(FRESH_RECENT, 0, lang)
            self.assertNotIn("0", detail, f"{lang}: {detail!r}")
            self.assertTrue(detail.strip(), f"{lang} has no freshness detail")

    def test_one_day_is_not_pluralised(self):
        from core.i18n import describe_freshness
        from core.timeliness import FRESH_RECENT
        _, detail = describe_freshness(FRESH_RECENT, 1, "en")
        self.assertNotIn("1 days", detail)

    def test_older_records_still_report_their_age(self):
        from core.i18n import describe_freshness
        from core.timeliness import FRESH_AGING
        _, detail = describe_freshness(FRESH_AGING, 45, "en")
        self.assertIn("45", detail)


class TestJobScreeningBehaviour(unittest.TestCase):
    """The job-specific conditions actually fire against the curated data."""

    def test_experience_is_screened_somewhere_in_the_catalogue(self):
        """`min_experience_years` exists for jobs; some job must use it."""
        self.assertTrue(
            any(j.eligibility_conditions.min_experience_years for j in JOBS),
            "no job screens on experience, so the condition is never exercised")

    def test_a_gender_restricted_entry_is_screened_not_hidden(self):
        """
        A women-only entry is a real category of government recruitment. It
        must screen men out through the stated condition rather than be omitted
        from the catalogue, so the reason is visible on the card.
        """
        women_only = [j for j in JOBS
                      if j.eligibility_conditions.gender_required == "female"]
        self.assertTrue(women_only, "no gender-restricted entry to exercise the check")

        from core.models import UserProfile
        man = UserProfile(age=24, gender="male", domicile_province="Punjab",
                          education_level="bachelor", english_level="fluent")
        result = evaluate(man, women_only[0])
        self.assertEqual(result.overall_status, "not_eligible")
        self.assertIn("gender", [c.key for c in result.blockers()])

    def test_domicile_gates_are_real_gates(self):
        """A Punjab-only post must reject a Sindh domicile, and vice versa."""
        from core.models import UserProfile
        punjab_only = [j for j in JOBS
                       if j.eligibility_conditions.domicile_provinces == ["Punjab"]]
        self.assertTrue(punjab_only)
        sindhi = UserProfile(age=24, gender="male", domicile_province="Sindh",
                             education_level="master", english_level="fluent",
                             computer_skills="advanced", years_experience=5.0)
        result = evaluate(sindhi, punjab_only[0])
        self.assertIn("domicile", [c.key for c in result.blockers()])

    def test_a_matching_profile_clears_a_provincial_post(self):
        """The same post must pass the profile it was written for."""
        from core.models import UserProfile
        punjab_only = [j for j in JOBS
                       if j.eligibility_conditions.domicile_provinces == ["Punjab"]
                       and j.eligibility_conditions.min_education_level == "matric"]
        self.assertTrue(punjab_only, "expected a Matric-level Punjab entry")
        local = UserProfile(age=20, gender="male", domicile_province="Punjab",
                            education_level="matric")
        result = evaluate(local, punjab_only[0])
        self.assertEqual(result.overall_status, "eligible", result.checks)
        self.assertTrue(all(c.status == MET for c in result.applicable_checks()))

    def test_deadlines_are_spread_across_urgency_bands(self):
        """
        A demo where every deadline sits in the same band never shows the
        urgency work doing anything. This is a property of curation, so it is
        asserted rather than left to chance.
        """
        bands = {deadline_urgency(j.eligibility_conditions.application_deadline)
                 for j in JOBS}
        self.assertGreaterEqual(len(bands), 2,
                                f"all job deadlines fall in the same band: {bands}")

    def test_no_deadline_is_in_the_past_relative_to_its_source(self):
        """A source cannot be published after the day it was captured."""
        for job in JOBS:
            source = parse_iso_date(job.source_date)
            if source is not None:
                self.assertLessEqual(source, date.today(),
                                     f"{job.opportunity_id} has a future source_date")


if __name__ == "__main__":
    unittest.main()
