#!/usr/bin/env python3
import argparse
import json
import math
import sys
import tempfile
from pathlib import Path


DEFAULT_SETTINGS = {
    "block_size": 200,
    "metanote_frequency": 10,
}

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
    block_size = data.get("block_size")
    metanote_frequency = data.get("metanote_frequency")
    if not isinstance(block_size, int) or block_size <= 0:
        block_size = DEFAULT_SETTINGS["block_size"]
    if not isinstance(metanote_frequency, int) or metanote_frequency <= 0:
        metanote_frequency = DEFAULT_SETTINGS["metanote_frequency"]
    normalized = {
        "block_size": block_size,
        "metanote_frequency": metanote_frequency,
    }
    if normalized != data:
        atomic_write_json(root / "settings.json", normalized)
    return normalized


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


def read_lines(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline=None) as handle:
        return handle.read().splitlines()


def calculate_total_blocks(total_lines: int, block_size: int) -> int:
    if total_lines == 0:
        return 0
    return math.ceil(total_lines / block_size)


def ensure_book_metadata(
    library: dict, filename: str, lines: list[str], block_size: int
) -> tuple[dict, bool]:
    books = library.setdefault("books", {})
    book = books.get(filename)
    total_lines = len(lines)
    total_blocks = calculate_total_blocks(total_lines, block_size)
    changed = False

    if not isinstance(book, dict):
        book = {}
        books[filename] = book
        changed = True

    if not isinstance(book.get("blocks"), dict):
        book["blocks"] = {}
        changed = True

    if not isinstance(book.get("meta_notes"), dict):
        book["meta_notes"] = {}
        changed = True

    if book.get("total_lines") != total_lines:
        book["total_lines"] = total_lines
        changed = True

    if book.get("total_blocks") != total_blocks:
        book["total_blocks"] = total_blocks
        changed = True

    return book, changed


def get_literature_files(root: Path) -> list[Path]:
    literature_dir = root / "literature"
    literature_dir.mkdir(exist_ok=True)
    return sorted(path for path in literature_dir.iterdir() if path.is_file())


def get_unread_blocks(book: dict) -> list[int]:
    total_blocks = book.get("total_blocks", 0)
    blocks = book.get("blocks", {})
    unread = []
    for index in range(total_blocks):
        block_data = blocks.get(str(index), {})
        if not isinstance(block_data, dict) or block_data.get("read") is not True:
            unread.append(index)
    return unread


def list_unread(root: Path, settings: dict, library: dict) -> int:
    lines_out = []
    changed = False

    for file_path in get_literature_files(root):
        lines = read_lines(file_path)
        book, book_changed = ensure_book_metadata(
            library, file_path.name, lines, settings["block_size"]
        )
        changed = changed or book_changed
        unread = get_unread_blocks(book)
        if not unread:
            continue
        total_blocks = book["total_blocks"]
        if len(unread) == total_blocks:
            detail = "all blocks"
        else:
            detail = f"block {unread[0]}-{unread[-1]} of {total_blocks}"
        label = "block" if len(unread) == 1 else "blocks"
        lines_out.append(
            f"{file_path.name}: {len(unread)} unread {label} ({detail})"
        )

    if changed:
        save_library(root, library)

    if lines_out:
        print("\n".join(lines_out))
        return 0
    return 1


def resolve_block_index(book: dict, requested_block: int | None) -> int | None:
    if requested_block is not None:
        return requested_block
    unread = get_unread_blocks(book)
    if unread:
        return unread[0]
    return None


def validate_block_index(book: dict, block_index: int, filename: str) -> str | None:
    total_blocks = book.get("total_blocks", 0)
    if not isinstance(block_index, int) or block_index < 0 or block_index >= total_blocks:
        if total_blocks <= 0:
            return f"Error: {filename} has no readable blocks"
        return (
            f"Error: invalid block_index {block_index} for {filename}; "
            f"valid range is 0 to {total_blocks - 1}"
        )
    return None


def validate_meta_note_index(meta_note_index: int) -> str | None:
    if not isinstance(meta_note_index, int) or meta_note_index < 0:
        return "Error: meta-note index must be a non-negative integer"
    return None


def print_read_output(
    file_path: Path, lines: list[str], book: dict, block_index: int, settings: dict
) -> None:
    previous_notes = None
    if block_index > 0:
        previous_block = book.get("blocks", {}).get(str(block_index - 1), {})
        if isinstance(previous_block, dict):
            notes = previous_block.get("notes")
            if isinstance(notes, str) and notes.strip():
                previous_notes = notes

    if previous_notes is not None:
        print(f"=== Previous Block Notes (Block {block_index - 1}) ===")
        print(previous_notes)
        print()

    total_blocks = book["total_blocks"]
    print(f"=== Block {block_index} of {total_blocks}: {file_path.name} ===")

    start = block_index * settings["block_size"]
    end = start + settings["block_size"]
    block_lines = lines[start:end]
    if block_lines:
        print("\n".join(block_lines))

    if total_blocks == 0:
        return

    is_last_block = block_index == total_blocks - 1
    meta_due = ((block_index + 1) % settings["metanote_frequency"] == 0) or is_last_block
    if meta_due:
        print()
        print(
            "[Meta-note due: this is block "
            f"{block_index}, metanote_frequency is {settings['metanote_frequency']}]"
        )


