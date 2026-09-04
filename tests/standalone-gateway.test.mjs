import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("standalone Band III gateway stays independent of the progress-report entry", async () => {
  const [index, tracker] = await Promise.all([
    readFile(new URL("../index.html", import.meta.url), "utf8"),
    readFile(new URL("../progress-tracker.js", import.meta.url), "utf8"),
  ]);

  assert.doesNotMatch(index, /דוח ההתקדמות שלי|efn-progress-home/);
  assert.doesNotMatch(tracker, /isBand3Home/);
  assert.match(tracker, /if \(isBand2Home && !document\.querySelector\('\.efn-progress-home'\)\)/);
  assert.match(tracker, /data-group-link/);
  assert.match(tracker, /const nav = document\.querySelector\('\.topbar,\.activity-top-nav,nav'\)/);
});
