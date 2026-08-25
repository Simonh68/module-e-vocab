import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';

const require = createRequire(import.meta.url);
require('../learning-loop.js');
const sessionApi = require('../practice-session.js');
const vocabApi = require('../vocab-practice.js');
const activityNames = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D1', 'D2', 'D3'];

function wordsFrom(html) {
  const match = html.match(/const words\s*=\s*(\[[^\n]*\]);/);
  assert.ok(match, 'embedded vocabulary array was not found');
  return JSON.parse(match[1]);
}

test('all twelve activities load the dormant rollout bundle without changing their vocabulary arrays', async () => {
  for (const name of activityNames) {
    const html = await readFile(new URL(`../${name}.html`, import.meta.url), 'utf8');
    assert.ok(wordsFrom(html).length > 12);
    assert.match(html, /window\.EFN_PAGE_WORDS=words/);
    assert.match(html, /learning-loop\.js/);
    assert.match(html, /practice-session\.js/);
    assert.match(html, /practice-panel\.js/);
    assert.match(html, /stage8-rollout\.js/);
    assert.match(html, /vocab-practice\.js/);
  }
});

test('wave one activates only A1 and uses its first twelve approved records', async () => {
  const context = { window: {} };
  vm.createContext(context);
  vm.runInContext(await readFile(new URL('../stage8-rollout.js', import.meta.url), 'utf8'), context);
  const rollout = context.window.EFN_STAGE8_ROLLOUT;
  assert.deepEqual(Object.keys(rollout.vocabulary), ['A1.html']);
  assert.equal(rollout.vocabulary['A1.html'].limit, 12);
  assert.equal(rollout.vocabulary['A1.html'].analyticsActivity, 'module-e-a1');
  assert.equal(vocabApi.rolloutFor('/module-e-vocab/A1.html', rollout.vocabulary).limit, 12);
  assert.equal(vocabApi.rolloutFor('/module-e-vocab/A2.html', rollout.vocabulary), null);
  const words = wordsFrom(await readFile(new URL('../A1.html', import.meta.url), 'utf8'));
  const session = sessionApi.createSession(words, { limit: 12, questionFactory: vocabApi.questionFactory });
  assert.equal(session.progress().total, 12);
  assert.equal(session.next().meta.record.en, words[0].en);
});

test('A1 questions provide immediate Hebrew-first and reverse-direction practice', async () => {
  const words = wordsFrom(await readFile(new URL('../A1.html', import.meta.url), 'utf8')).slice(0, 12);
  const primary = vocabApi.questionFactory(words[0], { records: words, mode: 'primary', phase: 'initial', filler: false, seed: 4 });
  const review = vocabApi.questionFactory(words[0], { records: words, mode: 'review', phase: 'review', filler: false, seed: 7 });
  assert.match(primary.prompt, /מה פירוש/);
  assert.equal(primary.answer, words[0].mean_he);
  assert.match(review.prompt, /איזו מילה/);
  assert.equal(review.answer, words[0].en);
  assert.ok(primary.choices.includes(primary.answer));
  assert.ok(review.choices.includes(review.answer));
  assert.deepEqual(primary.promptParts.map(part => part.lang), ['he', 'en', 'he']);
  assert.equal(primary.promptParts[1].text, words[0].en);
});

test('filler feedback does not promise an unscheduled return', () => {
  const record = {
    en: 'proof',
    mean_he: 'הוכחה',
    ex_en: 'The photo provided proof.',
    ex_he: 'התמונה סיפקה הוכחה.'
  };
  const feedback = vocabApi.formatFeedback({
    correct: false,
    entry: { filler: true },
    question: { meta: { record } }
  });
  assert.doesNotMatch(feedback.text, /נחזור/);
  assert.match(feedback.text, /חיזוק ביניים/);
  assert.ok(feedback.parts.some(part => part.lang === 'en'));
});

test('practice answers stay excluded while only start/completion measurements are exposed', async () => {
  const files = ['learning-loop.js', 'practice-session.js', 'practice-panel.js', 'vocab-practice.js'];
  const source = (await Promise.all(files.map(file => readFile(new URL(`../${file}`, import.meta.url), 'utf8')))).join('\n');
  const styles = await readFile(new URL('../practice-shell.css', import.meta.url), 'utf8');
  const analytics = await readFile(new URL('../analytics.js', import.meta.url), 'utf8');
  assert.doesNotMatch(source, /\bfetch\s*\(|\bsendBeacon\b|localStorage|sessionStorage|indexedDB|document\.cookie/);
  assert.match(source, /aria-live/);
  assert.match(source, /setTextParts/);
  assert.match(source, /activity_complete/);
  assert.match(source, /practice-start/);
  assert.match(source, /prefers-reduced-motion: reduce/);
  assert.match(styles, /\.efn-practice\{[^}]*box-sizing:border-box/);
  assert.match(styles, /overflow-wrap:anywhere/);
  assert.match(styles, /@media\(max-width:320px\)/);
  assert.match(styles, /@media\(prefers-reduced-motion:reduce\)/);
  assert.match(styles, /@media\(forced-colors:active\)/);
  assert.match(analytics, /data-analytics-ignore/);
  assert.match(analytics, /EFNAnalyticsIgnoreNextAudio/);
});

test('practice assets and the analytics privacy guard are cache-busted on rollout pages', async () => {
  const active = await readFile(new URL('../A1.html', import.meta.url), 'utf8');
  assert.match(active, /vocab-practice\.js\?v=20260825-stage9/);
  assert.match(active, /analytics\.js\?v=20260825-stage9/);
});
