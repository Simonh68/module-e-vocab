#!/usr/bin/env python3
"""Apply the shared accessibility shell to every flashcard activity page."""

from __future__ import annotations

import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
CURRENT_GROUPS = [f"{letter}{number}.html" for letter in "ABCD" for number in range(1, 4)]
LEGACY_GROUPS = ["A1v2.html", "A2v2.html", "A3v2.html"]
ACTIVITY_FILES = CURRENT_GROUPS + LEGACY_GROUPS

ACCESSIBILITY_CSS = r"""

        /* activity-accessibility-v1 */
        html {
            -webkit-text-size-adjust: 100%;
            text-size-adjust: 100%;
        }

        .skip-link {
            position: fixed;
            top: -100px;
            left: 12px;
            z-index: 1000;
            padding: 10px 14px;
            border-radius: 8px;
            background: #111827;
            color: #ffffff;
            font-weight: 800;
            text-decoration: none;
        }

        .skip-link:focus {
            top: 12px;
        }

        .activity-main {
            width: 100%;
            flex: 1 0 auto;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .sr-only {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }

        button:focus-visible,
        a:focus-visible {
            outline: 3px solid #b45309;
            outline-offset: 4px;
        }

        .flip-btn {
            background-color: #ede9fe;
            border-color: #8b5cf6;
            color: #4c1d95;
        }

        .nav-container {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 10px;
        }

        .nav-container .nav-btn {
            min-width: 0;
            justify-content: center;
            padding: 12px 10px;
        }

        .legal-footer {
            width: 100%;
            max-width: 640px;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 8px 16px;
            padding: 18px 10px 2px;
            color: var(--text-muted);
            font-size: 0.78rem;
            line-height: 1.5;
            text-align: center;
        }

        .legal-footer a {
            color: var(--primary-hover);
            font-weight: 700;
        }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                scroll-behavior: auto !important;
            }

            .card,
            .tts-btn,
            .nav-btn {
                transition: none !important;
            }
        }

        @media (max-width: 380px) {
            .nav-container { gap: 6px; }
            .nav-container .nav-btn { padding: 10px 4px; font-size: 0.8rem; }
            .nav-container .nav-btn svg { display: none; }
        }

        @media (forced-colors: active) {
            .card,
            .card-face,
            .tts-btn,
            .nav-btn {
                border: 1px solid ButtonText;
            }
        }
"""

LEGAL_FOOTER = """    <footer class="legal-footer" aria-label="Site information">
        <a href="index.html">Home</a>
        <a href="about.html">About</a>
        <a href="accessibility.html">Accessibility</a>
        <a href="privacy.html">Privacy</a>
        <a href="copyright.html">Copyright</a>
    </footer>

"""


