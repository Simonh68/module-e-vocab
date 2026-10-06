# Battle Room datasets

The multiplayer room, turns, scoring, streaks and power rounds live in `core.cjs` and do not import a vocabulary file.

## Dataset contract

A provider returns:

```js
{
  id: "band3",
  label: "Band III · All A–D",
  items: [
    {
      id: "A1-001",
      word: "proof",
      pos: "Noun",
      meaning: "information showing that something is true",
      example: "The photo provided proof of the damage.",
      group: "A1"
    }
  ],
  source: { ... }
}
```

Each item needs an id, an English word, and either an English meaning or a source English example.

## Registered datasets

- `band3` — local `data/vocabulary-master.json`
- `band2-core1` — Band II groups 01–20
- `band2-core2` — Band II groups 21–40
- `band2-all` — Band II groups 01–40

Band II is read from the existing public E‑Vocab Band II group pages and cached per server process. No student data is added.

When a Band II record has an explicit English sense (or source synonym), the game keeps the word → four English meanings format. When the source record has no English sense, the adapter uses its existing English example as a cloze question only when the target word can be removed safely. It does not invent a new English definition.

## Adding another corpus

Add a loader under `datasets/`, register one id in `vocab-provider.cjs`, and return the same contract. No room, scoring or multiplayer code should change.

## Merge note

This branch was intentionally created separately from `codex/word-rivals-online-20260928` because the spectator/four-pool work existed only as an unpublished local commit (`b419f52c1c1701af06c53961d9efe32482984f3f`) when this refactor began. Merge the two lines only after that work is available remotely, preserving the provider boundary.
