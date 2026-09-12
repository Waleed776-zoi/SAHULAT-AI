"""
Tests for core/validation.py - the rules that decide whether a wizard step is
complete. Kept out of app.py precisely so they can be tested without Streamlit.
"""
import unittest

from core.i18n import validation_message
from core.models import UserProfile
from core.validation import (
    AGE_MAX, AGE_MIN, ERR_AGE_RANGE, ERR_INVALID_CHOICE, ERR_MARKS_RANGE,
    ERR_NO_CATEGORY, ERR_REQUIRED, EXPERIENCE_MAX, RESULTS_STEP_INDEX, STEPS,
    can_advance, completion_percent, first_incomplete_step, step_index,
    validate_field, validate_step,
)

FOCUS, ABOUT, EDUCATION, CIRCUMSTANCES = STEPS[0], STEPS[1], STEPS[2], STEPS[3]


class TestFieldValidation(unittest.TestCase):

    def test_unanswered_is_not_an_error(self):
        """Optional fields are genuinely optional - None is allowed here."""
        for field in ("age", "marks_percentage", "monthly_household_income",
                      "years_experience", "gender", "education_level"):
            with self.subTest(field=field):
                self.assertIsNone(validate_field(field, None))

    def test_age_bounds(self):
        self.assertEqual(validate_field("age", AGE_MIN - 1), ERR_AGE_RANGE)
        self.assertEqual(validate_field("age", AGE_MAX + 1), ERR_AGE_RANGE)
        self.assertIsNone(validate_field("age", AGE_MIN))
        self.assertIsNone(validate_field("age", AGE_MAX))

    def test_marks_bounds(self):
        self.assertEqual(validate_field("marks_percentage", -1), ERR_MARKS_RANGE)
        self.assertEqual(validate_field("marks_percentage", 101), ERR_MARKS_RANGE)
        self.assertIsNone(validate_field("marks_percentage", 0))
        self.assertIsNone(validate_field("marks_percentage", 100))

    def test_zero_income_and_zero_experience_are_valid(self):
        """BUG-03 again, at the validation layer this time."""
        self.assertIsNone(validate_field("monthly_household_income", 0))
        self.assertIsNone(validate_field("years_experience", 0))

    def test_experience_upper_bound(self):
        self.assertIsNotNone(validate_field("years_experience", EXPERIENCE_MAX + 1))

    def test_choice_fields_reject_unknown_values(self):
        self.assertEqual(validate_field("education_level", "phd"), ERR_INVALID_CHOICE)
        self.assertEqual(validate_field("gender", "yes"), ERR_INVALID_CHOICE)
        self.assertEqual(validate_field("english_level", "perfect"), ERR_INVALID_CHOICE)

    def test_choice_fields_accept_known_values(self):
        self.assertIsNone(validate_field("education_level", "bachelor"))
        self.assertIsNone(validate_field("english_level", "none"))
        self.assertIsNone(validate_field("computer_skills", "advanced"))
        self.assertIsNone(validate_field("domicile_province", "Punjab"))


