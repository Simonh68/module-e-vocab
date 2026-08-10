#!/usr/bin/env python3
"""Static consistency checks for the GitHub Pages build."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import rebuild_official_vocab as vocab


REPO = Path(__file__).resolve().parents[1]
GROUPS = [f"{letter}{number}" for letter in "ABCD" for number in range(1, 4)]
EXPECTED_COUNTS = {
    "A1": 80, "A2": 80, "A3": 79,
    "B1": 80, "B2": 80, "B3": 79,
    "C1": 83, "C2": 83, "C3": 83,
    "D1": 85, "D2": 85, "D3": 85,
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    assert_true((REPO / ".nojekyll").exists(), ".nojekyll is missing")
    index = (REPO / "index.html").read_text(encoding="utf-8")
    for group in GROUPS:
        assert_true(f'href="{group}.html"' in index, f"Missing Play link for {group}")
        assert_true(f'data-file="{group}.html"' in index, f"Missing Copy link for {group}")
    assert_true("Download" not in index, "Old Download text remains in index.html")
    assert_true(
        "https://simonh68.github.io/module-e-vocab/" in index,
        "Absolute GitHub Pages base URL is missing",
    )

    official_rows = {letter: vocab.load_official_rows(letter) for letter in "ABCD"}
    official_cards = {
        letter: vocab.merge_official_cards(official_rows[letter]) for letter in "ABCD"
    }
    records_by_group = {}
    records_by_list = defaultdict(list)
    for group in GROUPS:
        path = REPO / f"{group}.html"
        text = path.read_text(encoding="utf-8")
        assert_true(
            f"<title>Module E 2027 Vocabulary Flashcards - Part {group}</title>" in text,
            f"Incorrect title in {group}.html",
        )
        assert_true("favicon.svg?v=" in text, f"Cache-busted favicon missing in {group}.html")
        assert_true(
            text.count('id="familyBox"') == 1,
            f"Family box must appear exactly once in {group}.html",
        )
        assert_true(
            text.count("const familyBox = document.getElementById('familyBox');") == 1,
            f"Family JavaScript must appear exactly once in {group}.html",
        )
        assert_true("familyBox.style.display = 'none'" in text, f"Empty-family hiding missing in {group}.html")
        records = vocab.read_html_records(path)
        records_by_group[group] = records
        records_by_list[group[0]].extend(records)
        assert_true(len(records) == EXPECTED_COUNTS[group], f"Unexpected count in {group}: {len(records)}")
        for record in records:
            assert_true(record.get("pos"), f"Missing POS in {group}: {record.get('en')}")
            assert_true(record.get("mean_he"), f"Missing Hebrew meaning in {group}: {record.get('en')}")
            assert_true(record.get("ex_en"), f"Missing English example in {group}: {record.get('en')}")
            assert_true(record.get("support_text"), f"Missing A2 support in {group}: {record.get('en')}")
            family_pairs = [(item.get("word"), item.get("pos")) for item in record.get("family_members", [])]
            assert_true(all(word and pos for word, pos in family_pairs), f"Incomplete family item in {group}")
            assert_true(len(family_pairs) == len(set(family_pairs)), f"Duplicate family item in {group}")

    for letter in "ABCD":
        expected = {(vocab.key_text(card["display"]), card["pos"]) for card in official_cards[letter]}
        actual_pairs = [(vocab.key_text(record["en"]), record["pos"]) for record in records_by_list[letter]]
        actual = set(actual_pairs)
        assert_true(len(actual_pairs) == len(actual), f"Duplicate activity card in List {letter}")
        if letter in "AB":
            assert_true(
                actual == expected,
                f"Official coverage mismatch in List {letter}: missing={sorted(expected-actual)[:5]}, extra={sorted(actual-expected)[:5]}",
            )
        else:
            # C/D card content and POS were already published and are intentionally
            # preserved; verify complete official headword coverage here.
            expected_words = {word for word, _ in expected}
            actual_words = {word for word, _ in actual}
            assert_true(
                actual_words == expected_words,
                f"Official headword coverage mismatch in List {letter}",
            )

        family_by_display = defaultdict(list)
        for row in official_rows[letter]:
            key = vocab.key_text(row["display"])
            seen = {(item["word"], item["pos"]) for item in family_by_display[key]}
            for item in row["family_members"]:
                pair = (item["word"], item["pos"])
                if pair not in seen:
                    family_by_display[key].append(item)
                    seen.add(pair)
        for record in records_by_list[letter]:
            expected_family = family_by_display[vocab.key_text(record["en"])]
            assert_true(
                record.get("family_members", []) == expected_family,
                f"Family mismatch: List {letter} {record['en']} {record['pos']}",
            )

    json_rows = json.loads((REPO / "data/vocabulary-master.json").read_text(encoding="utf-8"))
    assert_true(len(json_rows) == 982, f"Master JSON has {len(json_rows)} rows instead of 982")
    json_keys = Counter((row["group"], row["en"], row["pos"]) for row in json_rows)
    assert_true(max(json_keys.values()) == 1, "Duplicate Group + Word/Phrase + POS in master JSON")
    print("PASS: 12 activity files, 982 cards, official A–D coverage, family data, titles, links and static assets validated.")


if __name__ == "__main__":
    main()
