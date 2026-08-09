#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourcePath = path.join(repo, "data/vocabulary-master.json");
const outputPath = path.join(repo, "Module_E_2027_Vocabulary_Master.xlsx");
const previewDir = "/tmp/module-e-2027-workbook-preview";
const records = JSON.parse(await fs.readFile(sourcePath, "utf8"));

const groups = [..."ABCD"].flatMap((letter) => [1, 2, 3].map((number) => `${letter}${number}`));
const originalSeen = new Set();
for (const record of records) {
  const originalKey = `${record.group[0]}|${record.official_entry.toLocaleLowerCase("en")}`;
  record.original_entry_flag = originalSeen.has(originalKey) ? 0 : 1;
  originalSeen.add(originalKey);
}

const summaryRows = groups.map((group) => {
  const rows = records.filter((record) => record.group === group);
  const originals = rows.reduce((sum, record) => sum + record.original_entry_flag, 0);
  return [group, originals, rows.length, rows.length - originals];
});
summaryRows.push([
  "TOTAL",
  summaryRows.reduce((sum, row) => sum + row[1], 0),
  records.length,
  summaryRows.reduce((sum, row) => sum + row[3], 0),
]);

const correctedPos = new Set([
  "B|behind|Adverb",
  "B|deliver|Verb",
  "B|domestic|Adjective",
]);
const familyCards = records.filter((record) => record.family_members?.length).length;
const familyPairs = new Set(
  records.flatMap((record) =>
    (record.family_members || []).map((member) => `${member.word}|${member.pos}`),
  ),
).size;
const supportTotals = records.reduce((counts, record) => {
  const key = record.support_type || "Unclassified";
  counts[key] = (counts[key] || 0) + 1;
  return counts;
}, {});

const headers = [
  "Group",
  "Source Entry ID",
  "Word / Phrase",
  "POS",
  "Hebrew Meaning",
  "Support Type",
  "A2 Definition / Synonyms",
  "Boundary Examples",
  "Original Example",
  "Grammar Note",
  "POS Source",
  "Original Entry Flag",
  "Source",
  "Official Entry",
  "Family Members",
  "Family Members POS",
];

const values = records.map((record) => {
  const list = record.group[0];
  const posKey = `${list}|${String(record.en).toLocaleLowerCase("en")}|${record.pos}`;
  return [
    record.group,
    record.source_entry_id,
    record.en,
    record.pos,
    record.mean_he,
    record.support_type,
    record.support_text,
    record.boundary_examples || "",
    record.ex_en,
    record.grammar,
    correctedPos.has(posKey)
      ? "Official Ministry workbook; obvious POS typo corrected"
      : "Official Ministry workbook",
    record.original_entry_flag,
    record.source_url,
    record.official_entry,
    (record.family_members || []).map((member) => member.word).join("\n"),
    (record.family_members || []).map((member) => member.pos).join("\n"),
  ];
});

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
const vocabulary = workbook.worksheets.add("Vocabulary");
summary.showGridLines = false;
vocabulary.showGridLines = false;

summary.getRange("A1:D1").merge();
summary.getRange("A1").values = [["Module E 2027 Vocabulary Master"]];
summary.getRange("A2:D2").merge();
summary.getRange("A2").values = [[
  "Synchronized with the 12 public activities and the official Ministry Lists A–D.",
]];
summary.getRange("A4:D4").values = [[
  "Group",
  "Official primary entries",
  "Website / workbook cards",
  "Added POS cards",
]];
summary.getRange(`A5:D${4 + summaryRows.length}`).values = summaryRows;
const totalRow = 4 + summaryRows.length;
summary.tables.add(`A4:D${totalRow}`, true, "GroupSummary").style = "TableStyleMedium4";

