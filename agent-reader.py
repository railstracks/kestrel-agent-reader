#!/usr/bin/env python3
import argparse
import json
import sys
import tempfile
from pathlib import Path


DEFAULT_SETTINGS: dict = {}
DEFAULT_LIBRARY = {"books": {}}


def atomic_write_json(path: Path, data: dict) -> None:
    json.loads(json.dumps(data))
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_path = Path(handle.name)
    temp_path.replace(path)


def load_json_file(path: Path, default_data: dict) -> dict:
    if not path.exists():
        atomic_write_json(path, default_data)
        return dict(default_data)

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        atomic_write_json(path, default_data)
        return dict(default_data)

    if not isinstance(data, dict):
        atomic_write_json(path, default_data)
        return dict(default_data)

    return data


def load_settings(root: Path) -> dict:
    data = load_json_file(root / "settings.json", DEFAULT_SETTINGS)
    if not isinstance(data, dict):
        data = {}
    changed = False
    for key in ("block_size", "metanote_frequency"):
        if key in data:
            del data[key]
            changed = True
    if changed:
        atomic_write_json(root / "settings.json", data)
    return data


def load_library(root: Path) -> dict:
    path = root / "literature.json"
    if not path.exists():
        atomic_write_json(path, DEFAULT_LIBRARY)
        return dict(DEFAULT_LIBRARY)

    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Error: invalid JSON in literature.json") from exc

    if not isinstance(data, dict):
        raise ValueError("Error: invalid JSON in literature.json")

    books = data.get("books")
    if not isinstance(books, dict):
        raise ValueError("Error: invalid JSON in literature.json")
    return data


def save_library(root: Path, library: dict) -> None:
    atomic_write_json(root / "literature.json", library)


def load_chapters(file_path: Path) -> list[dict]:
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"Error: invalid JSON in {file_path.name}; expected an array of chapters"
        ) from exc

    if not isinstance(data, list):
        raise ValueError(
            f"Error: {file_path.name} must be a JSON array of chapters"
        )

    for index, chapter in enumerate(data):
        if not isinstance(chapter, dict):
            raise ValueError(
                f"Error: {file_path.name} chapter {index} must be an object"
            )
        title = chapter.get("title")
        content = chapter.get("content")
        if not isinstance(title, str) or not isinstance(content, str):
            raise ValueError(
                f"Error: {file_path.name} chapter {index} must have title/content strings"
            )
    return data


def ensure_book_metadata(library: dict, filename: str, total_chapters: int) -> tuple[dict, bool]:
    books = library.setdefault("books", {})
    book = books.get(filename)
    changed = False

    if not isinstance(book, dict):
        book = {}
        books[filename] = book
        changed = True

    if "chapters" not in book and isinstance(book.get("blocks"), dict):
        book["chapters"] = book["blocks"]
        changed = True

    if "meta_note" not in book and isinstance(book.get("meta_notes"), dict):
        meta_note_value = None
        meta_notes = book.get("meta_notes") or {}
        if isinstance(meta_notes, dict) and meta_notes:
            candidates: list[tuple[int, str]] = []
            for key, value in meta_notes.items():
                try:
                    index = int(key)
                except (TypeError, ValueError):
                    continue
                if isinstance(value, str):
                    candidates.append((index, value))
            if candidates:
                meta_note_value = sorted(candidates)[-1][1]
        book["meta_note"] = meta_note_value
        changed = True

    if not isinstance(book.get("chapters"), dict):
        book["chapters"] = {}
        changed = True

    meta_note = book.get("meta_note")
    if meta_note is not None and not isinstance(meta_note, str):
        book["meta_note"] = None
        changed = True

    if book.get("total_chapters") != total_chapters:
        book["total_chapters"] = total_chapters
        changed = True

    for key in ("blocks", "meta_notes", "total_blocks", "total_lines"):
        if key in book:
            del book[key]
            changed = True

    return book, changed


