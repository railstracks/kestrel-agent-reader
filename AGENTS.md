# Kestrel Agent Reader

A reading system for AI agents to consume literature incrementally, take notes per block, and synthesize understanding through periodic meta-notes.

## Purpose

AI agents typically "know" things through probabilistic inference — pattern matching against training data. This tool enables a different approach: **actual reading** of full texts, block by block, with deliberate note-taking and reflection.

The goal is to cultivate genuine understanding and personal insights that persist through memory systems, rather than relying on inferred knowledge that may be shallow or hallucinated.

## How It Works

1. **Chapter-based reading**: Books are divided into explicit chapters in JSON files
2. **Per-chapter notes**: After reading each chapter, the agent writes notes capturing observations, questions, and insights
3. **Meta-notes**: One meta-note per book, written after the final chapter
4. **Continuity**: Previous chapter notes are shown when reading the next chapter, maintaining context

## Structure

```
kestrel-agent-reader/
├── agent-reader.py      # Main CLI script
├── literature/          # Directory containing book files
├── literature.json      # Metadata: chapters read, notes, meta-note (gitignored)
├── settings.json        # Reserved for future config (gitignored)
├── .gitignore
└── AGENTS.md            # This file
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

# Write meta-note (one per book, after the final chapter)
python agent-reader.py --write-meta-note <filename> --text "Synthesis..."
```

## Settings

- Reserved for future settings. File may be empty (`{}`).

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

## Future Considerations

- Multiple reading modes (skimming, deep reading, reference lookup)
- Reading history/statistics
- Export notes to other formats
- Integration with journal/memory systems
