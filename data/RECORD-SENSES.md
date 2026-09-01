# Record-level sense metadata

Module E may contain the same displayed English entry in more than one Ministry-derived record. Each occurrence is independent and keeps its own meaning, example, source entry ID, group, order and supplied POS classification.

## Canonical fields

Every record in `vocabulary-master.json`, the generated master workbook and the 12 activity payloads carries:

| Field | Meaning |
|---|---|
| `record_sense_en` | The record-specific English support definition or synonym set. |
| `record_sense_he` | The natural Hebrew gloss for that record. |
| `repeated_entry` | Whether the same normalized displayed spelling appears in another record. |
| `same_entry_record_ids` | All other source entry IDs with the same displayed spelling. |
| `record_sense_scope` | `record-specific` for repeated spelling and `single-entry` otherwise. |

The A/B curation table `ab_content.tsv` carries the same metadata in explicit columns, including `Source Entry ID`. Repeated spelling is never merged or resolved from spelling or POS alone. A meaning difference is visible inside the linked records through their record-specific English and Hebrew sense fields.

`hebrew-glosses.json` remains an auxiliary exact-key lookup (`List|Display|POS`) for A/B Hebrew glosses. It is not the canonical record-identity store; record identity and repeated-entry links live in `vocabulary-master.json` and `ab_content.tsv`.

## Live example

`decrease` is retained in two independent records:

| Source entry ID | Record sense (English) | Record sense (Hebrew) | Same-entry record IDs |
|---|---|---|---|
| A1-068 | become or make smaller | להפחית; לצמצם; לרדת; להצטמצם | A2-069 |
| A2-069 | a reduction in size, number or amount | הפחתה; צמצום | A1-068 |

The record-specific fields make the two uses explicit without changing the displayed word or its supplied classification.
