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
        (self.root / "literature" / "dune.json").write_text(
            json.dumps(
                [
                    {"title": "Chapter 1", "content": "line 1"},
                ]
            ),
            encoding="utf-8",
        )
        result = self.run_script("--list-unread")

        self.assertEqual(result.returncode, 0)
        self.assertIn("dune.json: 1 unread chapter (all chapters)", result.stdout)

        settings = json.loads((self.root / "settings.json").read_text(encoding="utf-8"))
        literature = json.loads((self.root / "literature.json").read_text(encoding="utf-8"))
        self.assertEqual(settings, {})
        self.assertEqual(literature["books"]["dune.json"]["total_chapters"], 1)

    def test_list_unread_returns_one_when_no_unread_books_exist(self) -> None:
        (self.root / "literature.json").write_text(
            json.dumps(
                {
                    "books": {
                        "done.json": {
                            "total_chapters": 1,
                            "chapters": {"0": {"read": True}},
                            "meta_note": None,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        (self.root / "literature" / "done.json").write_text(
            json.dumps([{"title": "Only", "content": "a"}]),
            encoding="utf-8",
        )

        result = self.run_script("--list-unread")

        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")

    def test_read_shows_previous_notes_and_meta_note_prompt(self) -> None:
        (self.root / "literature" / "book.json").write_text(
            json.dumps(
                [
                    {"title": "Intro", "content": "first"},
                    {"title": "Final", "content": "second"},
                ]
            ),
            encoding="utf-8",
        )
        (self.root / "literature.json").write_text(
            json.dumps(
                {
                    "books": {
                        "book.json": {
                            "total_chapters": 2,
                            "chapters": {
                                "0": {"read": True, "notes": "note for chapter zero"},
                            },
                            "meta_note": None,
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        result = self.run_script("--read", "book.json")

        self.assertEqual(result.returncode, 0)
        self.assertIn("=== Previous Chapter Notes (Chapter 0) ===", result.stdout)
        self.assertIn("note for chapter zero", result.stdout)
        self.assertIn("=== Chapter 1: Final ===", result.stdout)
        self.assertIn("second", result.stdout)
        self.assertIn(
            "[This is the final chapter. Write a meta-note synthesizing your understanding of the book.]",
            result.stdout,
        )

    def test_read_specific_chapter_validates_range(self) -> None:
        (self.root / "literature" / "book.json").write_text(
            json.dumps([{"title": "Only", "content": "a"}]),
            encoding="utf-8",
        )

        result = self.run_script("--read", "book.json", "--chapter", "9")

        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid chapter_index 9", result.stderr)

    def test_write_note_persists_notes_and_marks_chapter_read(self) -> None:
        (self.root / "literature" / "dune.json").write_text(
            json.dumps(
                [
                    {"title": "One", "content": "line 1"},
                    {"title": "Two", "content": "line 2"},
                ]
            ),
            encoding="utf-8",
        )

        result = self.run_script(
            "--write-note",
            "dune.json",
            "1",
            "--text",
            "Block one notes",
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Notes saved for chapter 1 of dune.json", result.stdout)

        literature = json.loads((self.root / "literature.json").read_text(encoding="utf-8"))
        self.assertEqual(
            literature["books"]["dune.json"]["chapters"]["1"]["notes"],
            "Block one notes",
        )
        self.assertTrue(literature["books"]["dune.json"]["chapters"]["1"]["read"])
        self.assertEqual(literature["books"]["dune.json"]["total_chapters"], 2)

    def test_write_meta_note_persists_message(self) -> None:
        (self.root / "literature" / "dune.json").write_text(
            json.dumps([{"title": "Only", "content": "text"}]),
            encoding="utf-8",
        )

        result = self.run_script(
            "--write-meta-note",
            "dune.json",
            "--text",
            "Synthesis for blocks two and three",
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Meta-note saved for dune.json", result.stdout)

        literature = json.loads((self.root / "literature.json").read_text(encoding="utf-8"))
        self.assertEqual(
            literature["books"]["dune.json"]["meta_note"],
            "Synthesis for blocks two and three",
        )

    def test_write_note_requires_text(self) -> None:
        (self.root / "literature" / "dune.json").write_text(
            json.dumps([{"title": "Only", "content": "line 1"}]),
            encoding="utf-8",
        )

        result = self.run_script("--write-note", "dune.json", "0")

        self.assertEqual(result.returncode, 1)
        self.assertIn("--text is required for --write-note", result.stderr)

    def test_write_note_validates_missing_file(self) -> None:
        result = self.run_script(
            "--write-note",
            "missing.json",
            "0",
            "--text",
            "notes",
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("literature file not found: missing.txt", result.stderr)

    def test_write_operations_fail_on_invalid_literature_json(self) -> None:
        (self.root / "literature" / "dune.json").write_text(
            json.dumps([{"title": "Only", "content": "line 1"}]),
            encoding="utf-8",
        )
        (self.root / "literature.json").write_text("{not json", encoding="utf-8")

        result = self.run_script(
            "--write-note",
            "dune.json",
            "0",
            "--text",
            "notes",
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid JSON in literature.json", result.stderr)


if __name__ == "__main__":
    unittest.main()
