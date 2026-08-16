from __future__ import annotations

from . import validate_revised_action_matching_untouched as runner


FINAL_VALIDATION_CASES = {
    "9-3": "sequential process from the BPMN modeling reference guide",
    "6-1": "nested decision and loop in the ACME process",
    "2-1": "nested decision process for SLA violation handling",
    "9-4": "second sequential process from the BPMN modeling reference guide",
    "5-3": "nested decision process from a vendor tutorial",
}

ALL_PRIOR_CASES = frozenset(
    {
        "6-2", "5-2", "3-3", "6-3", "9-6", "4-1", "9-5",
        "3-1", "3-4", "8-2", "10-7", "1-2",
        "3-2", "3-6", "5-4", "10-6", "10-8",
        "8-1", "1-1", "2-2", "3-8", "10-9",
    }
)


def main() -> None:
    if set(FINAL_VALIDATION_CASES) & ALL_PRIOR_CASES:
        raise ValueError("Final untouched sample overlaps prior evaluation cases")
    runner.VALIDATION_CASES = FINAL_VALIDATION_CASES
    runner.EXCLUDED_CASES = ALL_PRIOR_CASES
    runner.main()


if __name__ == "__main__":
    main()
