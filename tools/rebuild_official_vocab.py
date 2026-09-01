#!/usr/bin/env python3
"""Rebuild the Module E activity data from the official Ministry workbooks.

The script keeps the activity HTML files self-contained, but also writes an
auditable JSON source used by the synchronized Excel workbook builder.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import random
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

from accessibility import patch_activity_page

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
OFFICIAL_DIR = REPO / "sources"
CURRENT_MASTER = REPO / "Module_E_2027_Vocabulary_Master.xlsx"
DATA_DIR = REPO / "data"
CONTENT_TSV = DATA_DIR / "ab_content.tsv"
SOURCE_JSON = DATA_DIR / "vocabulary-master.json"

CONTENT_COLUMNS = [
    "List",
    "Display",
    "POS",
    "Source Entry ID",
    "Hebrew source",
    "A2 definition or synonyms",
    "English example",
    "Hebrew example",
    "Record sense (English)",
    "Record sense (Hebrew)",
    "Repeated entry",
    "Same-entry record IDs",
    "Sense scope",
]

OFFICIAL_FILES = {
    "A": OFFICIAL_DIR / "LISTA12.12.21.xlsx",
    "B": OFFICIAL_DIR / "LISTB12.12.21.xlsx",
    "C": OFFICIAL_DIR / "LISTC12.12.21.xlsx",
    "D": OFFICIAL_DIR / "LIST-D.xlsx",
}

OFFICIAL_URLS = {
    "A": "https://meyda.education.gov.il/files/Mazkirut_Pedagogit/English/4Lists/LISTA12.12.21.xlsx",
    "B": "https://meyda.education.gov.il/files/Mazkirut_Pedagogit/English/4Lists/LISTB12.12.21.xlsx",
    "C": "https://meyda.education.gov.il/files/Mazkirut_Pedagogit/English/4Lists/LISTC12.12.21.xlsx",
    "D": "https://meyda.education.gov.il/files/Pop/0files/english/Chativa-Elyona/Bagrut/LIST-D.xlsx",
}

POS_NAMES = {
    "n": "Noun",
    "v": "Verb",
    "adj": "Adjective",
    "adv": "Adverb",
    "prep": "Preposition",
    "conj": "Conjunction",
    "pron": "Pronoun",
    "aux v": "Auxiliary verb",
    "det": "Determiner",
    "exclam": "Exclamation",
}

GRAMMAR = {
    "Noun": "noun",
    "Verb": "verb",
    "Adjective": "adjective",
    "Adverb": "adverb",
    "Preposition": "preposition",
    "Conjunction": "conjunction",
    "Pronoun": "pronoun",
    "Auxiliary verb": "auxiliary verb",
    "Determiner": "determiner",
    "Exclamation": "exclamation",
    "Phrase": "phrase / chunk",
    "Phrasal verb": "phrasal verb",
    "Noun phrase": "noun phrase",
}

# Shortened display forms follow the convention already used in Lists C and D.
DISPLAY_ALIASES = {
    # List A
    "be responsible for sth/doing sth": "be responsible for",
    "come after/first/last, etc": "come after/first/last",
    "focus on/upon sb/sth": "focus on/upon",
    "in ... terms / in terms of sth": "in terms of",
    "in connection with sth": "in connection with",
    "keep on doing sth": "keep on doing",
    "look at sth": "look at",
    "provided (that)": "provided that",
    "rely on/upon sb/sth": "rely on/upon",
    "set up sth or set sth up": "set up",
    "take advantage of sth": "take advantage of",
    "thanks to sb/sth": "thanks to",
    "throw away/out sth or throw sth away/out": "throw away/out",
    # List B
    "be situated in/on/by, etc": "be situated in/on/by",
    "believe in sth": "believe in",
    "bring up sb or bring sb up": "bring up",
    "cut down sth or cut sth down": "cut down",
    "get rid of sth": "get rid of",
    "get sth wrong": "get wrong",
    "give away sth or give sth away": "give away",
    "just as bad / good / tall /clever, etc (as sb/sth)": "just as ... as",
    "look forward to sth/doing sth": "look forward to",
    "make up sth or make sth up": "make up",
    "make up your mind or make your mind up": "make up your mind",
    "not believe / understand / hear / say, etc. a word": "not ... a word",
    "put up with sth/sb": "put up with",
    "shut (sth) down or shut down (sth)": "shut down",
    "slow (sb/sth) down / up or slow down/up (sb/sth)": "slow down/up",
    "start (sth) off or start off (sth)": "start off",
    "sum up (sth/sb) or sum (sth/sb) up": "sum up",
    "take into account sth": "take into account",
    "take the/this opportunity to do sth": "take the opportunity",
    "take sb/sth seriously": "take seriously",
    "take/accept/claim responsibility for sth": "take/accept/claim responsibility",
    "the heart of sth": "the heart of",
    "the reality/realities of sth": "the reality of",
    "use up sth or use sth up": "use up",
    # List C
    "(all) on your own": "on your own",
    "(at) any minute; any minute now": "any minute",
    "(be) in your twenties / 20s /thirties/30s, etc": "in your twenties",
    "(every) once in a while": "once in a while",
    "at his/its, etc. best": "at his best",
    "be (just) about to do sth": "be about to",
    "be out of sth": "be out of",
    "do a good/excellent, etc. job": "do a good job",
    "for the sake of sth/sb; for sth's/sb's sake": "for the sake of",
    "give in/up": "give in",
    "give up sth or give sth up": "give up",
    "here you are/here it is, etc.": "here you are",
    "hold up / hold up sb/sth or hold sb/sth up": "hold up",
    "leave behind sb/sth or leave sb/sth behind": "leave behind",
    "let out sb/sth or let sb/sth out": "let out",
    "let sb/sth in / past / through, etc": "let in",
    "log in/on": "log in",
    "log off/out": "log off",
    "lose interest / patience, etc": "lose interest",
    "remain calm/open, etc": "remain calm",
    "so did we/so have i/so is mine, etc.": "so did we",
    "somewhere around / between, etc.": "somewhere around",
    "sound angry / happy / rude, etc.": "sound angry",
    "speak about/of sth": "speak about",
    "suffer from sth": "suffer from",
    "take pleasure/pride/an interest, etc.": "take pleasure",
    "that kind/sort of thing": "that kind of thing",
    "the following day / morning, etc.": "the following day",
    "tired of doing sth": "tired of doing",
    "turn (sb/sth) into sb/sth": "turn into",
    "wear (sth) out or wear out (sth)": "wear out",
    # List D
    "blow up (sth/sb) or blow (sth/sb) up": "blow up",
    "for fun or for the fun of it": "for fun / for the fun of it",
    "grow tired/old/calm, etc.": "grow tired/old/calm",
    "hurry up sb/sth or hurry sb/sth up": "hurry up",
    "mix up sb/sth or mix sb/sth up": "mix up",
    "rub out sth or rub sth out": "rub out",
    "see off sb or see sb off": "see off",
    "show sb around / round": "show around",
    "shut (sb) up": "shut up",
    "step back / forward / over, etc.": "step back/forward",
    "step on/in sth": "step on",
    "take sb out or take out sb": "take sb out",
    "tie sb/sth up or tie up sb/sth": "tie up",
}

ENTRY_POS_CORRECTIONS = {
    ("B", "behind"): ["Adverb"],
    ("B", "deliver"): ["Verb"],
    ("B", "domestic"): ["Adjective"],
}

FAMILY_POS_CORRECTIONS = {
    "efficiently": "Adverb",
    "skillful": "Adjective",
    "respectable": "Adjective",
    "on average": "Phrase",
    "concerned with sth": "Phrase",
    "cope with sth": "Phrasal verb",
    "figure out sth": "Phrasal verb",
    "interested in sth": "Phrase",
    "old-fashioned": "Adjective",
    "set out sth, set sth out": "Phrasal verb",
    "at the expense of": "Phrase",
    "in light of": "Phrase",
    "made up of": "Phrase",
    "native language": "Noun phrase",
    "traffic jam": "Noun phrase",
    "care for": "Phrasal verb",
    "speed limit": "Noun phrase",
    "cyclist": "Noun",
    "prayer": "Noun",
    "harbour": "Noun",
}

CD_SUPPORT_FALLBACKS = {
    ("hardware", "Noun"): "the physical parts of a computer or machine",
    ("off", "Adverb"): "not operating; away from a place or position",
    ("preposition", "Noun"): "a word placed before a noun or pronoun to show place, time or direction",
    ("liquid", "Noun"): "a substance like water that flows",
    ("powder", "Noun"): "a dry substance made of very small particles",
    ("branch", "Noun"): "a part growing from a tree trunk; a local division of an organization",
    ("drink", "Noun"): "water, juice or another substance taken by mouth",
    ("grow tired/old/calm", "Verb"): "become less energetic, older or more peaceful",
    ("range", "Noun"): "a set of different things; the distance between two limits",
}


def clean_text(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = unicodedata.normalize("NFKC", str(value)).replace("\xa0", " ")
    text = text.replace("…", "...").replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", text).strip()


def cell_lines(value: object) -> list[str]:
    """Split an XLSX cell on line breaks before normalizing whitespace."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    text = unicodedata.normalize("NFKC", str(value)).replace("\xa0", " ")
    return [clean_text(line) for line in re.split(r"[\r\n]+", text) if clean_text(line)]


