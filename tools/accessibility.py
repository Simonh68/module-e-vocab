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

        /* activity-accessibility-v2 */
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

        .activity-top-nav {
            width: 100%;
            max-width: 480px;
            min-height: 44px;
            position: sticky;
            top: 8px;
            z-index: 40;
            display: flex;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 6px;
            pointer-events: none;
        }

        .activity-home,
        .audio-start {
            min-height: 44px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 7px;
            padding: 8px 13px;
            border: 1px solid #c7d2fe;
            border-radius: 12px;
            color: var(--primary-hover);
            background: rgba(255, 255, 255, 0.96);
            box-shadow: 0 3px 10px rgba(30, 41, 59, 0.14);
            font-size: 0.85rem;
            font-weight: 750;
            line-height: 1;
            text-decoration: none;
            pointer-events: auto;
        }

        .activity-home:hover {
            background: #eef2ff;
        }

        .audio-start[aria-pressed="true"] {
            border-color: #86efac;
            color: #166534;
            background: #f0fdf4;
        }

        .activity-home svg {
            width: 17px;
            height: 17px;
            flex: 0 0 auto;
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
            .activity-home,
            .audio-start,
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

HOME_NAV = """    <nav class="activity-top-nav" aria-label="Activity navigation">
        <a class="activity-home" href="index.html" aria-label="Return to Module E vocabulary home">
            <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11.5 12 4l9 7.5"></path><path d="M5.5 10.5V20h13v-9.5"></path><path d="M9.5 20v-6h5v6"></path></svg>
            <span>Home</span>
        </a>
        <button type="button" class="activity-home audio-start" id="audioStart" onclick="enableAutomaticAudio(event)" aria-pressed="false">Start audio</button>
    </nav>

"""


def require_replace(text: str, old: str, new: str, path: Path, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"Could not patch {label} in {path.name}")
    return text.replace(old, new, 1)


def patch_activity_page(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "activity-accessibility-v1" in text or "activity-accessibility-v2" in text:
        text = text.replace("Automatic pronunciation will start in three seconds.", "Automatic pronunciation will start in two seconds.", 1)
        text = text.replace("            }, 3000);\n        }\n\n        function enableAutomaticAudio", "            }, 2000);\n        }\n\n        function enableAutomaticAudio", 1)
        text = text.replace("justify-content: flex-start;\n            margin-bottom: 6px;", "justify-content: space-between;\n            gap: 10px;\n            margin-bottom: 6px;", 1)
        text = text.replace("        .activity-home {", "        .activity-home,\n        .audio-start {", 1)
        if '.audio-start[aria-pressed="true"]' not in text:
            text = text.replace(
                "        .activity-home:hover {\n            background: #eef2ff;\n        }",
                "        .activity-home:hover {\n            background: #eef2ff;\n        }\n\n"
                "        .audio-start[aria-pressed=\"true\"] {\n"
                "            border-color: #86efac;\n            color: #166534;\n            background: #f0fdf4;\n        }",
                1,
            )
        if 'id="audioStart"' not in text:
            text = text.replace(
                "        </a>\n    </nav>",
                "        </a>\n        <button type=\"button\" class=\"activity-home audio-start\" id=\"audioStart\" onclick=\"enableAutomaticAudio(event)\" aria-pressed=\"false\">Start audio</button>\n    </nav>",
                1,
            )
        if "let automaticAudioEnabled = false;" not in text:
            text = text.replace("        let hasUserInteracted = false;", "        let hasUserInteracted = false;\n        let automaticAudioEnabled = false;", 1)
        text = text.replace(
            "                if (scheduledIndex === currentIndex && !card.classList.contains('is-flipped')) {",
            "                if (automaticAudioEnabled && scheduledIndex === currentIndex && !card.classList.contains('is-flipped')) {",
            1,
        )
        if "function enableAutomaticAudio(event)" not in text:
            text = text.replace(
                "        function updateCard() {",
                "        function enableAutomaticAudio(event) {\n"
                "            if (event) event.stopPropagation();\n"
                "            automaticAudioEnabled = true;\n"
                "            hasUserInteracted = true;\n"
                "            if ('speechSynthesis' in window) window.speechSynthesis.resume();\n"
                "            const button = document.getElementById('audioStart');\n"
                "            button.setAttribute('aria-pressed', 'true');\n"
                "            button.textContent = 'Audio on';\n"
                "            button.disabled = true;\n"
                "            announceStatus('Audio enabled. Automatic pronunciation will start in two seconds.');\n"
                "            scheduleWordSpeech();\n"
                "        }\n\n"
                "        function updateCard() {",
                1,
            )
        if "function announceStatus(message)" not in text:
            text = text.replace(
                "        function announceCard(side) {",
                "        function announceStatus(message) {\n"
                "            const status = document.getElementById('cardStatus');\n"
                "            status.textContent = '';\n"
                "            window.clearTimeout(announceCard.timer);\n"
                "            announceCard.timer = window.setTimeout(() => { status.textContent = message; }, 80);\n"
                "        }\n\n"
                "        function announceCard(side) {",
                1,
            )
            text = text.replace(
                "            const status = document.getElementById('cardStatus');\n            const message = `${sideText}. Card ${currentIndex + 1} of ${words.length}. ${item.en}, ${item.pos}.`;\n            status.textContent = '';\n            window.clearTimeout(announceCard.timer);\n            announceCard.timer = window.setTimeout(() => {\n                status.textContent = message;\n            }, 80);",
                "            const message = `${sideText}. Card ${currentIndex + 1} of ${words.length}. ${item.en}, ${item.pos}.`;\n            announceStatus(message);",
                1,
            )
        text = text.replace(
            "            hasUserInteracted = true;\n            if (event) event.stopPropagation();\n            if (typeof words === 'undefined') return;",
            "            hasUserInteracted = true;\n            automaticAudioEnabled = true;\n            const audioStart = document.getElementById('audioStart');\n            audioStart.setAttribute('aria-pressed', 'true');\n            audioStart.textContent = 'Audio on';\n            audioStart.disabled = true;\n            if (event) event.stopPropagation();\n            if (typeof words === 'undefined') return;",
            1,
        )
        if "activity-top-nav" not in text:
            text = text.replace(
                "        .activity-main {",
                "        .activity-top-nav {\n"
                "            width: 100%;\n"
                "            max-width: 480px;\n"
                "            min-height: 44px;\n"
                "            position: sticky;\n"
                "            top: 8px;\n"
                "            z-index: 40;\n"
                "            display: flex;\n"
                "            justify-content: flex-start;\n"
                "            margin-bottom: 6px;\n"
                "            pointer-events: none;\n"
                "        }\n\n"
                "        .activity-home {\n"
                "            min-height: 44px;\n"
                "            display: inline-flex;\n"
                "            align-items: center;\n"
                "            justify-content: center;\n"
                "            gap: 7px;\n"
                "            padding: 8px 13px;\n"
                "            border: 1px solid #c7d2fe;\n"
                "            border-radius: 12px;\n"
                "            color: var(--primary-hover);\n"
                "            background: rgba(255, 255, 255, 0.96);\n"
                "            box-shadow: 0 3px 10px rgba(30, 41, 59, 0.14);\n"
                "            font-size: 0.85rem;\n"
                "            font-weight: 750;\n"
                "            line-height: 1;\n"
                "            text-decoration: none;\n"
                "            pointer-events: auto;\n"
                "        }\n\n"
                "        .activity-home:hover {\n"
                "            background: #eef2ff;\n"
                "        }\n\n"
                "        .activity-home svg {\n"
                "            width: 17px;\n"
                "            height: 17px;\n"
                "            flex: 0 0 auto;\n"
                "        }\n\n"
                "        .activity-main {",
                1,
            )
            text = text.replace(
                "    <header>",
                HOME_NAV + "    <header>",
                1,
            )
            text = text.replace(
                "            .card-face,\n            .tts-btn,",
                "            .card-face,\n            .activity-home,\n            .tts-btn,",
                1,
            )
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
        text = text.replace("activity-accessibility-v1", "activity-accessibility-v2", 1)
        if 'aria-label="Show answer for current word"' not in text:
            text = text.replace(
                'aria-controls="cardFront cardBack" aria-pressed="false">Show answer</button>',
                'aria-controls="cardFront cardBack" aria-pressed="false" '
                'aria-label="Show answer for current word">Show answer</button>',
                1,
            )
        if "flipButton.setAttribute('aria-label', 'Show answer for current word');" not in text:
            text = text.replace(
                "            flipButton.textContent = 'Show answer';",
                "            flipButton.textContent = 'Show answer';\n"
                "            flipButton.setAttribute('aria-label', 'Show answer for current word');",
                1,
            )
        if "function scheduleWordSpeech()" not in text:
            delayed_speech = r"""
        function scheduleWordSpeech() {
            window.clearTimeout(scheduleWordSpeech.timer);
            const scheduledIndex = currentIndex;
            scheduleWordSpeech.timer = window.setTimeout(() => {
                const card = document.getElementById('flashcard');
                if (scheduledIndex === currentIndex && !card.classList.contains('is-flipped')) {
                    speakText(words[currentIndex].en);
                }
            }, 2000);
        }
"""
            text, count = re.subn(
                r"(        function speakText\(text\) \{.*?^        \}\n)",
                r"\1" + delayed_speech,
                text,
                count=1,
                flags=re.S | re.M,
            )
            if count != 1:
                raise RuntimeError(f"Could not add delayed speech in {path.name}")
        if "            announceCard('word');\n            scheduleWordSpeech();" not in text:
            text = text.replace(
                "            announceCard('word');",
                "            announceCard('word');\n"
                "            scheduleWordSpeech();",
                1,
            )
        if "function playAudio(event) {\n            window.clearTimeout(scheduleWordSpeech.timer);" not in text:
            text = text.replace(
                "        function playAudio(event) {",
                "        function playAudio(event) {\n"
                "            window.clearTimeout(scheduleWordSpeech.timer);",
                1,
            )
        accessible_toggle = r"""        function announceCard(side) {
            const item = words[currentIndex];
            const sideText = side === 'answer' ? 'Answer shown' : 'Word shown';
            const status = document.getElementById('cardStatus');
            const message = `${sideText}. Card ${currentIndex + 1} of ${words.length}. ${item.en}, ${item.pos}.`;
            status.textContent = '';
            window.clearTimeout(announceCard.timer);
            announceCard.timer = window.setTimeout(() => {
                status.textContent = message;
            }, 80);
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
            flipButton.setAttribute(
                'aria-label',
                isFlipped ? 'Answer shown. Show word' : 'Word shown. Show answer'
            );
            announceCard(isFlipped ? 'answer' : 'word');
            if (isFlipped) {
                window.clearTimeout(scheduleWordSpeech.timer);
            } else {
                scheduleWordSpeech();
            }
        }

"""
        text, count = re.subn(
            r"        function announceCard\(side\) \{.*?(?=        function nextCard\(\))",
            accessible_toggle,
            text,
            count=1,
            flags=re.S,
        )
        if count != 1:
            raise RuntimeError(f"Could not upgrade card announcements in {path.name}")
        path.write_text(text, encoding="utf-8")
        return

    text = require_replace(text, "    </style>", ACCESSIBILITY_CSS + "    </style>", path, "CSS")
    text = require_replace(
        text,
        "<body>\n",
        '<body>\n    <a class="skip-link" href="#main-content">Skip to main content</a>\n' + HOME_NAV,
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
        '        <button type="button" class="nav-btn flip-btn" id="flipButton" onclick="toggleCard(event)" aria-controls="cardFront cardBack" aria-pressed="false" aria-label="Show answer for current word">Show answer</button>\n'
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
            flipButton.textContent = 'Show answer';
            flipButton.setAttribute('aria-label', 'Show answer for current word');"""
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

    text = text.replace(
        "            if (hasUserInteracted) {\n"
        "                speakText(item.en);\n"
        "            }\n",
        "            scheduleWordSpeech();\n",
        1,
    )

    delayed_speech = r"""
        function scheduleWordSpeech() {
            window.clearTimeout(scheduleWordSpeech.timer);
            const scheduledIndex = currentIndex;
            scheduleWordSpeech.timer = window.setTimeout(() => {
                const card = document.getElementById('flashcard');
                if (scheduledIndex === currentIndex && !card.classList.contains('is-flipped')) {
                    speakText(words[currentIndex].en);
                }
            }, 2000);
        }
"""
    text, count = re.subn(
        r"(        function speakText\(text\) \{.*?^        \}\n)",
        r"\1" + delayed_speech,
        text,
        count=1,
        flags=re.S | re.M,
    )
    if count != 1:
        raise RuntimeError(f"Could not add delayed speech in {path.name}")

    accessible_toggle = r"""        function announceCard(side) {
            const item = words[currentIndex];
            const sideText = side === 'answer' ? 'Answer shown' : 'Word shown';
            const status = document.getElementById('cardStatus');
            const message = `${sideText}. Card ${currentIndex + 1} of ${words.length}. ${item.en}, ${item.pos}.`;
            status.textContent = '';
            window.clearTimeout(announceCard.timer);
            announceCard.timer = window.setTimeout(() => {
                status.textContent = message;
            }, 80);
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
            flipButton.setAttribute(
                'aria-label',
                isFlipped ? 'Answer shown. Show word' : 'Word shown. Show answer'
            );
            announceCard(isFlipped ? 'answer' : 'word');
            if (isFlipped) {
                window.clearTimeout(scheduleWordSpeech.timer);
            } else {
                scheduleWordSpeech();
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

    text = text.replace(
        "        function playAudio(event) {",
        "        function playAudio(event) {\n"
        "            window.clearTimeout(scheduleWordSpeech.timer);",
        1,
    )

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
