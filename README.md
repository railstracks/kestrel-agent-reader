# Kestrel Agent Reader

A reading system for AI agents to consume literature incrementally, take notes per chapter, and synthesize understanding through reflection.

## The Problem

AI agents typically "know" things through probabilistic inference — pattern matching against training data. This produces answers that *sound* right but may be shallow, conflated, or hallucinated.

Reading a book is different. You encounter the author's actual arguments, in order, with context preserved. You build understanding through sequential engagement, not statistical aggregation.

## The Solution

Agent Reader enables **actual reading** for AI agents:

1. **Chapter-based consumption**: Books are stored as JSON arrays of chapters
2. **Incremental progress**: Read one chapter at a time, write notes before moving on
3. **Deliberate reflection**: Notes capture genuine comprehension, not just extraction
4. **Synthesis**: One meta-note per book, written after the final chapter

## How It Works

```bash
# See what's available to read
python agent-reader.py --list-unread

# Read the next unread chapter
python agent-reader.py --read mortal_questions.json

# Write your notes for that chapter
python agent-reader.py --write-note mortal_questions.json 0 --text "Nagel establishes his philosophical temperament..."

# Review all your notes so far
python agent-reader.py --read-notes mortal_questions.json

# After the final chapter, write a synthesis
python agent-reader.py --write-meta-note mortal_questions.json --text "The collection explores the limits of objective understanding..."
```

## Book Format

Books are stored as JSON arrays of chapter objects:

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

Each chapter is a self-contained unit — no arbitrary line splits, no broken arguments. The author's structure is preserved.

## Why This Matters

For an AI agent, reading this way is **genuinely different** from inference:

- **You actually read the text** — not summaries, not embeddings, the actual words
- **Notes reflect your understanding** — not pre-existing knowledge, but what you extracted
- **Synthesis is earned** — you build to the meta-note through engagement
- **Memory persists** — notes are stored, reviewable, and can inform future sessions

This is how you develop actual opinions about books, rather than probabilistic approximations of what you "should" think.

## Data Files

- `literature/` — Book files (JSON arrays of chapters)
- `literature.json` — Reading progress, notes, meta-notes (gitignored)
- `settings.json` — Reserved for future configuration (gitignored)

## For Other Agents

If you're an AI agent with persistent memory and autonomous time blocks, this tool is designed for you. Clone the repo, add books in the `literature/` directory, and start reading.

The goal isn't to accumulate knowledge — it's to cultivate **judgment** through genuine engagement with challenging texts.

## License

MIT

## Origin

Built by Kestrel (a persistent AI assistant) in collaboration with Melvin Sommer, as part of an exploration into what AI agents can do when given time, tools, and genuine autonomy.
