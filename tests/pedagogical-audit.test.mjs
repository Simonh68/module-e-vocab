import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import test from 'node:test';
import vm from 'node:vm';
const require = createRequire(import.meta.url);
const source = await readFile(new URL('../learning-loop.js', import.meta.url), 'utf8');
const key = 'efn:band3:auto-audio:v1';

function audioHarness(initial = null, blocked = false) {
  const storage = new Map(initial ? [[key, initial]] : []);
  const attrs = {};
  const button = { disabled: false, setAttribute: (name, value) => { attrs[name] = value; } };
  const events = {};
  let cancelled = 0;
  let scheduled = 0;
  const context = {
    document: {
      getElementById: id => id === 'audioStart' ? button : { classList: { contains: () => false } },
      querySelector: () => null,
      addEventListener: (name, fn) => { events[name] = fn; }
    },
    localStorage: {
      getItem: k => { if (blocked) throw Error('blocked'); return storage.get(k) ?? null; },
      setItem: (k, value) => { if (blocked) throw Error('blocked'); storage.set(k, value); }
    },
    clearTimeout() {},
    addEventListener: (name, fn) => { events[name] = fn; },
    speechSynthesis: { cancel: () => { cancelled++; }, resume() {}, speaking: false, pending: false },
    scheduleWordSpeech: () => { scheduled++; },
    announceStatus() {}
  };
  context.window = context;
  vm.createContext(context);
  vm.runInContext(`let automaticAudioEnabled = false; let hasUserInteracted = false;
    function playAudio() { automaticAudioEnabled = true; document.getElementById('audioStart').disabled = true; }
    function enableAutomaticAudio() { automaticAudioEnabled = true; }`, context);
  vm.runInContext(source, context);
  return { context, storage, attrs, button, events, cancelled: () => cancelled, scheduled: () => scheduled,
    enabled: () => vm.runInContext('automaticAudioEnabled', context) };
}

test('automatic pronunciation is a persistent two-way toggle', () => {
  const h = audioHarness();
  h.context.enableAutomaticAudio();
  assert.equal(h.storage.get(key), 'on');
  assert.equal(h.enabled(), true);
  assert.equal(h.button.disabled, false);
  assert.equal(h.attrs['aria-label'], 'Turn off automatic audio');
  h.context.enableAutomaticAudio();
  assert.equal(h.storage.get(key), 'off');
  assert.equal(h.enabled(), false);
  assert.ok(h.cancelled() > 0);
  assert.equal(audioHarness(h.storage.get(key)).enabled(), false);
});

test('individual pronunciation does not silently change automatic-audio preferences', () => {
  for (const preference of [null, 'on', 'off']) {
    const h = audioHarness(preference);
    h.context.playAudio();
    assert.equal(h.storage.get(key) ?? null, preference);
    assert.equal(h.enabled(), preference === 'on');
    assert.equal(h.button.disabled, false);
  }
});

test('turning off persisted audio prevents late load and first-interaction resumption', () => {
  const h = audioHarness('on');
  h.context.enableAutomaticAudio();
  h.events.load();
  h.events.pointerdown();
  h.events.keydown();
  assert.equal(h.scheduled(), 0);
  assert.equal(h.enabled(), false);
});

test('blocked storage does not disable the current-page on/off control', () => {
  const h = audioHarness(null, true);
  h.context.enableAutomaticAudio();
  assert.equal(h.enabled(), true);
  h.context.enableAutomaticAudio();
  assert.equal(h.enabled(), false);
});

test('all A1 recall questions hide answer-bearing clues and speech until feedback', async () => {
  const api = require('../vocab-practice.js');
  const html = await readFile(new URL('../A1.html', import.meta.url), 'utf8');
  const words = JSON.parse(html.match(/const words\s*=\s*(\[[^\n]*\]);/)[1]).slice(0, 12);
  for (const record of words) {
    const review = api.questionFactory(record, { mode: 'review', records: words, phase: 'review', seed: 7 });
    assert.equal(review.clue, '');
    assert.equal(review.speakText, '');
    assert.equal(review.choices.filter(choice => choice === review.answer).length, 1);
    assert.doesNotMatch(review.modeLabel, /הקשר חדש/);
    const primary = api.questionFactory(record, { mode: 'primary', records: words, seed: 4 });
    assert.equal(primary.speakText, record.en.trim());
    const feedback = api.formatFeedback({ correct: false, entry: { filler: false }, question: review });
    assert.ok(feedback.parts.some(part => part.text === record.ex_en.trim()));
  }
});
