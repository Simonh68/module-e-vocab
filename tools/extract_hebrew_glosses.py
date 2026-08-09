#!/usr/bin/env python3
"""Extract concise Hebrew glosses for official A/B cards from Milonchik.

Milonchik is an MIT-licensed English–Hebrew dictionary. This script stores
only the reviewed glosses needed by this project, keeping the website build
independent of the external database.
"""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from pathlib import Path

import rebuild_official_vocab as vocab


REPO = Path(__file__).resolve().parents[1]
DICTIONARY = Path("/tmp/module-e-milonchik/Milonchik/Resources/milon.db")
OUTPUT = REPO / "data/hebrew-glosses.json"

MANUAL = {
    # List A phrases and function words
    "among other things|Phrase": "בין היתר",
    "as|Conjunction": "כאשר; מפני ש; כפי ש־",
    "at least|Phrase": "לפחות",
    "be responsible for|Phrase": "להיות אחראי ל־",
    "before|Preposition": "לפני",
    "besides|Adverb": "בנוסף; חוץ מזה",
    "besides|Preposition": "מלבד; נוסף על",
    "can|Verb": "יכול; עשוי",
    "come after/first/last|Phrase": "לבוא אחרי; ראשון; אחרון",
    "conditions|Noun": "תנאים; נסיבות",
    "do|Auxiliary verb": "פועל עזר להדגשה",
    "even if|Phrase": "גם אם",
    "even though|Phrase": "אף על פי ש־",
    "except that|Phrase": "מלבד העובדה ש־",
    "focus on/upon|Phrase": "להתמקד ב־",
    "from|Preposition": "מ־; מאת; החל מ־",
    "in actual fact|Phrase": "למעשה",
    "in connection with|Phrase": "בקשר ל־",
    "in that case|Phrase": "במקרה כזה",
    "in terms of|Phrase": "מבחינת; במונחים של",
    "in the meantime|Phrase": "בינתיים",
    "in|Preposition": "ב־; בתוך; במהלך",
    "just about|Phrase": "כמעט; בערך",
    "keep on doing|Phrase": "להמשיך לעשות",
    "kind of|Phrase": "קצת; מעין",
    "look at|Phrase": "להסתכל על; לבחון",
    "likely|Adverb": "כנראה; קרוב לוודאי",
    "more or less|Phrase": "פחות או יותר",
    "must|Verb": "חייב; מוכרח",
    "nevertheless|Adverb": "למרות זאת; אף על פי כן",
    "not at all|Phrase": "בכלל לא",
    "not only|Phrase": "לא רק",
    "on the one hand ... on the other hand|Phrase": "מצד אחד... מצד שני",
    "once|Conjunction": "ברגע ש־; לאחר ש־",
    "others|Pronoun": "אחרים; אחרות",
    "otherwise|Adverb": "אחרת; באופן אחר",
    "otherwise|Conjunction": "אחרת; אם לא",
    "out of date|Phrase": "מיושן; לא מעודכן",
    "past|Adjective": "קודם; מן העבר",
    "point of view|Phrase": "נקודת מבט",
    "proposed|Adjective": "מוצע",
    "provided that|Phrase": "בתנאי ש־",
    "rely on/upon|Phrase": "להסתמך על; לסמוך על",
    "run out of|Phrase": "להיגמר; לא להישאר עם",
    "set up|Phrase": "להקים; לארגן",
    "take advantage of|Phrase": "לנצל הזדמנות או יתרון",
    "thanks to|Phrase": "הודות ל־",
    "throw away/out|Phrase": "לזרוק; להשליך",
    "unlike|Preposition": "בניגוד ל־; שלא כמו",
    "whom|Pronoun": "את מי; למי",
    "within|Adverb": "בפנים; בתוך הגבול",
    "within|Preposition": "בתוך; תוך",
    "would|Verb": "היה; היה רוצה; פועל עזר",
    # List B phrases, chunks and special display forms
    "above|Adjective": "הנזכר לעיל; שלמעלה",
    "all of a sudden|Phrase": "לפתע; פתאום",
    "be in charge|Phrase": "להיות אחראי; להיות ממונה",
    "be situated in/on/by|Phrase": "להימצא; להיות ממוקם",
    "behind|Adverb": "מאחור; בפיגור",
    "believe in|Phrase": "להאמין ב־",
    "bring up|Phrase": "להעלות נושא; לגדל",
    "cut down|Phrase": "להפחית; לכרות",
    "either way|Phrase": "בכל מקרה; כך או כך",
    "expected|Adjective": "צפוי",
    "farther/further|Adjective": "רחוק יותר; נוסף",
    "farther/further|Adverb": "רחוק יותר; הלאה",
    "fed up|Phrase": "נמאס; עייף ומוטרד",
    "get rid of|Phrase": "להיפטר מ־",
    "get wrong|Phrase": "לטעות ב־; להבין לא נכון",
    "get worse|Phrase": "להחמיר",
    "give away|Phrase": "לתת בחינם; לגלות סוד",
    "go out|Phrase": "לצאת; לכבות",
    "indoors|Adjective": "מקורה; שבתוך מבנה",
    "indoors|Adverb": "בתוך מבנה; פנימה",
    "inside|Adverb": "בפנים; פנימה",
    "it looks like/as if/as though|Phrase": "נראה ש־; כאילו",
    "just as ... as|Phrase": "בדיוק באותה מידה כמו",
    "look forward to|Phrase": "לצפות בשמחה ל־",
    "make sense|Phrase": "להיות הגיוני; להיות מובן",
    "make up your mind|Phrase": "להחליט",
    "make up|Phrase": "להמציא; להרכיב",
    "neither ... nor|Phrase": "לא... ולא...",
    "not ... a word|Phrase": "אף מילה; שום דבר",
    "not until|Phrase": "רק לאחר; לא לפני",
    "on the whole|Phrase": "בסך הכול; באופן כללי",
    "part-time|Phrase": "במשרה חלקית",
    "put up with|Phrase": "לסבול; להשלים עם",
    "shut down|Phrase": "לסגור; להשבית",
    "slow down/up|Phrase": "להאט; להאיץ",
    "so-called|Phrase": "מה שמכונה; כביכול",
    "sooner or later|Phrase": "במוקדם או במאוחר",
    "start off|Phrase": "להתחיל",
    "sum up|Phrase": "לסכם",
    "take into account|Phrase": "להביא בחשבון",
    "take part|Phrase": "להשתתף",
    "take place|Phrase": "להתרחש; להתקיים",
    "take seriously|Phrase": "להתייחס ברצינות",
    "take the opportunity|Phrase": "לנצל את ההזדמנות",
    "take/accept/claim responsibility|Phrase": "לקבל אחריות; ליטול אחריות",
    "the headlines|Phrase": "הכותרות הראשיות",
    "the heart of|Phrase": "לב העניין; המרכז של",
    "the main thing|Phrase": "הדבר העיקרי",
    "the reality of|Phrase": "המציאות של",
    "to start with|Phrase": "בתור התחלה; ראשית",
    "to|Preposition": "ל־; אל; עד",
    "underneath|Adverb": "מתחת; מלמטה",
    "underneath|Preposition": "מתחת ל־",
    "up-to-date|Phrase": "מעודכן; עדכני",
    "use up|Phrase": "לנצל עד תום; לגמור",
    "virtual reality|Phrase": "מציאות מדומה",
    "wherever|Adverb": "בכל מקום שבו; היכן ש־",
}

