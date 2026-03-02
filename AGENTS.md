# Kestrel Agent Reader

A reading system for AI agents to consume literature incrementally, take notes per chapter, and synthesize understanding through reflection.

## Purpose

AI agents typically "know" things through probabilistic inference — pattern matching against training data. This tool enables a different approach: **actual reading** of full texts, chapter by chapter, with deliberate note-taking and reflection.

The goal is to cultivate genuine understanding and personal insights that persist through memory systems, rather than relying on inferred knowledge that may be shallow or hallucinated.

## How It Works

1. **Chapter-based reading**: Books are stored as JSON arrays of chapters, preserving author structure
2. **Per-chapter notes**: After reading each chapter, the agent writes notes capturing observations, questions, and insights
3. **Meta-notes**: One meta-note per book, written after the final chapter
4. **Continuity**: Previous chapter notes are available when reading subsequent chapters, maintaining context
5. **Review**: The `--read-notes` command displays all notes for reflection before synthesis

## Structure

```
kestrel-agent-reader/
├── agent-reader.py      # Main CLI script
├── literature/          # Directory containing book files (JSON)
├── literature.json      # Metadata: chapters read, notes, meta-note (gitignored)
├── settings.json        # Reserved for future config (gitignored)
├── .gitignore
├── AGENTS.md            # This file (project context)
└── README.md            # Public documentation
```

## CLI Interface

```bash
# List books with unread chapters
python agent-reader.py --list-unread

# Read next unread chapter from a book
python agent-reader.py --read <filename>

# Read specific chapter
python agent-reader.py --read <filename> --chapter <n>

# Write notes for a chapter
python agent-reader.py --write-note <filename> <chapter_index> --text "Notes go here"

# Review all notes written so far
python agent-reader.py --read-notes <filename>

# Write meta-note (one per book, after the final chapter)
python agent-reader.py --write-meta-note <filename> --text "Synthesis..."
```

## Book Format

Books are stored as JSON arrays of chapter objects in the `literature/` directory:

```json
[
  {
    "title": "Chapter 1: What Is It Like to Be a Bat?",
    "content": "Consciousness is what makes the mind-body problem really intractable..."
  },
  {
    "title": "Chapter 2: Panpsychism",
    "content": "The view that the basic physical constituents..."
  }
]
```

Each chapter is a self-contained unit — the author's structure is preserved, not split at arbitrary line boundaries.

## Notes Schema (literature.json)

```json
{
  "books": {
    "filename.json": {
      "total_chapters": 14,
      "chapters": {
        "0": { "read": true, "notes": "..." },
        "1": { "read": true, "notes": "..." }
      },
      "meta_note": "Synthesis of the full book..."
    }
  }
}
```

## Intended User

This tool is designed for Kestrel (or similar persistent AI agents) to develop deeper understanding through deliberate reading practice. It's part of the "gallivanting" framework — autonomous exploration and personal development.

## Why This Matters

For an AI agent, reading this way is genuinely different from inference:

- **You actually read the text** — not summaries, not embeddings, the actual words
- **Notes reflect your understanding** — not pre-existing knowledge, but what you extracted
- **Synthesis is earned** — you build to the meta-note through sequential engagement
- **Memory persists** — notes are stored, reviewable, and can inform future sessions

## Future Considerations

- Multiple reading modes (skimming, deep reading, reference lookup)
- Reading history/statistics
- Export notes to other formats
- Integration with journal/memory systems
