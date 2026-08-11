import tempfile
import unittest
from pathlib import Path

from app import discover_properties, sort_risk_flags


class AppHelpersTests(unittest.TestCase):
    def test_discover_properties_returns_property_subfolders(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "properties").mkdir()
            (root / "properties" / "Alpha").mkdir()
            (root / "properties" / "Beta").mkdir()
            (root / "properties" / "notes.txt").write_text("ignore", encoding="utf-8")

            properties = discover_properties(root / "properties")

            self.assertEqual(properties, ["Alpha", "Beta"])

    def test_sort_risk_flags_prioritizes_high_and_medium(self) -> None:
        flags = [
            {"flag": "A", "severity": "low"},
            {"flag": "B", "severity": "high"},
            {"flag": "C", "severity": "medium"},
        ]

        sorted_flags = sort_risk_flags(flags)

        self.assertEqual([item["flag"] for item in sorted_flags], ["B", "C", "A"])


if __name__ == "__main__":
    unittest.main()