def get_literature_files(root: Path) -> list[Path]:
    literature_dir = root / "literature"
    literature_dir.mkdir(exist_ok=True)
    return sorted(
        path for path in literature_dir.iterdir() if path.is_file() and path.suffix == ".json"
    )


def get_unread_chapters(book: dict) -> list[int]:
    total_chapters = book.get("total_chapters", 0)
    chapters = book.get("chapters", {})
    unread = []
    for index in range(total_chapters):
        chapter_data = chapters.get(str(index), {})
        if not isinstance(chapter_data, dict) or chapter_data.get("read") is not True:
            unread.append(index)
    return unread


def list_unread(root: Path, library: dict) -> int:
    lines_out = []
    changed = False

    for file_path in get_literature_files(root):
        try:
            chapters = load_chapters(file_path)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1

        book, book_changed = ensure_book_metadata(
            library, file_path.name, len(chapters)
        )
        changed = changed or book_changed
        unread = get_unread_chapters(book)
        if not unread:
            continue
        total_chapters = book["total_chapters"]
        if len(unread) == total_chapters:
            detail = "all chapters"
        else:
            detail = f"chapters {unread[0]}-{unread[-1]} of {total_chapters}"
        label = "chapter" if len(unread) == 1 else "chapters"
        lines_out.append(
            f"{file_path.name}: {len(unread)} unread {label} ({detail})"
        )

    if changed:
        save_library(root, library)

    if lines_out:
        print("\n".join(lines_out))
        return 0
    return 1


def resolve_chapter_index(book: dict, requested_chapter: int | None) -> int | None:
    if requested_chapter is not None:
        return requested_chapter
    unread = get_unread_chapters(book)
    if unread:
        return unread[0]
    return None


def validate_chapter_index(book: dict, chapter_index: int, filename: str) -> str | None:
    total_chapters = book.get("total_chapters", 0)
    if not isinstance(chapter_index, int) or chapter_index < 0 or chapter_index >= total_chapters:
        if total_chapters <= 0:
            return f"Error: {filename} has no readable chapters"
        return (
            f"Error: invalid chapter_index {chapter_index} for {filename}; "
            f"valid range is 0 to {total_chapters - 1}"
        )
    return None


def print_read_output(
    chapter: dict, book: dict, chapter_index: int
) -> None:
    previous_notes = None
    if chapter_index > 0:
        previous_chapter = book.get("chapters", {}).get(str(chapter_index - 1), {})
        if isinstance(previous_chapter, dict):
            notes = previous_chapter.get("notes")
            if isinstance(notes, str) and notes.strip():
                previous_notes = notes

    if previous_notes is not None:
        print(f"=== Previous Chapter Notes (Chapter {chapter_index - 1}) ===")
        print(previous_notes)
        print()

    title = chapter["title"]
    content = chapter["content"]
    total_chapters = book["total_chapters"]
    print(f"=== Chapter {chapter_index}: {title} ===")
    if content:
        print(content)

    if total_chapters == 0:
        return

    is_last_chapter = chapter_index == total_chapters - 1
    if is_last_chapter:
        print()
        print(
            "[This is the final chapter. Write a meta-note synthesizing your understanding of the book.]"
        )


