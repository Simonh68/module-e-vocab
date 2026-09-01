#!/usr/bin/env python3
"""Static consistency checks for the GitHub Pages build."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import rebuild_official_vocab as vocab


REPO = Path(__file__).resolve().parents[1]
GROUPS = [f"{letter}{number}" for letter in "ABCD" for number in range(1, 4)]
POLICY_FILES = ["accessibility.html", "privacy.html", "copyright.html"]
EXPECTED_COUNTS = {
    "A1": 80, "A2": 80, "A3": 79,
    "B1": 80, "B2": 80, "B3": 79,
    "C1": 83, "C2": 83, "C3": 83,
    "D1": 85, "D2": 85, "D3": 85,
}
EXPECTED_IDENTITY_SHA256 = {
    "A1": "fc2ea43a37624014c4005a8cabc8abb295dd48b0f4b4f49628eb2cd78dfb95df",
    "A2": "bda30cceff657de7dcc7f4789902ac8d71051ee5a13e9f49f4995bd3318086f0",
    "A3": "d9f4283f922782c07d690eee548fb2fc318f27f637694837b7460d5a736c3581",
    "B1": "67a4aa5356c1a5f2bfa156d20d2bc5ac7a32c1c36816155e3d806b75f8ec5f2a",
    "B2": "b963c204b3bf72d66a9475a96bba1f292c87d5ecba69f669113c0e84d2c47b44",
    "B3": "6758afd52cd647fc90c8173d080d415c5e2d36b8e8ce2ca2f37dd40ed396af96",
    "C1": "7ec638d280aabff8d9ecd344ad0b939ebf8c7cd3c15d7b15e330a9a14634cebb",
    "C2": "7f244c3aa59d1257f1bf251bb4a249e8d5e67d3e6a514c8645f2117db3695d9e",
    "C3": "c12894bab80f57a6578e1a85fb546a258046c1d07a05b8bddbd597e671aa1c55",
    "D1": "f65c5d5b33052eebf418fb1d631e96653f03169787601bc5c3bc45ebb1cd8c5c",
    "D2": "1bbd9a1cc97a224e612866bc346a53981001aa29ee6bcf53cca6a57b5a00aa58",
    "D3": "863aafabfe4b86a1320a47ca0e70998f86dba62df77f6ef99d2e54747484a9d7",
}
EXPECTED_GLOBAL_IDENTITY_SHA256 = (
    "7efa2b5ee5396b0b1d4d4a67aa26ba60dcd10761315c4deff7e84839f5cf56ab"
)
MAX_EXAMPLE_WORDS = 12
# Contractions and hyphenated compounds count as one word; punctuation does
# not count. Numeric values count as one word. This is deliberately independent
# of whitespace so curly quotes and punctuation cannot change the result.
ENGLISH_WORD_RE = re.compile(
    r"[A-Za-z]+(?:[’'][A-Za-z]+)*(?:-[A-Za-z]+(?:[’'][A-Za-z]+)*)*"
    r"|\d+(?:[.,]\d+)*"
)
PLACEHOLDER_RE = re.compile(r"\b(?:sb|sth|smt)\b", re.IGNORECASE)
# These examples were explicitly identified as fragments. Keeping the check
# exact makes it useful without rejecting legitimate short imperatives or fixed
# linguistic formulas.
KNOWN_CLEAR_FRAGMENTS = {
    "the victim of the accident",
    "a lucky escape",
    "computer hardware",
    "a laser beam",
    "a scary monster under the bed",
    "the boy next door",
    "yours sincerely, anna",
}
VALID_FAMILY_POS = set(vocab.POS_NAMES.values()) | {
    "Phrase", "Phrasal verb", "Noun phrase",
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def assert_valid_family_pos(pos: str, context: str) -> None:
    labels = [label.strip() for label in pos.split(",")]
    assert_true(
        bool(labels) and all(label in VALID_FAMILY_POS for label in labels),
        f"Invalid family POS in {context}: {pos}",
    )


def english_word_count(text: str) -> int:
    """Count lexical English words; contractions/hyphenated forms count once."""
    return len(ENGLISH_WORD_RE.findall(text))


def identity_digest(rows: list[dict]) -> str:
    """Hash immutable ID, displayed entry and POS tuples in their exact order."""
    identity = [
        (row["source_entry_id"], row["en"], row["pos"])
        for row in rows
    ]
    payload = json.dumps(
        identity, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def assert_json_matches_html(json_rows: list[dict], html_rows: list[dict]) -> None:
    """Require byte-semantic row equality, including order, across both outputs."""
    if json_rows == html_rows:
        return
    if len(json_rows) != len(html_rows):
        raise AssertionError(
            "Master JSON/HTML row-count mismatch: "
            f"JSON={len(json_rows)}, HTML={len(html_rows)}"
        )
    for index, (json_row, html_row) in enumerate(zip(json_rows, html_rows), start=1):
        if json_row != html_row:
            fields = sorted(set(json_row) | set(html_row))
            different = [field for field in fields if json_row.get(field) != html_row.get(field)]
            identity = html_row.get("source_entry_id", f"row {index}")
            raise AssertionError(
                f"Master JSON/HTML mismatch at {identity}: "
                f"different field(s): {', '.join(different)}"
            )
    raise AssertionError("Master JSON and HTML rows differ")


def main() -> None:
    assert_true((REPO / ".nojekyll").exists(), ".nojekyll is missing")
    index = (REPO / "index.html").read_text(encoding="utf-8")
    analytics = (REPO / "analytics.js").read_text(encoding="utf-8")
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
        "<title>About | E-Vocab for Module E</title>" in about,
        "Dedicated About page is missing",
    )
    assert_true(
        "Source-data corrections and editorial transparency" not in about,
        "Teacher Guide content still appears on the About page",
    )
    future_resource_notice = (
        "not currently available"
        in guide
        and "not part of the content unit submitted at this stage" in guide
        and "compatible, complementary extension" in guide
        and "not currently available" in about
        and "not included in the content unit submitted at this stage" in about
    )
    assert_true(
        future_resource_notice,
        "Future teacher resources are not clearly separated from the submitted unit",
    )
    assert_true((REPO / "site-policy.css").exists(), "Shared policy-page stylesheet is missing")
    assert_true((REPO / "ownership.js").exists(), "Shared ownership notice is missing")
    assert_true("ownership.js?v=1" in analytics, "Analytics does not load the shared ownership notice")
    for filename in POLICY_FILES:
        assert_true(f'href="{filename}"' in about, f"About link to {filename} is missing")
        assert_true(f'href="{filename}"' in index, f"Homepage link to {filename} is missing")
        assert_true(f'href="{filename}"' in guide, f"Teacher Guide link to {filename} is missing")
    assert_true(
        "A formal certification by an external accessibility specialist is not claimed" in policy_pages["accessibility.html"],
        "Accessibility statement overclaims formal certification",
    )
    assert_true(
        "does not use registration, login forms, advertising" in policy_pages["privacy.html"]
        and "limited, anonymous operational analytics" in policy_pages["privacy.html"]
        and "does not collect names, email addresses" in policy_pages["privacy.html"],
        "Privacy policy does not state the site's data-minimizing design",
    )
    assert_true(
        "non-commercial classroom teaching" in policy_pages["copyright.html"]
        and "permission is limited to online use" in policy_pages["copyright.html"].lower()
        and "does not permit downloading, copying, printing, distributing, modifying" in policy_pages["copyright.html"],
        "Copyright page is missing the selected online-use-only permission",
    )
    assert_true(
        "שמעון הרצל הלוי גובני" in policy_pages["copyright.html"]
        and "all rights reserved" in policy_pages["copyright.html"].lower(),
        "Copyright page is missing the exact owner or all-rights-reserved notice",
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
    for letter, rows in official_rows.items():
        for row in rows:
            for member in row["family_members"]:
                assert_valid_family_pos(
                    member["pos"], f"Ministry List {letter} {row['official_entry']} / {member['word']}"
                )
    official_cards = {
        letter: vocab.merge_official_cards(official_rows[letter]) for letter in "ABCD"
    }
    records_by_group = {}
    records_by_list = defaultdict(list)
    for group in GROUPS:
        path = REPO / f"{group}.html"
        text = path.read_text(encoding="utf-8")
        assert_true(
            f"<title>E-Vocab for Module E - Flashcards Part {group}</title>" in text,
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
            "activity-accessibility-v2",
            'class="skip-link" href="#main-content"',
            'class="activity-top-nav" aria-label="Activity navigation"',
            'class="activity-home" href="index.html"',
            'class="activity-main" id="main-content"',
            'id="flipButton"',
            'id="cardStatus" role="status" aria-live="polite"',
            'id="cardBack" aria-hidden="true" inert',
            'role="group" aria-label="Flashcard controls"',
            "cardFront.inert = isFlipped",
            "document.getElementById('ttsBtn').disabled = isFlipped",
            "side === 'answer' ? 'Answer shown' : 'Word shown'",
            "isFlipped ? 'Answer shown. Show word' : 'Word shown. Show answer'",
            "function scheduleWordSpeech()",
            "}, 900);",
            "function scheduleExampleSpeech()",
            "announceCard('word');\n            scheduleWordSpeech();",
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
        assert_true(
            "speakText(words[currentIndex].ex_en)" not in text,
            f"The answer example should not interrupt screen-reader announcements in {group}.html",
        )
        for filename in POLICY_FILES:
            assert_true(f'href="{filename}"' in text, f"{filename} footer link missing in {group}.html")
        records = vocab.read_html_records(path)
        records_by_group[group] = records
        records_by_list[group[0]].extend(records)
        assert_true(len(records) == EXPECTED_COUNTS[group], f"Unexpected count in {group}: {len(records)}")
        for position, record in enumerate(records, start=1):
            context = f"{group}-{position:03d} {record.get('en', '<missing entry>')}"
            assert_true(record.get("pos"), f"Missing POS in {group}: {record.get('en')}")
            assert_true(record.get("mean_he"), f"Missing Hebrew meaning in {group}: {record.get('en')}")
            assert_true(record.get("ex_en"), f"Missing English example in {group}: {record.get('en')}")
            assert_true(record.get("ex_he"), f"Missing Hebrew example in {context}")
            assert_true(record.get("support_text"), f"Missing A2 support in {group}: {record.get('en')}")
            word_count = english_word_count(record.get("ex_en", ""))
            assert_true(
                word_count <= MAX_EXAMPLE_WORDS,
                f"English example exceeds {MAX_EXAMPLE_WORDS} words in {context}: "
                f"{word_count} words — {record.get('ex_en')}",
            )
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
                re.search(r"[.!?…][”\"׳״]?\s*$", record["ex_he"]) is not None,
                f"Hebrew example lacks terminal punctuation in {context}: {record['ex_he']}",
            )
            normalized_example = re.sub(
                r"[.!?…]+$", "", record["ex_en"].strip().casefold()
            ).strip()
            assert_true(
                normalized_example not in KNOWN_CLEAR_FRAGMENTS,
                f"Known sentence fragment remains in {context}: {record['ex_en']}",
            )
            assert_true(
                PLACEHOLDER_RE.search(record["ex_en"]) is None,
                f"Learner placeholder remains in English example in {context}: {record['ex_en']}",
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
            for word, pos in family_pairs:
                assert_valid_family_pos(pos, f"{group} {record.get('en')} / {word}")

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
        official_entries_by_display = defaultdict(list)
        for row in official_rows[letter]:
            key = vocab.key_text(row["display"])
            if row["official_entry"] not in official_entries_by_display[key]:
                official_entries_by_display[key].append(row["official_entry"])
        for record in records_by_list[letter]:
            display_key = vocab.key_text(record["en"])
            assert_true(
                record["en"] == display_by_key[display_key],
                f"Display capitalization mismatch: List {letter} {record['en']}",
            )
            expected_official_entry = " | ".join(official_entries_by_display[display_key])
            assert_true(
                record.get("official_entry") == expected_official_entry,
                f"Official entry changed: List {letter} {record['en']} {record['pos']}",
            )

    json_rows = json.loads((REPO / "data/vocabulary-master.json").read_text(encoding="utf-8"))
    assert_true(isinstance(json_rows, list), "Master JSON root must be an array")
    assert_true(
        all(isinstance(row, dict) for row in json_rows),
        "Every master JSON row must be an object",
    )
    expected_total = sum(EXPECTED_COUNTS.values())
    assert_true(
        len(json_rows) == expected_total,
        f"Master JSON has {len(json_rows)} rows instead of {expected_total}",
    )

    html_rows = []
    expected_groups = []
    expected_ids = []
    for group in GROUPS:
        for position, record in enumerate(records_by_group[group], start=1):
            source_entry_id = f"{group}-{position:03d}"
            html_rows.append(dict(record))
            expected_groups.append(group)
            expected_ids.append(source_entry_id)

    actual_groups = [row.get("group") for row in json_rows]
    actual_ids = [row.get("source_entry_id") for row in json_rows]
    assert_true(
        actual_groups == expected_groups,
        "Master JSON group sequence differs from the 12 canonical activity groups",
    )
    assert_true(
        actual_ids == expected_ids,
        "Master JSON source_entry_id sequence is not canonical or has been reordered",
    )
    assert_true(
        len(actual_ids) == len(set(actual_ids)),
        "Duplicate source_entry_id in master JSON",
    )
    json_content_rows = []
    for row in json_rows:
        content_row = dict(row)
        content_row.pop("group", None)
        content_row.pop("source_entry_id", None)
        json_content_rows.append(content_row)
    assert_json_matches_html(json_content_rows, html_rows)

    for group in GROUPS:
        group_rows = [row for row in json_rows if row["group"] == group]
        digest = identity_digest(group_rows)
        assert_true(
            digest == EXPECTED_IDENTITY_SHA256[group],
            f"Immutable identity/POS/order changed in {group}: {digest}",
        )
    global_digest = identity_digest(json_rows)
    assert_true(
        global_digest == EXPECTED_GLOBAL_IDENTITY_SHA256,
        f"Global identity/group order changed: {global_digest}",
    )

    json_keys = Counter((row["group"], row["en"], row["pos"]) for row in json_rows)
    assert_true(max(json_keys.values()) == 1, "Duplicate Group + Word/Phrase + POS in master JSON")
    rows_by_id = {row["source_entry_id"]: row for row in json_rows}
    for row in json_rows:
        context = f"{row['source_entry_id']} {row['en']}"
        siblings = row.get("same_entry_record_ids")
        assert_true(
            row.get("record_sense_en") == row.get("support_text") and bool(row.get("record_sense_en")),
            f"Missing or inconsistent English record sense: {context}",
        )
        assert_true(
            row.get("record_sense_he") == row.get("mean_he") and bool(row.get("record_sense_he")),
            f"Missing or inconsistent Hebrew record sense: {context}",
        )
        assert_true(isinstance(row.get("repeated_entry"), bool), f"Invalid repeated-entry flag: {context}")
        assert_true(isinstance(siblings, list), f"Invalid same-entry ID list: {context}")
        assert_true(len(siblings) == len(set(siblings)), f"Duplicate sibling IDs: {context}")
        assert_true(row["source_entry_id"] not in siblings, f"Record links to itself: {context}")
        assert_true(
            row["repeated_entry"] == bool(siblings),
            f"Repeated-entry flag disagrees with sibling links: {context}",
        )
        expected_scope = "record-specific" if siblings else "single-entry"
        assert_true(
            row.get("record_sense_scope") == expected_scope,
            f"Invalid record sense scope: {context}",
        )
        for sibling_id in siblings:
            assert_true(sibling_id in rows_by_id, f"Unknown sibling {sibling_id}: {context}")
            sibling = rows_by_id[sibling_id]
            assert_true(
                vocab.key_text(sibling["en"]) == vocab.key_text(row["en"]),
                f"Sibling spelling mismatch {sibling_id}: {context}",
            )
            assert_true(
                row["source_entry_id"] in sibling.get("same_entry_record_ids", []),
                f"Asymmetric sibling link {sibling_id}: {context}",
            )
        for member in row.get("family_members", []):
            assert_valid_family_pos(
                member["pos"], f"master JSON {row['group']} {row['en']} / {member['word']}"
            )

    content_path = REPO / "data/ab_content.tsv"
    with content_path.open(encoding="utf-8", newline="") as handle:
        content_rows = list(csv.DictReader(handle, delimiter="\t"))
    required_content_columns = set(vocab.CONTENT_COLUMNS)
    assert_true(
        content_rows and required_content_columns.issubset(content_rows[0]),
        "A/B content table is missing record-sense columns",
    )
    ab_rows = [row for row in json_rows if row["group"][0] in "AB"]
    ab_by_key = {
        (row["group"][0], vocab.key_text(row["en"]), row["pos"]): row
        for row in ab_rows
    }
    assert_true(len(content_rows) == len(ab_by_key), "A/B content metadata row-count mismatch")
    for content_row in content_rows:
        key = (content_row["List"], vocab.key_text(content_row["Display"]), content_row["POS"])
        assert_true(key in ab_by_key, f"Unknown A/B content row: {' | '.join(key)}")
        row = ab_by_key[key]
        expected = {
            "Source Entry ID": row["source_entry_id"],
            "Hebrew source": row["mean_he"],
            "A2 definition or synonyms": row["support_text"],
            "English example": row["ex_en"],
            "Hebrew example": row["ex_he"],
            "Record sense (English)": row["record_sense_en"],
            "Record sense (Hebrew)": row["record_sense_he"],
            "Repeated entry": "TRUE" if row["repeated_entry"] else "FALSE",
            "Same-entry record IDs": "; ".join(row["same_entry_record_ids"]),
            "Sense scope": row["record_sense_scope"],
        }
        for field, value in expected.items():
            assert_true(
                content_row.get(field) == value,
                f"A/B content metadata mismatch in {row['source_entry_id']}: {field}",
            )

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

    support_pool, _ = vocab.current_records()
    expected_support_keys = {
        (row["group"], vocab.key_text(row["en"]), row["pos"])
        for row in json_rows
    }
    assert_true(
        set(support_pool) == expected_support_keys,
        "Generator support lookup is not record/group-aware and may collapse repeated senses",
    )

    print("PASS: 12 activities, 982 cards, policies, accessibility controls, privacy checks, archived A–D sources, official coverage, capitalization, punctuation, links and static assets validated.")


if __name__ == "__main__":
    main()
