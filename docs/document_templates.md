# Engram document templates

Engram stores project-history documents as JSON objects. Pydantic validates the
objects before ingestion. The `document_type` field selects exactly one of the
three type-specific schemas.

## Common metadata

| Field | Type | Required | Purpose |
| --- | --- | --- | --- |
| `document_id` | string matching `^[A-Z][A-Z0-9-]*-\d{3,}$` | Yes | Stable reference used by relationships and citations. |
| `title` | string, 10-200 characters | Yes | Human-readable document title. |
| `document_type` | `adr`, `incident_report`, or `design_specification` | Yes | Discriminator for the document schema. |
| `document_date` | ISO date (`YYYY-MM-DD`) | Yes | Creation date for decisions/specifications or occurrence date for incidents. |
| `status` | type-specific enum | Yes | Lifecycle state. |
| `related_documents` | list of document IDs | No | Undirected contextual references. |
| `relationships` | list of typed ID edges | No | Meaningful directed links such as `implements` or `mitigates`. |

Every relationship target must exist in the corpus, and a document cannot
reference itself. IDs are unique within a corpus.

## Architecture Decision Record (ADR)

Required fields: common metadata, `context`, `decision`, `alternatives`,
`rationale`, and `consequences`. Optional fields: `supersedes`.

`status` is one of `proposed`, `accepted`, `superseded`, or `retired`.
`supersedes` is restricted to ADR IDs and records replacement decisions.

```json
{
  "document_id": "ADR-010",
  "title": "Use a read replica for reporting",
  "document_type": "adr",
  "document_date": "2024-09-05",
  "status": "accepted",
  "context": "Reporting queries compete with transactional workloads.",
  "decision": "Route eligible reporting queries to a PostgreSQL read replica.",
  "alternatives": ["Tune reports on the primary", "Use a warehouse"],
  "rationale": "A replica reduces primary database risk without a new warehouse.",
  "consequences": ["Reports can lag by five minutes"],
  "supersedes": ["ADR-003"]
}
```

## Incident Report

Required fields: common metadata, `severity`, `detected_at`, `impact`,
`root_cause`, `resolution`, and `preventive_actions`. Optional field:
`resolved_at`.

`status` is one of `investigating`, `mitigated`, `resolved`, or `closed`;
`severity` is one of `sev1`, `sev2`, `sev3`, or `sev4`. `resolved_at` cannot
precede `detected_at`.

## Design Specification

Required fields: common metadata, `problem_statement`, `architecture`,
`components`, and `technical_requirements`. Optional fields: `dependencies`,
`apis`, and `tradeoffs`.

`status` is one of `draft`, `approved`, or `deprecated`.

The complete field definitions and executable validation are in
[`src/engram/models.py`](../src/engram/models.py). The fictional,
interconnected examples are in [`data/sample_corpus.json`](../data/sample_corpus.json).