def smart_english_punctuation(value: object) -> str:
    """Use typographic English punctuation without changing letter case."""
    text = clean_text(value).replace("'", "’")
    return re.sub(r'"([^"\n]+)"', r"“\1”", text)


def normalize_fragment(value: object) -> str:
    """Normalize a definition or label, which does not take terminal punctuation."""
    return re.sub(r"[.!?…;:]+$", "", smart_english_punctuation(value)).strip()


def normalize_hebrew_meaning(value: object) -> str:
    """Use semicolons between glosses and no terminal punctuation."""
    text = re.sub(r"\s*/\s*", "; ", clean_text(value))
    text = re.sub(r"\s*;\s*", "; ", text)
    return re.sub(r"[.!?…;:]+$", "", text).strip()


def key_text(value: object) -> str:
    return clean_text(value).casefold()


def display_entry(official_entry: str) -> str:
    key = key_text(official_entry)
    return smart_english_punctuation(DISPLAY_ALIASES.get(key, clean_text(official_entry)))


def parse_pos(list_letter: str, entry: str, raw_pos: object) -> list[str]:
    correction = ENTRY_POS_CORRECTIONS.get((list_letter, key_text(entry)))
    if correction:
        return correction
    raw = key_text(raw_pos)
    if not raw:
        return ["Phrase"]
    return [POS_NAMES.get(part.strip(), part.strip().title()) for part in raw.split(",")]


