import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const pages = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D1', 'D2', 'D3'];
let referenceHelper = null;

for (const page of pages) {
  const source = fs.readFileSync(path.join(root, `${page}.html`), 'utf8');
  const helperStart = source.indexOf('function resetCardForNavigation(card)');
  const updateStart = source.indexOf('function updateCard()', helperStart);
  const helper = source.slice(helperStart, updateStart).trim();
  const resetCall = source.indexOf('resetCardForNavigation(card);', updateStart);
  const itemRead = source.indexOf('const item = words[currentIndex];', updateStart);
  const answerWrite = source.indexOf("document.getElementById('transHe').innerText", updateStart);

  assert.ok(helperStart >= 0, `${page} is missing the navigation reset helper`);
  assert.ok(updateStart > helperStart, `${page} has the helper in the wrong place`);
  assert.ok(resetCall > updateStart, `${page} does not reset the card before updating it`);
  assert.ok(resetCall < itemRead, `${page} reads the next item before resetting the visible card`);
  assert.ok(itemRead < answerWrite, `${page} has an unexpected answer-rendering order`);
  assert.match(helper, /card\.style\.transition = 'none';/);
  assert.match(helper, /card\.classList\.remove\('is-flipped'\);/);
  assert.match(helper, /void card\.offsetWidth;/);
  assert.match(helper, /card\.style\.transition = previousTransition;/);

  if (referenceHelper === null) referenceHelper = helper;
  else assert.equal(helper, referenceHelper, `${page} does not use the shared navigation sequence`);
}

const resetCardForNavigation = Function(`${referenceHelper}; return resetCardForNavigation;`)();
const operations = [];
const classes = new Set(['is-flipped']);
const transitionState = { value: 'transform 0.6s ease' };
const card = {
  classList: {
    contains(name) {
      operations.push(`contains:${name}`);
      return classes.has(name);
    },
    remove(name) {
      operations.push(`remove:${name}`);
      classes.delete(name);
    }
  },
  style: new Proxy({}, {
    get(_target, property) {
      if (property === 'transition') {
        operations.push('get:transition');
        return transitionState.value;
      }
      return undefined;
    },
    set(_target, property, value) {
      if (property === 'transition') {
        operations.push(`set:transition:${value}`);
        transitionState.value = value;
        return true;
      }
      return false;
    }
  }),
  get offsetWidth() {
    operations.push('flush-layout');
    return 480;
  }
};

resetCardForNavigation(card);
assert.deepEqual(operations, [
  'contains:is-flipped',
  'get:transition',
  'set:transition:none',
  'remove:is-flipped',
  'flush-layout',
  'set:transition:transform 0.6s ease'
]);
assert.equal(classes.has('is-flipped'), false);
assert.equal(transitionState.value, 'transform 0.6s ease');

console.log(`Flashcard navigation regression: ${pages.length}/${pages.length} pages passed.`);
