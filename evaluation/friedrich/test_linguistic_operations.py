from __future__ import annotations

from pathlib import Path
import unittest

from .linguistic_operations import LinguisticOperationExtractor


class LinguisticOperationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.extractor = LinguisticOperationExtractor(
            Path("/private/tmp/friedrich-nltk-data")
        )

    def test_unique_wordnet_derivations_are_canonicalized(self) -> None:
        expected = {
            "confirmation of dismissal": ("confirm", "dismissal"),
            "rejection of dismissal": ("reject", "dismissal"),
            "registration of request": ("register", "request"),
            "examination of application": ("examine", "application"),
        }
        for label, (operation, object_phrase) in expected.items():
            with self.subTest(label=label):
                result = self.extractor.extract(label)
                self.assertTrue(result.operation_resolved)
                self.assertEqual(result.canonical_operation, operation)
                self.assertEqual(result.object_phrase, object_phrase)
                self.assertEqual(
                    result.derivation_source, "wordnet_unique_derivational_verb"
                )

    def test_missing_wordnet_derivation_is_not_guessed(self) -> None:
        result = self.extractor.extract("deregistration of employee")
        self.assertFalse(result.operation_resolved)
        self.assertEqual(result.canonical_operation, "deregistration")
        self.assertEqual(result.derivation_source, "wordnet_no_derivational_verb")

    def test_actor_led_fragment_uses_predicate(self) -> None:
        result = self.extractor.extract("go informs applicant about the assignment")
        self.assertEqual(result.canonical_operation, "inform")
        self.assertEqual(result.object_phrase, "applicant about the assignment")


if __name__ == "__main__":
    unittest.main()