# Sense-specific corrections where a general dictionary offers secondary
# meanings that are not useful for these Ministry entries.
MANUAL.update({
    "advance|Noun": "התקדמות; קידום",
    "challenge|Verb": "לאתגר; לערער על",
    "change|Verb": "לשנות; להשתנות",
    "common|Adjective": "נפוץ; רגיל; משותף",
    "concern|Verb": "להדאיג; לעסוק ב־; להיות נוגע ל־",
    "critic|Noun": "מבקר; אדם שנותן ביקורת",
    "development|Noun": "התפתחות; פיתוח",
    "essay|Noun": "חיבור; מאמר",
    "feature|Noun": "מאפיין; תכונה",
    "finding/findings|Noun": "ממצא; תוצאות מחקר",
    "flu|Noun": "שפעת",
    "gain|Noun": "רווח; יתרון; עלייה",
    "introduce|Verb": "להציג; לערוך היכרות; להכניס",
    "invest|Verb": "להשקיע",
    "low|Adverb": "נמוך; בגובה או ברמה נמוכים",
    "material|Noun": "חומר; חומר לימוד",
    "means|Noun": "אמצעי; דרך",
    "measure|Noun": "צעד; אמצעי; מידה",
    "participate|Verb": "להשתתף; לקחת חלק",
    "particular|Adjective": "מסוים; מיוחד; ספציפי",
    "plant|Verb": "לשתול",
    "policy|Noun": "מדיניות; כלל רשמי",
    "proof|Noun": "הוכחה; ראיה",
    "recommend|Verb": "להמליץ",
    "regard|Noun": "כבוד; הערכה; התייחסות",
    "regard|Verb": "לראות כ־; להחשיב; להתייחס",
    "sense|Noun": "חוש; תחושה; משמעות",
    "supposed|Adjective": "אמור; לכאורה; משוער",
    "transport|Noun": "תחבורה; הובלה",
    "transport|Verb": "להעביר; להוביל",
    "trash|Noun": "אשפה; זבל",
    "treatment|Noun": "טיפול; יחס",
    "view|Noun": "דעה; השקפה; נוף",
    "visible|Adjective": "נראה לעין; ניתן לראות",
    "volume|Noun": "נפח; כרך; עוצמת קול",
    "altogether|Adverb": "בסך הכול; לגמרי",
    "brilliant|Adjective": "מבריק; מצוין; חכם מאוד",
    "degree|Noun": "מידה; דרגה; תואר",
    "expedition|Noun": "משלחת; מסע מאורגן",
    "fetch|Verb": "להביא; ללכת להביא",
    "final|Noun": "גמר; שלב אחרון",
    "generation|Noun": "דור",
    "incredible|Adjective": "מדהים; לא ייאמן",
    "input|Noun": "קלט; מידע או רעיונות",
    "interrupt|Verb": "להפריע; לקטוע",
    "jam|Noun": "פקק; ריבה",
    "judgment|Noun": "שיקול דעת; שיפוט; החלטה",
    "justice|Noun": "צדק; משפט הוגן",
    "kit|Noun": "ערכה; ציוד",
    "lower|Verb": "להוריד; להנמיך",
    "native|Adjective": "ילידי; מקומי; שפת אם",
    "occupy|Verb": "לתפוס מקום; לאכלס; להעסיק",
    "organ|Noun": "איבר בגוף; אורגן; עוגב",
    "point|Noun": "נקודה; טענה; רעיון",
    "potential|Noun": "פוטנציאל; יכולת עתידית",
    "principal|Noun": "מנהל או מנהלת בית ספר",
    "record|Noun": "רשומה; תיעוד; שיא",
    "register|Noun": "רשימה רשמית; מרשם",
    "relate|Verb": "לקשר; להתייחס; לספר",
    "remark|Verb": "להעיר; לציין",
    "respect|Noun": "כבוד; הערכה",
    "retire|Verb": "לפרוש; לצאת לגמלאות",
    "satisfy|Verb": "לספק; להשביע רצון",
    "shortly|Adverb": "בקרוב; תוך זמן קצר; בקצרה",
    "undo|Verb": "לבטל פעולה; להתיר; לפתוח",
    "vowel|Noun": "תנועה בדיבור או בכתב",
    "waste|Adjective": "מיותר; פסולת; שנותר ללא שימוש",
    "welcome|Verb": "לקבל בברכה; לברך לשלום",
})