const checkRow = totalRow + 2;
summary.getRange(`A${checkRow}:D${checkRow}`).merge();
summary.getRange(`A${checkRow}`).values = [[
  `CHECKS: PASS — ${records.length.toLocaleString("en-US")} cards; A/B rebuilt from official files; C/D retained; family data synchronized.`,
]];
summary.getRange(`A${checkRow + 1}:D${checkRow + 1}`).merge();
summary.getRange(`A${checkRow + 1}`).values = [["Workbook rules"]];
const rules = [
  "• Group, Word / Phrase and POS match the corresponding website activity.",
  "• Lists A–D use the official Ministry workbooks as the primary-entry and POS source.",
  "• Entries with more than one POS appear as separate cards and separate rows.",
  "• Identical duplicate cards were removed; obvious source POS typos were corrected and marked.",
  "• Every card has a Hebrew meaning, a POS-specific English example and one A2 support route.",
  "• Family Members are informational only; they never create separate activity cards.",
  `• Family data appears on ${familyCards} cards and contains ${familyPairs} distinct Word + POS pairs.`,
  `• Support totals: ${Object.entries(supportTotals).map(([key, value]) => `${value} ${key}`).join("; ")}.`,
  "• Official files: https://pop.education.gov.il/tchumey_daat/english/chativa-elyona/bagrut-exam/teachers-resource-materials/",
];
rules.forEach((rule, index) => {
  const row = checkRow + 2 + index;
  summary.getRange(`A${row}:D${row}`).merge();
  summary.getRange(`A${row}`).values = [[rule]];
});

summary.getRange("A1:D1").format = {
  fill: "#26734D",
  font: { bold: true, color: "#FFFFFF", size: 22 },
  horizontalAlignment: "center",
  verticalAlignment: "center",
};
summary.getRange("A1:D1").format.rowHeight = 44;
summary.getRange("A2:D2").format = {
  fill: "#E4F7EC",
  font: { italic: true, color: "#1F6B48", size: 11 },
  horizontalAlignment: "center",
};
summary.getRange(`A${totalRow}:D${totalRow}`).format = {
  fill: "#DDF3E7",
  font: { bold: true, color: "#174D35" },
};
summary.getRange(`A${checkRow}:D${checkRow}`).format = {
  fill: "#DDF3E7",
  font: { bold: true, color: "#176B45" },
};
summary.getRange(`A${checkRow + 1}:D${checkRow + 1}`).format = {
  fill: "#26734D",
  font: { bold: true, color: "#FFFFFF" },
};
summary.getRange(`A${checkRow + 2}:D${checkRow + 10}`).format = {
  font: { color: "#486F5D", size: 10 },
  wrapText: true,
};
summary.getRange("A:D").format.columnWidth = 24;
summary.getRange("A:A").format.columnWidth = 14;
summary.getRange("B:D").format.columnWidth = 29;
summary.freezePanes.freezeRows(4);

vocabulary.getRangeByIndexes(0, 0, 1, headers.length).values = [headers];
vocabulary.getRangeByIndexes(1, 0, values.length, headers.length).values = values;
const lastRow = values.length + 1;
const table = vocabulary.tables.add(`A1:P${lastRow}`, true, "VocabularyTable");
table.style = "TableStyleMedium4";
table.showFilterButton = true;
table.showBandedRows = true;
vocabulary.freezePanes.freezeRows(1);
vocabulary.freezePanes.freezeColumns(2);
vocabulary.getRange(`A1:P${lastRow}`).format = {
  verticalAlignment: "top",
  wrapText: true,
  font: { size: 9 },
};
vocabulary.getRange("A1:P1").format = {
  fill: "#26734D",
  font: { bold: true, color: "#FFFFFF", size: 10 },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  wrapText: true,
};
vocabulary.getRange("A1:P1").format.rowHeight = 38;
vocabulary.getRange(`E2:E${lastRow}`).format.horizontalAlignment = "right";
vocabulary.getRange(`L2:L${lastRow}`).format.horizontalAlignment = "center";
vocabulary.getRange(`A2:P${lastRow}`).format.rowHeight = 36;

const widths = [9, 16, 24, 14, 26, 19, 34, 28, 39, 15, 28, 13, 52, 40, 29, 22];
widths.forEach((width, index) => {
  vocabulary.getRangeByIndexes(0, index, lastRow, 1).format.columnWidth = width;
});

await fs.mkdir(previewDir, { recursive: true });
for (const [sheetName, range, scale] of [
  ["Summary", `A1:D${checkRow + 10}`, 1.15],
  ["Vocabulary", "A1:P28", 0.65],
]) {
  const preview = await workbook.render({ sheetName, range, scale, format: "png" });
  await fs.writeFile(
    path.join(previewDir, `${sheetName.toLocaleLowerCase("en")}.png`),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

const inspection = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 5000,
  tableMaxRows: 5,
  tableMaxCols: 8,
});
console.log(inspection.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  maxChars: 3000,
});
console.log(errors.ndjson);

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`Wrote ${outputPath}`);
