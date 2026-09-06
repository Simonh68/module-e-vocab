import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const source = fs.readFileSync(new URL('../analytics.js', import.meta.url), 'utf8');

test('only Band III activity pages migrate; the standalone gateway stays in place', () => {
  assert.match(source, /\[A-D\]\[1-3\]\\\.html/);
  assert.match(source, /\/module-e-vocab\/play\//);
  assert.match(source, /efn\.vocab\.progress\.v1/);
  assert.doesNotMatch(source, /location\.pathname === '\/module-e-vocab\/'/);
});
