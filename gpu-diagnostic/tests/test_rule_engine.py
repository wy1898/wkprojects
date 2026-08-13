from __future__ import annotations

import unittest

from gpu_diagnostic.analyzer.rule_engine import RuleEngine


class RuleLibraryTests(unittest.TestCase):
    def test_rule_library_loads_structured_rules(self) -> None:
        rules = RuleEngine().rules
        self.assertGreaterEqual(len(rules), 10)
        self.assertEqual(rules["xid_79"]["id"], "xid_79")
        self.assertEqual(rules["xid_79"]["category"], ["PCIe", "Hardware"])
        self.assertIn("match_conditions", rules["driver_communication_failure"])


if __name__ == "__main__":
    unittest.main()
