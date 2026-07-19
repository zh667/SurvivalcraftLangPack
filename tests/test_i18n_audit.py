import unittest

from tools.i18n_audit import audit_values, compare_string, flatten
from tools.i18n_repair import repair_string, restore_markup


class FlattenTests(unittest.TestCase):
    def test_nested_paths_are_stable(self):
        self.assertEqual(
            flatten({"Menu": {"Title": "Game"}, "Items": ["One", "Two"]}),
            {"Menu.Title": "Game", "Items[0]": "One", "Items[1]": "Two"},
        )


class StringAuditTests(unittest.TestCase):
    def categories(self, source, target):
        return {issue.category for issue in compare_string("Example", source, target)}

    def test_placeholder_damage_is_an_error(self):
        self.assertIn("placeholder_mismatch", self.categories("Hello {0}", "Bonjour format@@0"))

    def test_polluted_marker_is_an_error(self):
        self.assertIn("mt_marker_pollution", self.categories("Grass Trap", "Piège format@@0"))

    def test_missing_decimal_is_a_warning(self):
        self.assertIn("missing_numbers", self.categories("Output is 0.8V", "Sortie 0 V"))

    def test_identical_english_is_a_warning(self):
        self.assertIn("source_identical", self.categories("New Game", "New Game"))


class StructureAuditTests(unittest.TestCase):
    def test_missing_and_extra_keys_are_errors(self):
        result = audit_values({"A": "a", "B": "b"}, {"A": "a", "C": "c"}, "xx.json")
        categories = {issue.category for issue in result.errors}
        self.assertEqual(categories, {"missing_key", "extra_key"})

    def test_wrong_language_menu_name_is_an_error(self):
        result = audit_values(
            {"Language": {"Name": "English"}},
            {"Language": {"Name": "Anglais"}},
            "fr-FR.json",
        )
        self.assertIn("language_name_mismatch", {issue.category for issue in result.errors})


class RepairTests(unittest.TestCase):
    def test_marker_pollution_falls_back_to_source(self):
        repaired, reasons = repair_string("Grass Trap", "Piège format@@0")
        self.assertEqual(repaired, "Grass Trap")
        self.assertIn("mt_marker_fallback", reasons)

    def test_unknown_marker_is_restored_to_pipe(self):
        repaired, reasons = repair_string("Texture | {0}x{1}", "Texture <unk> {0}x{1}")
        self.assertEqual(repaired, "Texture | {0}x{1}")
        self.assertIn("separator_restored", reasons)

    def test_translated_markup_attributes_are_restored(self):
        repaired, changed = restore_markup(
            "<c=yellow>Title</c><br/>",
            "<c=kuning>Judul</c><br/>",
        )
        self.assertTrue(changed)
        self.assertEqual(repaired, "<c=yellow>Judul</c><br/>")

    def test_duplicate_closing_markup_is_removed(self):
        repaired, changed = restore_markup("<em>smile</em>", "<em>Lächeln</em></em>")
        self.assertTrue(changed)
        self.assertEqual(repaired, "<em>Lächeln</em>")


if __name__ == "__main__":
    unittest.main()
