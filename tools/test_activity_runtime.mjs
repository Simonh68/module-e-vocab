#!/usr/bin/env node

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const activities = [
  ...["A", "B", "C", "D"].flatMap((letter) =>
    [1, 2, 3].map((number) => `${letter}${number}.html`),
  ),
  "A1v2.html",
  "A2v2.html",
  "A3v2.html",
];

class ClassList {
  constructor() {
    this.values = new Set();
  }

  add(...names) {
    names.forEach((name) => this.values.add(name));
  }

  remove(...names) {
    names.forEach((name) => this.values.delete(name));
  }

  contains(name) {
    return this.values.has(name);
  }

  toggle(name) {
    if (this.values.has(name)) {
      this.values.delete(name);
      return false;
    }
    this.values.add(name);
    return true;
  }
}

class MockElement {
  constructor(id = "") {
    this.id = id;
    this.attributes = new Map();
    this.classList = new ClassList();
    this.children = [];
    this.listeners = new Map();
    this.style = {};
    this.textContent = "";
    this.innerText = "";
    this.value = "";
    this.disabled = false;
    this.inert = false;
  }

  setAttribute(name, value) {
    this.attributes.set(name, String(value));
  }

  getAttribute(name) {
    return this.attributes.get(name) ?? null;
  }

  append(...children) {
    this.children.push(...children);
  }

  appendChild(child) {
    this.children.push(child);
    return child;
  }

  replaceChildren(...children) {
    this.children = [...children];
  }

  addEventListener(type, listener) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(listener);
  }
}

function makeClock() {
  let now = 0;
  let nextId = 1;
  const timers = new Map();

  function setTimeout(callback, delay = 0) {
    const id = nextId++;
    timers.set(id, { at: now + Number(delay), callback });
    return id;
  }

  function clearTimeout(id) {
    timers.delete(id);
  }

  function advance(milliseconds) {
    const target = now + milliseconds;
    while (true) {
      const due = [...timers.entries()]
        .filter(([, timer]) => timer.at <= target)
        .sort((left, right) => left[1].at - right[1].at || left[0] - right[0])[0];
      if (!due) break;
      const [id, timer] = due;
      timers.delete(id);
      now = timer.at;
      timer.callback();
    }
    now = target;
  }

  return { advance, clearTimeout, get now() { return now; }, setTimeout };
}

function loadActivity(filename) {
  const html = fs.readFileSync(path.join(repo, filename), "utf8");
  const wordsMatch = html.match(/const words = (\[.*\]);\s*<\/script>/s);
  assert(wordsMatch, `${filename}: words array not found`);
  const words = JSON.parse(wordsMatch[1]);
  const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(
    (match) => match[1],
  );
  const runtime = scripts.at(-1);
  assert(runtime?.includes("function updateCard()"), `${filename}: runtime script not found`);

  const ids = [
    "backDetailsGrid",
    "audioStart",
    "cardBack",
    "cardFront",
    "cardStatus",
    "counter",
    "exEn",
    "exHe",
    "familyBox",
    "familyList",
    "flashcard",
    "flipButton",
    "jumpInput",
    "posBadge",
    "supportBox",
    "supportLabel",
    "supportText",
    "transHe",
    "ttsBtn",
    "wordEn",
    "wordGrammar",
  ];
  const elements = Object.fromEntries(ids.map((id) => [id, new MockElement(id)]));
  elements.cardBack.setAttribute("aria-hidden", "true");
  elements.cardBack.inert = true;
  elements.cardFront.setAttribute("aria-hidden", "false");
  elements.flipButton.setAttribute("aria-pressed", "false");

  const documentListeners = new Map();
  const document = {
    body: new MockElement("body"),
    createElement: () => new MockElement(),
    getElementById: (id) => elements[id] ?? (elements[id] = new MockElement(id)),
    addEventListener(type, listener) {
      if (!documentListeners.has(type)) documentListeners.set(type, []);
      documentListeners.get(type).push(listener);
    },
  };
  const clock = makeClock();
  const speech = [];
  let resumeCalls = 0;
  class SpeechSynthesisUtterance {
    constructor(text) {
      this.text = text;
      this.lang = "";
      this.rate = 1;
    }
  }
  const window = {
    clearTimeout: clock.clearTimeout,
    onload: null,
    setTimeout: clock.setTimeout,
    speechSynthesis: {
      cancel() {},
      resume() { resumeCalls += 1; },
      speak(utterance) {
        speech.push({ at: clock.now, text: utterance.text });
      },
    },
  };
  const sandbox = {
    alert() {},
    console,
    document,
    SpeechSynthesisUtterance,
    window,
    words,
  };
  vm.createContext(sandbox);
  vm.runInContext(runtime, sandbox, { filename });
  assert.equal(typeof window.onload, "function", `${filename}: onload is not registered`);

  return { clock, documentListeners, elements, html, resumeCalls: () => resumeCalls, sandbox, speech, words, window };
}

function event(key = "") {
  return {
    altKey: false,
    ctrlKey: false,
    defaultPrevented: false,
    key,
    metaKey: false,
    preventDefault() {
      this.defaultPrevented = true;
    },
    stopPropagation() {},
  };
}

