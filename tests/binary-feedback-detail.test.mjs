import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const pages = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D1', 'D2', 'D3'];

function fakeElement(tagName) {
  const listeners = new Map();
  return {
    tagName,
    children: [],
    dataset: {},
    classList: { add() {}, remove() {} },
    setAttribute() {},
    querySelector() { return null; },
    addEventListener(name, listener) { listeners.set(name, listener); },
    append(...children) { this.children.push(...children); },
    appendChild(child) { this.children.push(child); },
    get offsetWidth() { return 44; },
    listeners,
  };
}

test('Band III feedback identifies the exact group, card and word', async () => {
  const [runtime, vocabulary] = await Promise.all([
    readFile(path.join(root, 'learning-loop.js'), 'utf8'),
    readFile(path.join(root, 'data/vocabulary-master.json'), 'utf8').then(JSON.parse),
  ]);

  assert.match(runtime, /event: 'button_click'/);
  assert.match(runtime, /context: \{ target, outcome \}/);
  assert.match(runtime, /const item = words\[currentIndex\]/);
  assert.match(runtime, /const cardId = .*group.*String\(currentIndex \+ 1\)\.padStart\(3, '0'\)/);
  assert.match(runtime, /vf1\|.*group.*cardId.*definition-example.*encodeURIComponent/);
  assert.match(runtime, /wrap\.dataset\.analyticsIgnore = 'true'/);
  assert.match(runtime, /ack\.textContent = '💬'/);
  assert.doesNotMatch(runtime, /✓ תודה/);
  assert.doesNotMatch(runtime, /band3-\$\{activity\}-definition-example-feedback/);

  const targets = vocabulary.map((word) => ['vf1', word.group, word.source_entry_id, 'definition-example', encodeURIComponent(String(word.en || ''))].join('|'));
  assert.equal(new Set(targets).size, vocabulary.length);
  assert.ok(targets.every((target) => target.length <= 120));

  for (const page of pages) {
    const html = await readFile(path.join(root, `${page}.html`), 'utf8');
    assert.match(html, /learning-loop\.js\?v=20260904-feedback-card1/, page);
  }
});

test('Band III precise feedback adds no personal or answer fields', async () => {
  const runtime = await readFile(path.join(root, 'learning-loop.js'), 'utf8');
  const feedbackSource = runtime.slice(runtime.indexOf('[data-efn-binary-feedback]'));

  assert.doesNotMatch(feedbackSource, /visitId|visitorId|email|studentId|fingerprint|referrer|freeText|answerText|recording/i);
});

test('Band III feedback click emits one precise payload for the visible card', async () => {
  const runtime = await readFile(path.join(root, 'learning-loop.js'), 'utf8');
  const feedbackSource = runtime.slice(runtime.lastIndexOf("(() => {\n  if (typeof window"));
  const back = fakeElement('section');
  const requests = [];
  const context = vm.createContext({
    words: [{ en: 'example' }, { en: 'take the opportunity' }],
    currentIndex: 1,
    document: {
      head: fakeElement('head'),
      querySelector: (selector) => selector === '.card-back' ? back : null,
      createElement: fakeElement,
    },
    location: { pathname: '/module-e-vocab/B2.html' },
    fetch: (url, options) => {
      requests.push({ url, options });
      return Promise.resolve(new Response(null, { status: 204 }));
    },
    setTimeout: (callback) => { callback(); return 1; },
  });
  context.window = context;

  vm.runInContext(feedbackSource, context);
  const wrap = back.children[0];
  const negative = wrap.children[1];
  negative.listeners.get('click')({ stopPropagation() {} });

  assert.equal(requests.length, 1);
  assert.equal(requests[0].url, 'https://englishfornoar.co.il/api/analytics');
  assert.deepEqual(JSON.parse(requests[0].options.body), {
    site: 'module-e',
    path: '/module-e-vocab/B2.html',
    pageKind: 'group',
    event: 'button_click',
    context: {
      target: 'vf1|B2|B2-002|definition-example|take%20the%20opportunity',
      outcome: 'negative',
    },
  });
  assert.equal(wrap.dataset.analyticsIgnore, 'true');
});