def read_block(
    root: Path, settings: dict, library: dict, filename: str, block_arg: int | None
) -> int:
    file_path = root / "literature" / filename
    if not file_path.is_file():
        print(f"Error: literature file not found: {filename}", file=sys.stderr)
        return 1

    lines = read_lines(file_path)
    book, changed = ensure_book_metadata(library, filename, lines, settings["block_size"])
    if changed:
        save_library(root, library)

    if book["total_blocks"] == 0:
        print(f"Error: {filename} has no readable blocks", file=sys.stderr)
        return 1

    block_index = resolve_block_index(book, block_arg)
    if block_index is None:
        print(f"Error: no unread blocks remain in {filename}", file=sys.stderr)
        return 1

    block_error = validate_block_index(book, block_index, filename)
    if block_error is not None:
        print(block_error, file=sys.stderr)
        return 1

    print_read_output(file_path, lines, book, block_index, settings)
    return 0


def write_note(
    root: Path,
    settings: dict,
    library: dict,
    filename: str,
    block_index: int,
    text: str | None,
) -> int:
    if text is None:
        print("Error: --text is required for --write-note", file=sys.stderr)
        return 1

    file_path = root / "literature" / filename
    if not file_path.is_file():
        print(f"Error: literature file not found: {filename}", file=sys.stderr)
        return 1

    lines = read_lines(file_path)
    book, changed = ensure_book_metadata(library, filename, lines, settings["block_size"])
    block_error = validate_block_index(book, block_index, filename)
    if block_error is not None:
        print(block_error, file=sys.stderr)
        return 1

    blocks = book.setdefault("blocks", {})
    block_key = str(block_index)
    block_data = blocks.get(block_key)
    if not isinstance(block_data, dict):
        block_data = {}
        blocks[block_key] = block_data
        changed = True

    if block_data.get("read") is not True:
        block_data["read"] = True
        changed = True
    if block_data.get("notes") != text:
        block_data["notes"] = text
        changed = True

    if changed:
        save_library(root, library)

    print(f"Notes saved for block {block_index} of {filename}")
    return 0


def write_meta_note(
    root: Path,
    settings: dict,
    library: dict,
    filename: str,
    meta_note_index: int,
    text: str | None,
) -> int:
    if text is None:
        print("Error: --text is required for --write-meta-note", file=sys.stderr)
        return 1

    meta_note_error = validate_meta_note_index(meta_note_index)
    if meta_note_error is not None:
        print(meta_note_error, file=sys.stderr)
        return 1

    file_path = root / "literature" / filename
    if not file_path.is_file():
        print(f"Error: literature file not found: {filename}", file=sys.stderr)
        return 1

    lines = read_lines(file_path)
    book, changed = ensure_book_metadata(library, filename, lines, settings["block_size"])
    total_blocks = book.get("total_blocks", 0)
    if total_blocks <= 0:
        print(f"Error: {filename} has no readable blocks", file=sys.stderr)
        return 1

    meta_notes = book.setdefault("meta_notes", {})
    meta_note_key = str(meta_note_index)
    if meta_notes.get(meta_note_key) != text:
        meta_notes[meta_note_key] = text
        changed = True

    if changed:
        save_library(root, library)

    first_block = meta_note_index * settings["metanote_frequency"]
    last_block = min(
        ((meta_note_index + 1) * settings["metanote_frequency"]) - 1,
        total_blocks - 1,
    )
    print(
        f"Meta-note {meta_note_index} saved for {filename} "
        f"(covers blocks {first_block}-{last_block})"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Incremental literature reader for AI agents")
    parser.add_argument("--list-unread", action="store_true", help="List books with unread blocks")
    parser.add_argument("--read", metavar="FILENAME", help="Read the next unread or specified block")
    parser.add_argument(
        "--write-note",
        nargs=2,
        metavar=("FILENAME", "BLOCK_INDEX"),
        help="Write notes for a specific block",
    )
    parser.add_argument(
        "--write-meta-note",
        nargs=2,
        metavar=("FILENAME", "META_NOTE_INDEX"),
        help="Write a meta-note for a range of blocks",
    )
    parser.add_argument("--text", help="Text payload for note-writing commands")
    parser.add_argument("--block", type=int, help="0-indexed block number to read")
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

    if args.block is not None and not args.read:
        parser.error("--block requires --read")

    root = Path(__file__).resolve().parent
    settings = load_settings(root)
    try:
        library = load_library(root)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.list_unread:
        return list_unread(root, settings, library)
    if args.read:
        return read_block(root, settings, library, args.read, args.block)
    if args.write_note:
        filename, block_index_raw = args.write_note
        try:
            block_index = int(block_index_raw)
        except ValueError:
            print(
                f"Error: invalid block_index {block_index_raw}; expected integer",
                file=sys.stderr,
            )
            return 1
        return write_note(root, settings, library, filename, block_index, args.text)

    filename, meta_note_index_raw = args.write_meta_note
    try:
        meta_note_index = int(meta_note_index_raw)
    except ValueError:
        print(
            f"Error: invalid meta-note index {meta_note_index_raw}; expected integer",
            file=sys.stderr,
        )
        return 1
    return write_meta_note(
        root, settings, library, filename, meta_note_index, args.text
    )


if __name__ == "__main__":
    raise SystemExit(main())