def family_pos_label(raw: str) -> str:
    raw = key_text(raw)
    if not raw:
        return "Phrase"
    return ", ".join(POS_NAMES.get(part.strip(), part.strip().title()) for part in raw.split(","))


def parse_family(raw_words: object, raw_pos: object, entry: str) -> list[dict[str, str]]:
    if not clean_text(raw_words):
        return []
    words = cell_lines(raw_words)
    poses = cell_lines(raw_pos)
    if len(poses) == 1 and len(words) > 1:
        poses *= len(words)
    family = []
    for index, word in enumerate(words):
        # Ministry sheets occasionally repeat the entry itself as a family member.
        if key_text(word) == key_text(entry):
            continue
        correction = FAMILY_POS_CORRECTIONS.get(key_text(word))
        raw_label = poses[index] if index < len(poses) else ""
        if not raw_label and not correction:
            raise RuntimeError(f"Missing family POS for {entry}: {word}")
        label = correction or family_pos_label(raw_label)
        family.append({"word": smart_english_punctuation(word), "pos": label})
    return family


def load_official_rows(list_letter: str) -> list[dict]:
    frame = pd.read_excel(OFFICIAL_FILES[list_letter], header=None, dtype=object).iloc[5:]
    rows = []
    for _, row in frame.iterrows():
        official = clean_text(row.iloc[0])
        if not official:
            continue
        rows.append(
            {
                "list": list_letter,
                "official_entry": official,
                "display": display_entry(official),
                "poses": parse_pos(list_letter, official, row.iloc[1]),
                "family_members": parse_family(row.iloc[3], row.iloc[4], official),
                "official_meaning": clean_text(row.iloc[5]),
                "rec_prod": clean_text(row.iloc[6]),
            }
        )
    return rows


