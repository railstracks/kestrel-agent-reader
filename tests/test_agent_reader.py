import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_NAME = "agent-reader.py"


class AgentReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "literature").mkdir()
        (self.root / SCRIPT_NAME).write_text(
            (PROJECT_ROOT / SCRIPT_NAME).read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, SCRIPT_NAME, *args],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_list_unread_creates_defaults_and_lists_books(self) -> None:
        (self.root / "literature" / "dune.txt").write_text(
            "line 1\nline 2\nline 3\n",
            encoding="utf-8",
        )
        result = self.run_script("--list-unread")

        self.assertEqual(result.returncode, 0)
        self.assertIn("dune.txt: 1 unread block (all blocks)", result.stdout)

        settings = json.loads((self.root / "settings.json").read_text(encoding="utf-8"))
        literature = json.loads((self.root / "literature.json").read_text(encoding="utf-8"))
        self.assertEqual(settings["block_size"], 200)
        self.assertEqual(settings["metanote_frequency"], 10)
        self.assertEqual(literature["books"]["dune.txt"]["total_lines"], 3)
        self.assertEqual(literature["books"]["dune.txt"]["total_blocks"], 1)

    def test_list_unread_returns_one_when_no_unread_books_exist(self) -> None:
        (self.root / "literature.json").write_text(
            json.dumps(
                {
                    "books": {
                        "done.txt": {
                            "total_blocks": 1,
                            "total_lines": 2,
                            "blocks": {"0": {"read": True}},
                            "meta_notes": {},
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        (self.root / "literature" / "done.txt").write_text("a\nb\n", encoding="utf-8")

        result = self.run_script("--list-unread")

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")

    def test_read_shows_previous_notes_and_meta_note_reminder(self) -> None:
        (self.root / "settings.json").write_text(
            json.dumps({"block_size": 2, "metanote_frequency": 2}),
            encoding="utf-8",
        )
        (self.root / "literature" / "book.txt").write_text(
            "a\nb\nc\nd\ne\n",
            encoding="utf-8",
        )
        (self.root / "literature.json").write_text(
            json.dumps(
                {
                    "books": {
                        "book.txt": {
                            "total_blocks": 3,
                            "total_lines": 5,
                            "blocks": {
                                "0": {"read": True, "notes": "note for block zero"},
                            },
                            "meta_notes": {},
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        result = self.run_script("--read", "book.txt")

        self.assertEqual(result.returncode, 0)
        self.assertIn("=== Previous Block Notes (Block 0) ===", result.stdout)
        self.assertIn("note for block zero", result.stdout)
        self.assertIn("=== Block 1 of 3: book.txt ===", result.stdout)
        self.assertIn("c\nd", result.stdout)
        self.assertIn("[Meta-note due: this is block 1, metanote_frequency is 2]", result.stdout)

    def test_read_specific_block_validates_range(self) -> None:
        (self.root / "literature" / "book.txt").write_text("a\n", encoding="utf-8")

        result = self.run_script("--read", "book.txt", "--block", "9")

        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid block number 9", result.stderr)


if __name__ == "__main__":
    unittest.main()
