import csv
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SUPPLIED_HASHES = {
    "generate_data.py": "e5bd939dfa40402281d0285bdf755d3b75f42159265d78098e248e58683de6cd",
    "mock_llm.py": "77bf9bb7cb96e67f49d808cb2e84befb0e5a346833cd508df924437b606905b6",
}

REQUIRED_HEADINGS = [
    "## Overview",
    "## Reproduce",
    "## Part A",
    "## Part B",
    "## Part C",
    "## Part D",
    "## Limitations and Next Steps",
]


class SetupTests(unittest.TestCase):
    def test_supplied_files_are_unmodified(self):
        for name, expected in SUPPLIED_HASHES.items():
            digest = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            self.assertEqual(digest, expected, name)

    def test_raw_data_counts(self):
        expected = {
            "customers.csv": 1200,
            "products.csv": 40,
            "orders.csv": 13084,
            "tickets.csv": 164,
        }
        for name, count in expected.items():
            with (ROOT / "data" / "raw" / name).open(encoding="utf-8", newline="") as handle:
                self.assertEqual(len(list(csv.reader(handle))) - 1, count, name)

    def test_policy_documents_exist(self):
        names = {
            "refund_policy.txt",
            "delivery_policy.txt",
            "payment_policy.txt",
            "privacy_policy.txt",
            "escalation_policy.txt",
        }
        found = {path.name for path in (ROOT / "data" / "policies").glob("*.txt")}
        self.assertEqual(found, names)

    def test_readme_section_order(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        positions = [text.find(heading) for heading in REQUIRED_HEADINGS]
        self.assertNotIn(-1, positions)
        self.assertEqual(positions, sorted(positions))

    def test_mock_llm_interface(self):
        import mock_llm

        mock_llm.reset()
        response = mock_llm.chat(
            [
                {"role": "system", "content": "CLASSIFY this ticket."},
                {"role": "user", "content": "I was charged twice for my order."},
            ]
        )
        self.assertIn("billing", response.choices[0].message.content)
        self.assertGreater(response.usage.total_tokens, 0)


if __name__ == "__main__":
    unittest.main()