def clean_translation(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    value = re.sub(r"\([^)]{20,}\)", "", value)
    value = re.sub(r"\s+", " ", value).strip(" ;")
    return value


def lookup(connection: sqlite3.Connection, word: str, pos: str) -> str:
    candidates = [word.casefold()]
    if "/" in word:
        candidates.extend(part.strip() for part in word.casefold().split("/") if part.strip())
    pos_key = {
        "Noun": "noun",
        "Verb": "verb",
        "Adjective": "adjective",
        "Adverb": "adverb",
        "Preposition": "preposition",
        "Conjunction": "conjunction",
        "Pronoun": "pronoun",
    }.get(pos, "")
    for candidate in candidates:
        rows = connection.execute(
            "SELECT part_of_speech, translations FROM definitions "
            "WHERE translated_lang='eng' AND translated_word_sanitized=?",
            (candidate,),
        ).fetchall()
        ranked = sorted(rows, key=lambda row: row[0] != pos_key)
        for row_pos, raw in ranked:
            if pos_key and row_pos and row_pos != pos_key:
                continue
            parts = []
            for item in raw.split("\t"):
                item = clean_translation(item)
                if item and len(item) <= 42 and item not in parts:
                    parts.append(item)
                if len(parts) == 3:
                    break
            if parts:
                return "; ".join(parts)
    return ""


def main() -> None:
    if not DICTIONARY.exists():
        raise SystemExit(f"Missing Milonchik database: {DICTIONARY}")
    connection = sqlite3.connect(DICTIONARY)
    output = {}
    missing = []
    for letter in "AB":
        cards = vocab.merge_official_cards(vocab.load_official_rows(letter))
        for card in cards:
            key = f"{card['display'].casefold()}|{card['pos']}"
            gloss = MANUAL.get(key) or lookup(connection, card["display"], card["pos"])
            if not gloss:
                missing.append(key)
            output[f"{letter}|{key}"] = gloss
    if missing:
        print("Missing glosses:")
        print("\n".join(missing))
        raise SystemExit(1)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(output)} Hebrew glosses to {OUTPUT}")


if __name__ == "__main__":
    main()
