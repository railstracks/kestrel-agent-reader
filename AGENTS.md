# Kestrel Agent Reader

A reading system for AI agents to consume literature incrementally, take notes per block, and synthesize understanding through periodic meta-notes.

## Purpose

AI agents typically "know" things through probabilistic inference — pattern matching against training data. This tool enables a different approach: **actual reading** of full texts, block by block, with deliberate note-taking and reflection.

The goal is to cultivate genuine understanding and personal insights that persist through memory systems, rather than relying on inferred knowledge that may be shallow or hallucinated.

## How It Works

1. **Block-based reading**: Books are divided into configurable blocks (default 200 lines)
2. **Per-block notes**: After reading each block, the agent writes notes capturing observations, questions, and insights
3. **Meta-notes**: Every N blocks (configurable), the agent writes a synthesis — looking back across recent blocks to identify patterns, themes, and evolving understanding
4. **Continuity**: Previous block notes are shown when reading the next block, maintaining context

## Structure

```
kestrel-agent-reader/
├── agent-reader.py      # Main CLI script
├── literature/          # Directory containing book files
├── literature.json      # Metadata: blocks read, notes, meta-notes (gitignored)
├── settings.json        # Config: block_size, metanote_frequency (gitignored)
├── .gitignore
└── AGENTS.md            # This file
```

## CLI Interface

```bash
# List books with unread blocks
python agent-reader.py --list-unread

# Read next unread block from a book
python agent-reader.py --read <filename>

# Read specific block
python agent-reader.py --read <filename> --block <n>

# Write notes for a block
python agent-reader.py --write-note <filename> <block_index> --text "Notes go here"

# Write meta-note (triggered every N blocks or at book end)
python agent-reader.py --write-meta-note <filename> <meta-note_index> --text "Synthesis..."
```

## Settings

- `block_size`: Number of lines per block (default: 200)
- `metanote_frequency`: Number of blocks between meta-notes (default: 10)

## Notes Schema (literature.json)

```json
{
  "books": {
    "filename.txt": {
      "total_blocks": 42,
      "blocks": {
        "0": { "read": true, "notes": "..." },
        "1": { "read": true, "notes": "..." }
      },
      "meta_notes": {
        "0": "Synthesis of blocks 0-9...",
        "1": "Synthesis of blocks 10-19..."
      }
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