class TestStepValidation(unittest.TestCase):

    def test_focus_step_needs_a_category(self):
        self.assertEqual(validate_step(FOCUS, UserProfile(), []),
                         {"categories": ERR_NO_CATEGORY})
        self.assertEqual(validate_step(FOCUS, UserProfile(), ["scholarship"]), {})

    def test_about_step_requires_age_and_domicile(self):
        errors = validate_step(ABOUT, UserProfile())
        self.assertEqual(errors["age"], ERR_REQUIRED)
        self.assertEqual(errors["domicile_province"], ERR_REQUIRED)

    def test_about_step_does_not_require_gender(self):
        errors = validate_step(ABOUT, UserProfile(age=25, domicile_province="Punjab"))
        self.assertEqual(errors, {})

    def test_about_step_rejects_impossible_age(self):
        errors = validate_step(ABOUT, UserProfile(age=3, domicile_province="Punjab"))
        self.assertEqual(errors["age"], ERR_AGE_RANGE)

    def test_education_step_requires_level_only(self):
        self.assertEqual(validate_step(EDUCATION, UserProfile())["education_level"],
                         ERR_REQUIRED)
        self.assertEqual(validate_step(EDUCATION, UserProfile(education_level="matric")), {})

    def test_education_step_rejects_bad_marks(self):
        errors = validate_step(EDUCATION,
                               UserProfile(education_level="matric", marks_percentage=140))
        self.assertEqual(errors["marks_percentage"], ERR_MARKS_RANGE)

    def test_circumstances_step_is_entirely_optional(self):
        self.assertEqual(validate_step(CIRCUMSTANCES, UserProfile()), {})

    def test_can_advance_mirrors_validate_step(self):
        self.assertFalse(can_advance(ABOUT, UserProfile()))
        self.assertTrue(can_advance(ABOUT, UserProfile(age=20, domicile_province="Sindh")))


class TestWizardNavigation(unittest.TestCase):

    def test_first_incomplete_step_walks_forward(self):
        empty = UserProfile()
        self.assertEqual(first_incomplete_step(empty, []), 0)
        self.assertEqual(first_incomplete_step(empty, ["scholarship"]), 1)

        partial = UserProfile(age=20, domicile_province="Punjab")
        self.assertEqual(first_incomplete_step(partial, ["scholarship"]), 2)

        complete = UserProfile(age=20, domicile_province="Punjab",
                               education_level="bachelor")
        self.assertEqual(first_incomplete_step(complete, ["scholarship"]),
                         RESULTS_STEP_INDEX)

    def test_step_keys_are_unique_and_ordered(self):
        keys = [s.key for s in STEPS]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(STEPS[RESULTS_STEP_INDEX].key, "results")

    def test_step_index_lookup(self):
        self.assertEqual(step_index("focus"), 0)
        self.assertEqual(step_index("results"), RESULTS_STEP_INDEX)
        self.assertEqual(step_index("nonexistent"), 0)

    def test_required_fields_are_a_subset_of_step_fields(self):
        for step in STEPS:
            with self.subTest(step=step.key):
                self.assertTrue(set(step.required_fields) <= set(step.fields))


class TestScreenability(unittest.TestCase):

    def test_profile_is_screenable_once_required_answered(self):
        self.assertFalse(UserProfile().is_screenable())
        self.assertTrue(UserProfile(age=20, domicile_province="Punjab",
                                    education_level="matric").is_screenable())

    def test_missing_required_fields_listed(self):
        self.assertEqual(UserProfile(age=20).missing_required_fields(),
                         ["domicile_province", "education_level"])

    def test_completion_percent(self):
        self.assertEqual(completion_percent(UserProfile()), 0)
        self.assertGreater(completion_percent(UserProfile(age=20, gender="female")), 0)


class TestValidationMessagesAreTranslated(unittest.TestCase):
    """I18N-02: validation emits codes; i18n renders them in both languages."""

    ALL_CODES = (ERR_REQUIRED, ERR_AGE_RANGE, ERR_MARKS_RANGE, ERR_NO_CATEGORY,
                 ERR_INVALID_CHOICE, "income_range", "experience_range")

    def test_every_code_renders_in_both_languages(self):
        for code in self.ALL_CODES:
            for language in ("en", "ur"):
                with self.subTest(code=code, lang=language):
                    message = validation_message(code, language)
                    self.assertTrue(message)
                    self.assertFalse(message.startswith("err_"),
                                     f"missing string for {code}/{language}")

    def test_age_message_names_the_real_bounds(self):
        message = validation_message(ERR_AGE_RANGE, "en")
        self.assertIn(str(AGE_MIN), message)
        self.assertIn(str(AGE_MAX), message)


if __name__ == "__main__":
    unittest.main()