def require_replace(text: str, old: str, new: str, path: Path, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Could not patch {label} in {path.name}")
    return text.replace(old, new, 1)


def patch_activity_page(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "activity-accessibility-v1" in text:
        if "grid-template-columns: repeat(3, minmax(0, 1fr));" not in text:
            text = text.replace(
                "        .flip-btn {\n"
                "            background-color: #ede9fe;\n"
                "            border-color: #8b5cf6;\n"
                "            color: #4c1d95;\n"
                "        }\n",
                "        .flip-btn {\n"
                "            background-color: #ede9fe;\n"
                "            border-color: #8b5cf6;\n"
                "            color: #4c1d95;\n"
                "        }\n\n"
                "        .nav-container {\n"
                "            display: grid;\n"
                "            grid-template-columns: repeat(3, minmax(0, 1fr));\n"
                "            gap: 10px;\n"
                "        }\n\n"
                "        .nav-container .nav-btn {\n"
                "            min-width: 0;\n"
                "            justify-content: center;\n"
                "            padding: 12px 10px;\n"
                "        }\n",
                1,
            )
            text = text.replace(
                "        @media (forced-colors: active) {",
                "        @media (max-width: 380px) {\n"
                "            .nav-container { gap: 6px; }\n"
                "            .nav-container .nav-btn { padding: 10px 4px; font-size: 0.8rem; }\n"
                "            .nav-container .nav-btn svg { display: none; }\n"
                "        }\n\n"
                "        @media (forced-colors: active) {",
                1,
            )
        text = text.replace(
            '<div class="counter" id="counter" role="status" aria-live="polite" aria-atomic="true">1 / 1</div>',
            '<div class="counter" id="counter">1 / 1</div>',
            1,
        )
        text = text.replace(
            '<div class="counter" id="counter" aria-label="Card position">1 / 1</div>',
            '<div class="counter" id="counter">1 / 1</div>',
            1,
        )
        text = text.replace(
            'role="group" aria-labelledby="wordEn" aria-describedby="cardInstructions"',
            'role="group" aria-label="Flashcard" aria-describedby="cardInstructions"',
            1,
        )
        text = text.replace(
            'id="cardBack" aria-hidden="true">',
            'id="cardBack" aria-hidden="true" inert>',
            1,
        )
        text = text.replace(
            '<div class="nav-container" aria-label="Flashcard controls">',
            '<div class="nav-container" role="group" aria-label="Flashcard controls">',
            1,
        )
        text = text.replace(
            "            document.getElementById('cardFront').setAttribute('aria-hidden', 'false');\n"
            "            document.getElementById('cardBack').setAttribute('aria-hidden', 'true');",
            "            const cardFront = document.getElementById('cardFront');\n"
            "            const cardBack = document.getElementById('cardBack');\n"
            "            cardFront.setAttribute('aria-hidden', 'false');\n"
            "            cardBack.setAttribute('aria-hidden', 'true');\n"
            "            cardFront.inert = false;\n"
            "            cardBack.inert = true;\n"
            "            document.getElementById('ttsBtn').disabled = false;",
            1,
        )
        text = text.replace(
            "            document.getElementById('cardFront').setAttribute('aria-hidden', String(isFlipped));\n"
            "            document.getElementById('cardBack').setAttribute('aria-hidden', String(!isFlipped));",
            "            const cardFront = document.getElementById('cardFront');\n"
            "            const cardBack = document.getElementById('cardBack');\n"
            "            cardFront.setAttribute('aria-hidden', String(isFlipped));\n"
            "            cardBack.setAttribute('aria-hidden', String(!isFlipped));\n"
            "            cardFront.inert = isFlipped;\n"
            "            cardBack.inert = !isFlipped;\n"
            "            document.getElementById('ttsBtn').disabled = isFlipped;",
            1,
        )
        path.write_text(text, encoding="utf-8")
        return

    text = require_replace(text, "    </style>", ACCESSIBILITY_CSS + "    </style>", path, "CSS")
    text = require_replace(
        text,
        "<body>\n",
        '<body>\n    <a class="skip-link" href="#main-content">Skip to main content</a>\n',
        path,
        "skip link",
    )
    text, count = re.subn(
        r'<div class="title">(.*?)</div>',
        r'<h1 class="title">\1</h1>',
        text,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"Could not patch title in {path.name}")
    text = require_replace(
        text,
        '<div class="counter" id="counter">1 / 1</div>',
        '<div class="counter" id="counter">1 / 1</div>',
        path,
        "counter",
    )
    text = require_replace(
        text,
        '    <div class="container" id="cardContainer">',
        '    <main class="activity-main" id="main-content">\n    <div class="container" id="cardContainer">',
        path,
        "main landmark",
    )
    text = require_replace(
        text,
        '<div class="card" id="flashcard" onclick="toggleCard()">',
        '<div class="card" id="flashcard" role="group" aria-label="Flashcard" aria-describedby="cardInstructions" onclick="toggleCard()">',
        path,
        "card group",
    )
    text = require_replace(
        text,
        '<div class="card-face">',
        '<div class="card-face" id="cardFront" aria-hidden="false">',
        path,
        "front face",
    )
    text = require_replace(
        text,
        '<div class="card-face card-back">',
        '<div class="card-face card-back" id="cardBack" aria-hidden="true" inert>',
        path,
        "back face",
    )
    text = require_replace(
        text,
        '<button class="tts-btn" id="ttsBtn" onclick="playAudio(event)" title="Listen">',
        '<button type="button" class="tts-btn" id="ttsBtn" onclick="playAudio(event)" aria-label="Listen to the word" title="Listen to the word">',
        path,
        "speech button",
    )
    text = text.replace(
        '<svg viewBox=',
        '<svg aria-hidden="true" focusable="false" viewBox=',
    )
    text = text.replace(
        '<span class="trans-he" id="transHe">',
        '<span class="trans-he" id="transHe" lang="he" dir="rtl">',
        1,
    )
    text = text.replace(
        '<div class="example-trans he" id="exHe">',
        '<div class="example-trans he" id="exHe" lang="he" dir="rtl">',
        1,
    )
    text = require_replace(
        text,
        '    </div>\n\n    <div class="nav-container">',
        '        <p class="sr-only" id="cardInstructions">Use Show answer to flip the card. Use Previous and Next to move between cards.</p>\n'
        '        <div class="sr-only" id="cardStatus" role="status" aria-live="polite" aria-atomic="true"></div>\n'
        '    </div>\n\n    <div class="nav-container" role="group" aria-label="Flashcard controls">',
        path,
        "card instructions",
    )
    text = text.replace('<button class="nav-btn"', '<button type="button" class="nav-btn"')
    text = require_replace(
        text,
        '        </button>\n        <button type="button" class="nav-btn" onclick="nextCard()">',
        '        </button>\n'
        '        <button type="button" class="nav-btn flip-btn" id="flipButton" onclick="toggleCard(event)" aria-controls="cardFront cardBack" aria-pressed="false">Show answer</button>\n'
        '        <button type="button" class="nav-btn" onclick="nextCard()">',
        path,
        "flip button",
    )
    text, count = re.subn(
        r'(    <div class="jump-container"[^>]*>.*?    </div>)\n\s*(    <script>)',
        r'\1\n    </main>\n\n' + LEGAL_FOOTER + r'\2',
        text,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError(f"Could not close main or add footer in {path.name}")

    reset_state = """            const card = document.getElementById('flashcard');
            card.classList.remove('is-flipped');
            const cardFront = document.getElementById('cardFront');
            const cardBack = document.getElementById('cardBack');
            cardFront.setAttribute('aria-hidden', 'false');
            cardBack.setAttribute('aria-hidden', 'true');
            cardFront.inert = false;
            cardBack.inert = true;
            document.getElementById('ttsBtn').disabled = false;
            const flipButton = document.getElementById('flipButton');
            flipButton.setAttribute('aria-pressed', 'false');
            flipButton.textContent = 'Show answer';"""
    text = require_replace(
        text,
        "            document.getElementById('flashcard').classList.remove('is-flipped');",
        reset_state,
        path,
        "card state reset",
    )
    text = require_replace(
        text,
        "            document.getElementById('counter').innerText = `${currentIndex + 1} / ${words.length}`;",
        "            document.getElementById('counter').innerText = `${currentIndex + 1} / ${words.length}`;\n"
        "            announceCard('word');",
        path,
        "card announcement",
    )

    accessible_toggle = r"""        function announceCard(side) {
            const item = words[currentIndex];
            const sideText = side === 'answer' ? 'Answer side' : 'Word side';
            document.getElementById('cardStatus').textContent =
                `Card ${currentIndex + 1} of ${words.length}. ${item.en}, ${item.pos}. ${sideText}.`;
        }

        function toggleCard(event) {
            if (event) event.stopPropagation();
            hasUserInteracted = true;
            const card = document.getElementById('flashcard');
            const isFlipped = card.classList.toggle('is-flipped');
            const cardFront = document.getElementById('cardFront');
            const cardBack = document.getElementById('cardBack');
            cardFront.setAttribute('aria-hidden', String(isFlipped));
            cardBack.setAttribute('aria-hidden', String(!isFlipped));
            cardFront.inert = isFlipped;
            cardBack.inert = !isFlipped;
            document.getElementById('ttsBtn').disabled = isFlipped;
            const flipButton = document.getElementById('flipButton');
            flipButton.setAttribute('aria-pressed', String(isFlipped));
            flipButton.textContent = isFlipped ? 'Show word' : 'Show answer';
            announceCard(isFlipped ? 'answer' : 'word');

            if (isFlipped) {
                speakText(words[currentIndex].ex_en);
            }
        }

"""
    text, count = re.subn(
        r"        function toggleCard\(\) \{.*?(?=        function nextCard\(\))",
        accessible_toggle,
        text,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError(f"Could not patch toggleCard in {path.name}")

    keyboard_handler = r"""        document.addEventListener('keydown', (event) => {
            if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey) return;
            if (event.key === 'ArrowRight') {
                event.preventDefault();
                nextCard();
            }
            if (event.key === 'ArrowLeft') {
                event.preventDefault();
                prevCard();
            }
        });
"""
    text, count = re.subn(
        r"        document\.addEventListener\('keydown', \(e\) => \{.*?        \}\);",
        keyboard_handler.rstrip(),
        text,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError(f"Could not patch keyboard handler in {path.name}")
    text, count = re.subn(
        r"\n        document\.body\.addEventListener\('click', \(\) => \{.*?        \}, \{ once: true \}\);\n",
        "\n",
        text,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError(f"Could not remove automatic body speech in {path.name}")

    path.write_text(text, encoding="utf-8")


def main() -> None:
    for filename in ACTIVITY_FILES:
        patch_activity_page(REPO / filename)
    print(f"Applied accessible activity shell to {len(ACTIVITY_FILES)} files.")


if __name__ == "__main__":
    main()