def read_chapter(
    root: Path, library: dict, filename: str, chapter_arg: int | None
) -> int:
    file_path = root / "literature" / filename
    if not file_path.is_file():
        print(f"Error: literature file not found: {filename}", file=sys.stderr)
        return 1

    try:
        chapters = load_chapters(file_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    book, changed = ensure_book_metadata(library, filename, len(chapters))
    if changed:
        save_library(root, library)

    if book["total_chapters"] == 0:
        print(f"Error: {filename} has no readable chapters", file=sys.stderr)
        return 1

    chapter_index = resolve_chapter_index(book, chapter_arg)
    if chapter_index is None:
        print(f"Error: no unread chapters remain in {filename}", file=sys.stderr)
        return 1

    chapter_error = validate_chapter_index(book, chapter_index, filename)
    if chapter_error is not None:
        print(chapter_error, file=sys.stderr)
        return 1

    print_read_output(chapters[chapter_index], book, chapter_index)
    return 0


def write_note(
    root: Path,
    library: dict,
    filename: str,
    chapter_index: int,
    text: str | None,
) -> int:
    if text is None:
        print("Error: --text is required for --write-note", file=sys.stderr)
        return 1

    file_path = root / "literature" / filename
    if not file_path.is_file():
        print(f"Error: literature file not found: {filename}", file=sys.stderr)
        return 1

    try:
        chapters = load_chapters(file_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    book, changed = ensure_book_metadata(library, filename, len(chapters))
    chapter_error = validate_chapter_index(book, chapter_index, filename)
    if chapter_error is not None:
        print(chapter_error, file=sys.stderr)
        return 1

    chapters_data = book.setdefault("chapters", {})
    chapter_key = str(chapter_index)
    chapter_data = chapters_data.get(chapter_key)
    if not isinstance(chapter_data, dict):
        chapter_data = {}
        chapters_data[chapter_key] = chapter_data
        changed = True

    if chapter_data.get("read") is not True:
        chapter_data["read"] = True
        changed = True
    if chapter_data.get("notes") != text:
        chapter_data["notes"] = text
        changed = True

    if changed:
        save_library(root, library)

    print(f"Notes saved for chapter {chapter_index} of {filename}")
    return 0


def write_meta_note(
    root: Path,
    library: dict,
    filename: str,
    text: str | None,
) -> int:
    if text is None:
        print("Error: --text is required for --write-meta-note", file=sys.stderr)
        return 1

    file_path = root / "literature" / filename
    if not file_path.is_file():
        print(f"Error: literature file not found: {filename}", file=sys.stderr)
        return 1

    try:
        chapters = load_chapters(file_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    book, changed = ensure_book_metadata(library, filename, len(chapters))
    total_chapters = book.get("total_chapters", 0)
    if total_chapters <= 0:
        print(f"Error: {filename} has no readable chapters", file=sys.stderr)
        return 1

    if book.get("meta_note") != text:
        book["meta_note"] = text
        changed = True

    if changed:
        save_library(root, library)

    print(f"Meta-note saved for {filename}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Incremental literature reader for AI agents")
    parser.add_argument("--list-unread", action="store_true", help="List books with unread chapters")
    parser.add_argument("--read", metavar="FILENAME", help="Read the next unread or specified chapter")
    parser.add_argument(
        "--write-note",
        nargs=2,
        metavar=("FILENAME", "CHAPTER_INDEX"),
        help="Write notes for a specific chapter",
    )
    parser.add_argument(
        "--write-meta-note",
        metavar="FILENAME",
        help="Write a meta-note for the entire book",
    )
    parser.add_argument("--text", help="Text payload for note-writing commands")
    parser.add_argument("--chapter", type=int, help="0-indexed chapter number to read")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    selected_commands = [
        bool(args.list_unread),
        args.read is not None,
        args.write_note is not None,
        args.write_meta_note is not None,
    ]
    if sum(selected_commands) == 0:
        parser.print_help()
        return 1

    if sum(selected_commands) > 1:
        parser.error("choose exactly one command")

    if args.chapter is not None and not args.read:
        parser.error("--chapter requires --read")

    root = Path(__file__).resolve().parent
    load_settings(root)
    try:
        library = load_library(root)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.list_unread:
        return list_unread(root, library)
    if args.read:
        return read_chapter(root, library, args.read, args.chapter)
    if args.write_note:
        filename, chapter_index_raw = args.write_note
        try:
            chapter_index = int(chapter_index_raw)
        except ValueError:
            print(
                f"Error: invalid chapter_index {chapter_index_raw}; expected integer",
                file=sys.stderr,
            )
            return 1
        return write_note(root, library, filename, chapter_index, args.text)

    filename = args.write_meta_note
    return write_meta_note(root, library, filename, args.text)


if __name__ == "__main__":
    raise SystemExit(main())
