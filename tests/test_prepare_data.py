import unittest
from decimal import Decimal

from python.prepare_data import (
    is_cross_sheet_overlap,
    is_missing,
    is_non_product_code,
    line_revenue,
    normalize_description,
)


class PrepareDataTests(unittest.TestCase):
    def test_missing_values_include_blank_strings(self):
        self.assertTrue(is_missing(None))
        self.assertTrue(is_missing("   "))
        self.assertFalse(is_missing("0"))

    def test_line_revenue_uses_decimal_arithmetic(self):
        self.assertEqual(Decimal(line_revenue(3, 0.1)), Decimal("0.3"))

    def test_description_is_trimmed_without_changing_non_strings(self):
        self.assertEqual(normalize_description("  WHITE CHERRY LIGHTS  "), "WHITE CHERRY LIGHTS")
        self.assertIsNone(normalize_description(None))

    def test_manual_fee_test_and_voucher_codes_are_flagged(self):
        for code in ("POST", "CRUK", "TEST001", "TEST002", "gift_0001_10", "gift_0001_80"):
            with self.subTest(code=code):
                self.assertTrue(is_non_product_code(code))

    def test_letter_suffixed_product_codes_are_not_blanket_flagged(self):
        for code in ("85123A", "85099B", "15056BL"):
            with self.subTest(code=code):
                self.assertFalse(is_non_product_code(code))

    def test_only_overlap_multiplicity_is_removed(self):
        # Earlier sheet has two identical rows: remove the first two matching
        # rows from the later sheet, but preserve any additional later repeats.
        self.assertTrue(is_cross_sheet_overlap(1, 2))
        self.assertTrue(is_cross_sheet_overlap(2, 2))
        self.assertFalse(is_cross_sheet_overlap(3, 2))
        self.assertFalse(is_cross_sheet_overlap(1, 0))


if __name__ == "__main__":
    unittest.main()
