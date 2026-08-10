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
LEGACY_ACTIVITY_FILES = ["A1v2.html", "A2v2.html", "A3v2.html"]
POLICY_FILES = ["accessibility.html", "privacy.html", "copyright.html"]
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
    guide = (REPO / "teacher-guide.html").read_text(encoding="utf-8")
    about = (REPO / "about.html").read_text(encoding="utf-8")
    policy_pages = {
        filename: (REPO / filename).read_text(encoding="utf-8") for filename in POLICY_FILES
    }
    assert_true(
        'class="teacher-guide-callout" href="teacher-guide.html"' in index,
        "Prominent Teacher Guide link is missing from index.html",
    )
    assert_true('href="about.html"' in index, "About link is missing from index.html")
    assert_true("<h1>Teacher Guide</h1>" in guide, "Dedicated Teacher Guide page is missing")
    assert_true(
        "<title>About | Module E Bagrut Vocabulary</title>" in about,
        "Dedicated About page is missing",
    )
    assert_true(
        "Source-data corrections and editorial transparency" not in about,
        "Teacher Guide content still appears on the About page",
    )
    assert_true((REPO / "site-policy.css").exists(), "Shared policy-page stylesheet is missing")
    for filename in POLICY_FILES:
        assert_true(f'href="{filename}"' in about, f"About link to {filename} is missing")
        assert_true(f'href="{filename}"' in index, f"Homepage link to {filename} is missing")
        assert_true(f'href="{filename}"' in guide, f"Teacher Guide link to {filename} is missing")
    assert_true(
        "A formal certification by an external accessibility specialist is not claimed" in policy_pages["accessibility.html"],
        "Accessibility statement overclaims formal certification",
    )
    assert_true(
        "does not use registration, login forms, contact forms, advertising, analytics" in policy_pages["privacy.html"],
        "Privacy policy does not state the site's data-minimizing design",
    )
    assert_true(
        "non-commercial classroom teaching" in policy_pages["copyright.html"]
        and "created and edited by Teacher Simon Halevi" in policy_pages["copyright.html"],
        "Copyright page is missing the selected educational-use permission and credit",
    )
    source_files = {
        "LISTA12.12.21.xlsx": "List A",
        "LISTB12.12.21.xlsx": "List B",
        "LISTC12.12.21.xlsx": "List C",
        "LIST-D.xlsx": "List D",
    }
    for filename, label in source_files.items():
        source_path = REPO / "sources" / filename
        assert_true(source_path.exists(), f"Archived Ministry {label} file is missing")
        assert_true(source_path.read_bytes()[:2] == b"PK", f"Archived {label} is not a valid XLSX container")
        assert_true(
            f'href="sources/{filename}"' in guide,
            f"Teacher Guide link to archived {label} is missing",
        )
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
        assert_true(".toUpperCase()" in text, f"Uppercase POS badge formatting missing in {group}.html")
        assert_true(".toLowerCase()" in text, f"Lowercase family POS formatting missing in {group}.html")
        assert_true("familyBox.style.display = 'none'" in text, f"Empty-family hiding missing in {group}.html")
        accessibility_fragments = [
            'class="skip-link" href="#main-content"',
            'class="activity-main" id="main-content"',
            'id="flipButton"',
            'id="cardStatus" role="status" aria-live="polite"',
            'id="cardBack" aria-hidden="true" inert',
            'role="group" aria-label="Flashcard controls"',
            "cardFront.inert = isFlipped",
            "document.getElementById('ttsBtn').disabled = isFlipped",
            "event.key === 'ArrowRight'",
            "event.key === 'ArrowLeft'",
            "prefers-reduced-motion: reduce",
        ]
        for fragment in accessibility_fragments:
            assert_true(fragment in text, f"Accessibility feature missing in {group}.html: {fragment}")
        assert_true(
            "e.key === ' ' || e.key === 'Enter'" not in text,
            f"Conflicting global Enter/Space handler remains in {group}.html",
        )
        for filename in POLICY_FILES:
            assert_true(f'href="{filename}"' in text, f"{filename} footer link missing in {group}.html")
        records = vocab.read_html_records(path)
        records_by_group[group] = records
        records_by_list[group[0]].extend(records)
        assert_true(len(records) == EXPECTED_COUNTS[group], f"Unexpected count in {group}: {len(records)}")
        for record in records:
            assert_true(record.get("pos"), f"Missing POS in {group}: {record.get('en')}")
            assert_true(record.get("mean_he"), f"Missing Hebrew meaning in {group}: {record.get('en')}")
            assert_true(record.get("ex_en"), f"Missing English example in {group}: {record.get('en')}")
            assert_true(record.get("support_text"), f"Missing A2 support in {group}: {record.get('en')}")
            assert_true(
                record.get("grammar") == record.get("grammar", "").lower()
                and not re.search(r"[.!?…;:]$", record.get("grammar", "")),
                f"Inconsistent grammar label in {group}: {record.get('en')}",
            )
            assert_true(
                " / " not in record["mean_he"] and not re.search(r"[.!?…;:]$", record["mean_he"]),
                f"Inconsistent Hebrew punctuation in {group}: {record.get('en')}",
            )
            assert_true(
                re.search(r"[.!?…][”\"]?$", record["ex_en"]) is not None,
                f"English example lacks terminal punctuation in {group}: {record.get('en')}",
            )
            assert_true(
                not re.search(r"[.!?…;:]$", record["support_text"]),
                f"Support text has terminal punctuation in {group}: {record.get('en')}",
            )
            assert_true(
                "'" not in record["en"] and "'" not in record["ex_en"],
                f"Straight apostrophe remains in visible English in {group}: {record.get('en')}",
            )
            family_pairs = [(item.get("word"), item.get("pos")) for item in record.get("family_members", [])]
            assert_true(all(word and pos for word, pos in family_pairs), f"Incomplete family item in {group}")
            assert_true(len(family_pairs) == len(set(family_pairs)), f"Duplicate family item in {group}")
            assert_true(
                all(pos.casefold() != "nan" and "'" not in word for word, pos in family_pairs),
                f"Invalid family spelling or POS in {group}: {record.get('en')}",
            )

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

        display_by_key = {
            vocab.key_text(card["display"]): card["display"] for card in official_cards[letter]
        }
        for record in records_by_list[letter]:
            assert_true(
                record["en"] == display_by_key[vocab.key_text(record["en"])],
                f"Display capitalization mismatch: List {letter} {record['en']}",
            )

    json_rows = json.loads((REPO / "data/vocabulary-master.json").read_text(encoding="utf-8"))
    assert_true(len(json_rows) == 982, f"Master JSON has {len(json_rows)} rows instead of 982")
    json_keys = Counter((row["group"], row["en"], row["pos"]) for row in json_rows)
    assert_true(max(json_keys.values()) == 1, "Duplicate Group + Word/Phrase + POS in master JSON")

    for filename in LEGACY_ACTIVITY_FILES:
        text = (REPO / filename).read_text(encoding="utf-8")
        assert_true('class="skip-link" href="#main-content"' in text, f"Skip link missing in {filename}")
        assert_true('id="flipButton"' in text, f"Accessible flip control missing in {filename}")
        assert_true("e.key === ' ' || e.key === 'Enter'" not in text, f"Keyboard conflict remains in {filename}")
        for policy in POLICY_FILES:
            assert_true(f'href="{policy}"' in text, f"{policy} footer link missing in {filename}")

    all_html = {path.name: path.read_text(encoding="utf-8") for path in REPO.glob("*.html")}
    for filename, text in all_html.items():
        assert_true("document.cookie" not in text, f"Cookie-writing code found in {filename}")
        assert_true("localStorage" not in text, f"Local storage code found in {filename}")
        assert_true("<form" not in text.lower(), f"Unexpected form found in {filename}")
        assert_true(
            re.search(r'<script[^>]+src=["\']https?://', text, re.I) is None,
            f"Unexpected external script found in {filename}",
        )
        for href in re.findall(r'href=["\']([^"\']+)["\']', text, re.I):
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            local_path = href.split("#", 1)[0].split("?", 1)[0]
            if local_path:
                assert_true((REPO / local_path).exists(), f"Broken local link in {filename}: {href}")

    print("PASS: 12 activities, 982 cards, legacy pages, policies, accessibility controls, privacy checks, archived A–D sources, official coverage, capitalization, punctuation, links and static assets validated.")


if __name__ == "__main__":
    main()