def merge_official_cards(rows: list[dict]) -> list[dict]:
    cards: dict[tuple[str, str], dict] = {}
    for row in rows:
        for pos in row["poses"]:
            key = (key_text(row["display"]), pos)
            if key not in cards:
                cards[key] = {
                    "list": row["list"],
                    "official_entries": [],
                    "display": row["display"],
                    "pos": pos,
                    "family_members": [],
                    "official_meanings": [],
                    "rec_prod": row["rec_prod"],
                }
            card = cards[key]
            if row["official_entry"] not in card["official_entries"]:
                card["official_entries"].append(row["official_entry"])
            if row["official_meaning"] and row["official_meaning"] not in card["official_meanings"]:
                card["official_meanings"].append(row["official_meaning"])
            seen = {(x["word"], x["pos"]) for x in card["family_members"]}
            for member in row["family_members"]:
                pair = (member["word"], member["pos"])
                if pair not in seen:
                    card["family_members"].append(member)
                    seen.add(pair)
    return list(cards.values())


def read_html_records(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"const\s+words\s*=\s*(\[.*?\]);\s*</script>", text, re.S)
    if not match:
        raise RuntimeError(f"Could not find words array in {path}")
    return json.loads(match.group(1))


def current_records() -> tuple[dict[tuple[str, str, str], dict], dict[str, list[dict]]]:
    """Read current support data without collapsing same-word/same-POS senses."""
    pool: dict[tuple[str, str, str], dict] = {}
    groups: dict[str, list[dict]] = {}
    workbook = pd.read_excel(CURRENT_MASTER, sheet_name="Vocabulary", dtype=object)
    by_key = {}
    for _, row in workbook.iterrows():
        key = (
            clean_text(row["Group"]),
            key_text(row["Word / Phrase"]),
            clean_text(row["POS"]),
        )
        by_key[key] = {
            "support_type": clean_text(row["Support Type"]),
            "support_text": clean_text(row["A2 Definition / Synonyms"]),
            "boundary_examples": clean_text(row["Boundary Examples"]),
        }
    for letter in "ABCD":
        for number in range(1, 4):
            group = f"{letter}{number}"
            records = read_html_records(REPO / f"{group}.html")
            groups[group] = records
            for record in records:
                key = (group, key_text(record["en"]), clean_text(record["pos"]))
                merged = dict(record)
                merged.update(by_key.get(key, {}))
                pool.setdefault(key, merged)
    return pool, groups