function testActivity(filename) {
  const state = loadActivity(filename);
  const { clock, documentListeners, elements, html, resumeCalls, sandbox, speech, words, window } = state;

  window.onload();
  assert.equal(elements.counter.innerText, `1 / ${words.length}`, `${filename}: first counter`);
  assert.equal(speech.length, 0, `${filename}: first word spoke immediately`);
  clock.advance(3000);
  assert.equal(speech.length, 0, `${filename}: first word spoke before audio was enabled`);
  sandbox.enableAutomaticAudio(event());
  assert.equal(resumeCalls(), 1, `${filename}: audio engine was not resumed from the user action`);
  assert.equal(elements.audioStart.getAttribute("aria-pressed"), "true", `${filename}: audio state`);
  assert.equal(elements.audioStart.disabled, true, `${filename}: Start audio remained enabled`);
  clock.advance(80);
  assert.match(elements.cardStatus.textContent, /^Audio enabled\./, `${filename}: audio status`);
  clock.advance(2919);
  assert.equal(speech.length, 0, `${filename}: first word spoke before 3 seconds after enabling audio`);
  clock.advance(1);
  assert.deepEqual(speech.at(-1), { at: 6000, text: words[0].en }, `${filename}: first word`);

  sandbox.nextCard();
  assert.equal(elements.counter.innerText, `2 / ${words.length}`, `${filename}: Next counter`);
  const beforeNextSpeech = speech.length;
  clock.advance(2999);
  assert.equal(speech.length, beforeNextSpeech, `${filename}: next word spoke before 3 seconds`);
  clock.advance(1);
  assert.equal(speech.at(-1).text, words[1].en, `${filename}: next word pronunciation`);

  sandbox.nextCard();
  clock.advance(1000);
  sandbox.nextCard();
  const quickTarget = words[3].en;
  const beforeQuickSpeech = speech.length;
  clock.advance(2000);
  assert.equal(speech.length, beforeQuickSpeech, `${filename}: stale timer was not cancelled`);
  clock.advance(1000);
  assert.equal(speech.length, beforeQuickSpeech + 1, `${filename}: latest timer did not speak once`);
  assert.equal(speech.at(-1).text, quickTarget, `${filename}: stale word was spoken`);

  sandbox.nextCard();
  clock.advance(500);
  const beforeFlipSpeech = speech.length;
  sandbox.toggleCard(event());
  clock.advance(80);
  assert.match(elements.cardStatus.textContent, /^Answer shown\./, `${filename}: answer status`);
  assert.equal(elements.flipButton.getAttribute("aria-pressed"), "true", `${filename}: pressed state`);
  assert.equal(elements.flipButton.getAttribute("aria-label"), "Answer shown. Show word", `${filename}: answer label`);
  assert.equal(elements.cardFront.inert, true, `${filename}: front remains exposed`);
  assert.equal(elements.cardBack.inert, false, `${filename}: back remains inert`);
  assert.equal(elements.ttsBtn.disabled, true, `${filename}: hidden pronunciation remains enabled`);
  clock.advance(5000);
  assert.equal(speech.length, beforeFlipSpeech, `${filename}: pending word spoke on answer side`);

  sandbox.toggleCard(event());
  clock.advance(3000);
  assert.equal(speech.at(-1).text, words[4].en, `${filename}: word did not speak after returning`);
  assert.equal(elements.flipButton.getAttribute("aria-pressed"), "false", `${filename}: word pressed state`);

  sandbox.nextCard();
  const beforeManualSpeech = speech.length;
  sandbox.playAudio(event());
  assert.equal(speech.length, beforeManualSpeech + 1, `${filename}: Listen button did not speak`);
  clock.advance(3000);
  assert.equal(speech.length, beforeManualSpeech + 1, `${filename}: manual speech was duplicated`);

  const keydown = documentListeners.get("keydown")?.[0];
  assert(keydown, `${filename}: keyboard handler missing`);
  const beforeArrow = elements.counter.innerText;
  const arrowEvent = event("ArrowRight");
  keydown(arrowEvent);
  assert.equal(arrowEvent.defaultPrevented, true, `${filename}: ArrowRight default not prevented`);
  assert.notEqual(elements.counter.innerText, beforeArrow, `${filename}: ArrowRight did not navigate`);
  const beforeEnter = elements.counter.innerText;
  keydown(event("Enter"));
  assert.equal(elements.counter.innerText, beforeEnter, `${filename}: global Enter changed cards`);
  keydown(event(" "));
  assert.equal(elements.counter.innerText, beforeEnter, `${filename}: global Space changed cards`);

  assert.match(html, /class="activity-home" href="index\.html"[^>]+aria-label="Return to Module E vocabulary home"/, `${filename}: Home semantics`);
  assert.match(html, /id="cardStatus" role="status" aria-live="polite" aria-atomic="true"/, `${filename}: live region`);
  assert.match(html, /id="audioStart"[^>]+aria-pressed="false"[^>]*>Start audio<\/button>/, `${filename}: Start audio control`);
  assert.match(html, /button:focus-visible,[\s\S]*a:focus-visible/, `${filename}: focus style`);
  assert.match(html, /@media \(prefers-reduced-motion: reduce\)/, `${filename}: reduced motion`);
  assert.match(html, /<html\b[^>]*\blang="en"[^>]*>/, `${filename}: page language`);
}

for (const filename of activities) testActivity(filename);

console.log(
  `PASS: ${activities.length} activities simulated: explicit audio enablement, first-card and Next pronunciation at 3000 ms after enablement, stale-timer cancellation, flip cancellation, live announcements, Listen, keyboard, Home, focus, reduced motion and language.`,
);