def write_content_template(cards: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CONTENT_TSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(CONTENT_COLUMNS)
        for card in sorted(cards, key=lambda x: (x["list"], key_text(x["display"]), x["pos"])):
            writer.writerow(
                [
                    card["list"],
                    card["display"],
                    card["pos"],
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )


def load_content() -> dict[tuple[str, str, str], dict[str, str]]:
    if not CONTENT_TSV.exists():
        raise RuntimeError(f"Missing curated content file: {CONTENT_TSV}")
    result = {}
    with CONTENT_TSV.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required_columns = set(CONTENT_COLUMNS)
        missing_columns = required_columns - set(reader.fieldnames or [])
        if missing_columns:
            raise RuntimeError(
                f"Missing required column(s) in {CONTENT_TSV}: "
                + ", ".join(sorted(missing_columns))
            )
        for row in reader:
            key = (row["List"], key_text(row["Display"]), row["POS"])
            if key in result:
                raise RuntimeError(
                    f"Duplicate curated content row: {' | '.join(key)}"
                )
            result[key] = {
                "hebrew_source": clean_text(row["Hebrew source"]),
                "support_text": clean_text(row["A2 definition or synonyms"]),
                "example": clean_text(row["English example"]),
                "hebrew_example": clean_text(row["Hebrew example"]),
            }
    return result


def attach_record_sense_metadata(groups: dict[str, list[dict]]) -> None:
    """Bind meaning to a record ID and link every repeated displayed entry."""
    ordered_groups = [f"{letter}{number}" for letter in "ABCD" for number in range(1, 4)]
    indexed: list[tuple[str, dict]] = []
    by_entry: dict[str, list[str]] = defaultdict(list)
    for group in ordered_groups:
        for index, record in enumerate(groups[group], start=1):
            record_id = f"{group}-{index:03d}"
            indexed.append((record_id, record))
            by_entry[key_text(record["en"])].append(record_id)

    for record_id, record in indexed:
        siblings = [
            sibling_id
            for sibling_id in by_entry[key_text(record["en"])]
            if sibling_id != record_id
        ]
        record["record_sense_en"] = record["support_text"]
        record["record_sense_he"] = record["mean_he"]
        record["repeated_entry"] = bool(siblings)
        record["same_entry_record_ids"] = siblings
        record["record_sense_scope"] = "record-specific" if siblings else "single-entry"


def synchronize_content_sense_metadata(groups: dict[str, list[dict]]) -> None:
    """Keep the A/B curation rows explicit about record identity and sense."""
    metadata = {}
    for letter in "AB":
        for number in range(1, 4):
            group = f"{letter}{number}"
            for index, record in enumerate(groups[group], start=1):
                key = (letter, key_text(record["en"]), record["pos"])
                if key in metadata:
                    raise RuntimeError(f"Duplicate A/B metadata key: {' | '.join(key)}")
                metadata[key] = {
                    "Source Entry ID": f"{group}-{index:03d}",
                    "Record sense (English)": record["record_sense_en"],
                    "Record sense (Hebrew)": record["record_sense_he"],
                    "Repeated entry": "TRUE" if record["repeated_entry"] else "FALSE",
                    "Same-entry record IDs": "; ".join(record["same_entry_record_ids"]),
                    "Sense scope": record["record_sense_scope"],
                }

    with CONTENT_TSV.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    for row in rows:
        key = (row["List"], key_text(row["Display"]), row["POS"])
        if key not in metadata:
            raise RuntimeError(f"No generated record matches curated row: {' | '.join(key)}")
        row.update(metadata[key])
    if len(rows) != len(metadata):
        raise RuntimeError(
            f"A/B metadata coverage mismatch: TSV={len(rows)}, generated={len(metadata)}"
        )
    with CONTENT_TSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CONTENT_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def support_route(text: str) -> tuple[str, list[str]]:
    """Classify concise glosses as synonyms; keep explanatory text as a definition."""
    parts = [clean_text(part) for part in re.split(r"[;,]", text) if clean_text(part)]
    definition_signals = {
        "a", "an", "the", "to", "be", "being", "become", "make", "used", "connected",
        "happening", "having", "someone", "something", "people", "person", "thing", "things",
        "place", "time", "way", "amount", "number", "which", "that", "when", "where", "who",
    }
    words = re.findall(r"[a-z]+", text.casefold())
    looks_like_synonyms = (
        len(parts) >= 1
        and len(words) <= 7
        and all(len(re.findall(r"[a-z]+", part.casefold())) <= 3 for part in parts)
        and not definition_signals.intersection(words)
    )
    return ("A2 synonym(s)", parts) if looks_like_synonyms else ("A2 definition", [])


def attach_families_to_existing(
    list_letter: str, groups: dict[str, list[dict]], rows: list[dict]
) -> None:
    family_by_display = defaultdict(list)
    official_by_display = defaultdict(list)
    natural_display = {}
    for row in rows:
        display_key = key_text(row["display"])
        natural_display[display_key] = row["display"]
        official_by_display[display_key].append(row["official_entry"])
        seen = {(x["word"], x["pos"]) for x in family_by_display[display_key]}
        for member in row["family_members"]:
            pair = (member["word"], member["pos"])
            if pair not in seen:
                family_by_display[display_key].append(member)
                seen.add(pair)
    for number in range(1, 4):
        group = f"{list_letter}{number}"
        for record in groups[group]:
            key = key_text(record["en"])
            if key not in official_by_display:
                raise RuntimeError(f"No official {list_letter} row matched {record['en']} in {group}")
            record["en"] = natural_display[key]
            record["official_entry"] = " | ".join(official_by_display[key])
            record["family_members"] = family_by_display[key]


def build_ab_groups(cards: list[dict], content: dict) -> dict[str, list[dict]]:
    generated = []
    missing_content = []
    for card in cards:
        key = (card["list"], key_text(card["display"]), card["pos"])
        curated = content.get(key)
        if (
            not curated
            or not curated["hebrew_source"]
            or not curated["support_text"]
            or not curated["example"]
            or not curated["hebrew_example"]
        ):
            missing_content.append(key)
            continue
        support_text = normalize_fragment(curated["support_text"])
        route, synonyms = support_route(support_text)
        record = {
            "en": card["display"],
            "pos": card["pos"],
            "grammar": GRAMMAR.get(card["pos"], card["pos"].lower()),
            "mean_he": normalize_hebrew_meaning(curated["hebrew_source"]),
            "mean_fr": "-",
            "ex_en": smart_english_punctuation(curated["example"]),
            "ex_he": curated["hebrew_example"],
            "ex_fr": "-",
            "synonyms": synonyms,
            "official_entry": " | ".join(card["official_entries"]),
            "family_members": card["family_members"],
            "support_type": route,
            "support_text": support_text,
            "boundary_examples": "",
            "rec_prod": card["rec_prod"],
            "source_url": OFFICIAL_URLS[card["list"]],
        }
        generated.append(record)
    if missing_content:
        sample = "\n".join(" | ".join(x) for x in missing_content[:20])
        raise RuntimeError(f"Missing curated content for {len(missing_content)} cards:\n{sample}")

    result = {}
    for letter in "AB":
        letter_cards = [r for r in generated if r["source_url"] == OFFICIAL_URLS[letter]]
        random.Random(f"Module E 2027 official List {letter}").shuffle(letter_cards)
        sizes = [len(letter_cards) // 3] * 3
        for i in range(len(letter_cards) % 3):
            sizes[i] += 1
        cursor = 0
        for index, size in enumerate(sizes, start=1):
            result[f"{letter}{index}"] = letter_cards[cursor : cursor + size]
            cursor += size
    return result


def replace_words_array(path: Path, records: list[dict]) -> None:
    text = path.read_text(encoding="utf-8")
    payload = json.dumps(records, ensure_ascii=False, separators=(",", ":"))
    replaced, count = re.subn(
        r"const\s+words\s*=\s*\[.*?\];\s*</script>",
        f"const words = {payload};\n    </script>",
        text,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError(f"Could not replace words array in {path}")
    path.write_text(replaced, encoding="utf-8")


def patch_family_ui(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if ".family-box" not in text:
        css = """

        .back-details-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.25fr) minmax(0, 0.9fr);
            gap: 12px;
            align-items: stretch;
        }

        .back-details-grid.family-empty {
            grid-template-columns: 1fr;
        }

        .family-box {
            background: #ecfdf5;
            border-left: 4px solid #22c55e;
            padding: 10px 12px;
            border-radius: 0 10px 10px 0;
            font-size: 0.82rem;
            color: #166534;
        }

        .family-title {
            font-weight: 800;
            margin-bottom: 6px;
            color: #15803d;
        }

        .family-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .family-word {
            font-weight: 700;
        }

        .family-pos {
            color: #4b5563;
            font-size: 0.76rem;
        }

        @media (max-width: 520px) {
            .back-details-grid {
                grid-template-columns: 1fr;
            }
        }
"""
        text = text.replace("        /* Navigation Controls */", css + "\n        /* Navigation Controls */")

    old_markup = """                <div class="example-box">
                    <div class="example-en" id="exEn">-</div>
                    <div class="example-trans he" id="exHe">-</div>
                </div>"""
    new_markup = """                <div class="back-details-grid" id="backDetailsGrid">
                    <div class="example-box">
                        <div class="example-en" id="exEn">-</div>
                        <div class="example-trans he" id="exHe">-</div>
                    </div>
                    <div class="family-box" id="familyBox">
                        <div class="family-title">Family Members</div>
                        <ul class="family-list" id="familyList"></ul>
                    </div>
                </div>"""
    if old_markup in text:
        text = text.replace(old_markup, new_markup, 1)
    elif 'id="familyBox"' not in text:
        raise RuntimeError(f"Could not add family markup to {path}")

    family_js = """            document.getElementById('exEn').innerText = item.ex_en || '';
            const exHe = document.getElementById('exHe');
            exHe.innerText = item.ex_he || '';
            exHe.style.display = item.ex_he ? 'block' : 'none';

            const familyBox = document.getElementById('familyBox');
            const familyList = document.getElementById('familyList');
            const backDetailsGrid = document.getElementById('backDetailsGrid');
            familyList.replaceChildren();
            if (item.family_members && item.family_members.length > 0) {
                familyBox.style.display = 'block';
                backDetailsGrid.classList.remove('family-empty');
                item.family_members.forEach(member => {
                    const listItem = document.createElement('li');
                    const word = document.createElement('span');
                    const pos = document.createElement('span');
                    word.className = 'family-word';
                    pos.className = 'family-pos';
                    word.textContent = member.word;
                    pos.textContent = ` — ${String(member.pos || '').toLowerCase()}`;
                    listItem.append(word, pos);
                    familyList.appendChild(listItem);
                });
            } else {
                familyBox.style.display = 'none';
                backDetailsGrid.classList.add('family-empty');
            }
"""
    # Replace the whole dynamic back-card section every time. This keeps the
    # generator idempotent and removes stale or accidentally duplicated blocks.
    dynamic_section = re.compile(
        r"            document\.getElementById\('exEn'\)\.innerText = item\.ex_en \|\| '';\n"
        r".*?"
        r"(?=            document\.getElementById\('counter'\)\.innerText =)",
        re.S,
    )
    text, count = dynamic_section.subn(family_js, text, count=1)
    if count != 1:
        raise RuntimeError(f"Could not normalize family JS in {path}")
    text = text.replace(
        "document.getElementById('posBadge').innerText = item.pos || '';",
        "document.getElementById('posBadge').innerText = (item.pos || '').toUpperCase();",
        1,
    )
    path.write_text(text, encoding="utf-8")


def build_source_json(groups: dict[str, list[dict]]) -> None:
    rows = []
    for group in [f"{letter}{number}" for letter in "ABCD" for number in range(1, 4)]:
        for index, record in enumerate(groups[group], start=1):
            row = dict(record)
            row["group"] = group
            row["source_entry_id"] = f"{group}-{index:03d}"
            rows.append(row)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def validate(groups: dict[str, list[dict]], official_cards: dict[str, list[dict]]) -> None:
    for letter in "AB":
        expected = {(key_text(c["display"]), c["pos"]) for c in official_cards[letter]}
        actual = {
            (key_text(r["en"]), r["pos"])
            for number in range(1, 4)
            for r in groups[f"{letter}{number}"]
        }
        if actual != expected:
            raise RuntimeError(
                f"List {letter} mismatch: missing={sorted(expected-actual)[:10]}, extra={sorted(actual-expected)[:10]}"
            )
    for group, records in groups.items():
        for record in records:
            definition = key_text(record.get("support_text", ""))
            target = key_text(record["en"])
            if not definition:
                raise RuntimeError(f"Missing support text: {group} {record['en']} {record['pos']}")
            if target and re.search(rf"\b{re.escape(target)}\b", definition):
                raise RuntimeError(f"Target repeated in definition: {group} {record['en']} -> {definition}")
            if not record.get("mean_he") or not record.get("ex_en") or not record.get("ex_he"):
                raise RuntimeError(f"Incomplete card: {group} {record['en']} {record['pos']}")
            if record.get("record_sense_en") != record.get("support_text"):
                raise RuntimeError(f"Record English sense mismatch: {group} {record['en']} {record['pos']}")
            if record.get("record_sense_he") != record.get("mean_he"):
                raise RuntimeError(f"Record Hebrew sense mismatch: {group} {record['en']} {record['pos']}")
            expected_scope = "record-specific" if record.get("repeated_entry") else "single-entry"
            if record.get("record_sense_scope") != expected_scope:
                raise RuntimeError(f"Record sense scope mismatch: {group} {record['en']} {record['pos']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true", help="Write the A/B content TSV template only")
    args = parser.parse_args()

    rows = {letter: load_official_rows(letter) for letter in "ABCD"}
    official_cards = {letter: merge_official_cards(rows[letter]) for letter in "ABCD"}
    if args.prepare:
        write_content_template(official_cards["A"] + official_cards["B"])
        print(f"Wrote {CONTENT_TSV} with {len(official_cards['A']) + len(official_cards['B'])} cards")
        return

    pool, groups = current_records()
    content = load_content()
    groups.update(build_ab_groups(official_cards["A"] + official_cards["B"], content))
    attach_families_to_existing("C", groups, rows["C"])
    attach_families_to_existing("D", groups, rows["D"])

    # Existing C/D support data is preserved from the synchronized workbook.
    for letter in "CD":
        for number in range(1, 4):
            group = f"{letter}{number}"
            for record in groups[group]:
                current = pool[(group, key_text(record["en"]), record["pos"])]
                record["grammar"] = GRAMMAR.get(record["pos"], record["pos"].lower())
                record["mean_he"] = normalize_hebrew_meaning(
                    record.get("mean_he") or record.get("he", "")
                )
                record["mean_fr"] = record.get("mean_fr", "-")
                record["ex_en"] = smart_english_punctuation(record.get("ex_en", ""))
                record["ex_fr"] = record.get("ex_fr", "-")
                record["synonyms"] = [
                    normalize_fragment(item) for item in record.get("synonyms", [])
                ]
                record["support_type"] = current.get("support_type", "A2 definition")
                record["support_text"] = normalize_fragment(
                    current.get("support_text", "") or CD_SUPPORT_FALLBACKS.get(
                        (key_text(record["en"]), record["pos"]), ""
                    )
                )
                record["boundary_examples"] = normalize_fragment(
                    current.get("boundary_examples", "")
                )
                record["rec_prod"] = ""
                record["source_url"] = OFFICIAL_URLS[letter]

    attach_record_sense_metadata(groups)
    synchronize_content_sense_metadata(groups)
    validate(groups, official_cards)
    for group, records in groups.items():
        replace_words_array(REPO / f"{group}.html", records)
        patch_family_ui(REPO / f"{group}.html")
        patch_activity_page(REPO / f"{group}.html")
    build_source_json(groups)
    print("Rebuilt groups:", ", ".join(f"{g}={len(v)}" for g, v in groups.items()))


if __name__ == "__main__":
    main()
