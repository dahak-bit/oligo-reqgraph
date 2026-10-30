# Oligonucleotide Regulatory Requirements Graph (oligo reqgraph)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23818609.svg)](https://doi.org/10.5281/zenodo.23818609)

An open, machine-readable map of which laws, guidelines, pharmacopoeial texts and
regulatory programmes apply to oligonucleotide therapeutics (ASO, siRNA, aptamers,
GalNAc/antibody/LNP-delivered oligos) along the development path from discovery to
post-approval. Coverage: ICH, EU, US, Japan, UK, plus field-level consensus (OSWG).

Release 0.4.2 (data model 0.3) · 104 nodes · 94 semantic relations + 292 derived gate links · generated 2026-10-30

**Changes in 0.4.1–0.4.2:** Zenodo DOI added to CITATION.cff, README, `graph.json` (`meta.doi`) and the page (byline and citation line); LICENSE names the copyright holder and covers all code and data files.

**Changes in 0.4.0 (Phase C, page only — data unchanged):** the explorer and the map are one
page, `index.html`, with four views (Map, Explore, Register, Notes) behind one filter panel; the
active view is in the URL hash (`#map`, `#explore`, `#register`, `#notes`). Built-in filter presets
per programme type, user-saved presets (browser local storage), sortable register with CSV export
of the filtered rows, theme-resolved SVG export, an A4 print stylesheet (Figure 1 split at lane
boundaries onto landscape pages; Panel 1 and Table 1 portrait), keyboard access to bars and keys,
and a colour-vision check of the palette with non-colour status cues (every status has a distinct
outline pattern or shape). `figure.html` and the old explorer are retired.

**Changes in 0.3.0 (data model 0.3):** every node now carries `domain`, `gate_from`/`gate_to`
on an eight-gate scale, a unique citation `key`, an optional `group` (series aggregation for
the figure), `triggers` (programme types that engage the document) and `last_checked`. The
`phase` field and stored `governs_phase` edges are gone; gate links are regenerated at build
time under `derived.applies_at` and are never edited by hand. `supersedes` edges record revision
history. Content: intrathecal/CNS references, FDA DILI and renal-impairment PK guidances, US
statutes re-verified on primary govinfo texts, zero documents left unchecked; EDQM/Pharmeuropa
negative result dated. Tooling: `validate.py` and a CI workflow.

**Changes in 0.2.0:** reconciled against a source inventory of 107 checked documents.
Corrected status, dates and document numbers (e.g. FDA oligo clinical-pharmacology
guidance is final since June 2024; the three individualised-ASO guidances are still
drafts; the Rare Pediatric Disease voucher was reauthorised in February 2026). Added
19 documents, including FDA's draft nonclinical guidance for oligonucleotides (Nov 2024),
the FDA Plausible Mechanism framework (Feb 2026), the EMA draft oligonucleotide quality
guideline, both Japanese oligo guidelines, and conjugate/LNP-relevant guidance.
Added `status_note` and `verification` fields.

> **Not regulatory advice.** Guidance documents change status, get revised or
> withdrawn. Every node carries a `confidence` field; treat anything below `high`
> as a pointer to check, and verify every document with the issuing body before
> relying on it.

## Files

| File | Content |
|---|---|
| `graph.json` | Complete graph: `meta` (gates, domains, groups, triggers), `nodes`, `edges`, `derived` |
| `nodes.json` / `edges.json` | Same data, split |
| `nodes.csv` / `edges.csv` | Flat tables for spreadsheets, R, pandas |
| `schema.json` | JSON Schema (draft-07) for `graph.json` |
| `index.html` | The page: Map (Figure 1, Panel 1), Explore (d3 force graph), Register (Table 1), About (scope, how to read the fields, how to use the page). Self-contained, data embedded; d3 is loaded from cdnjs for the Explore view only. |
| `figure1.svg` | Standalone Figure 1 (light theme, links kept) for manuscripts |
| `build.py` | Builds `graph.json`, `nodes.*`, `edges.*` from the source definitions |
| `build_page.py` | Generates `index.html` and `figure1.svg` from `graph.json` |
| `validate.py` | Schema, integrity, key/span/group checks; `--links` writes `link-report.json` |
| `.github/workflows/validate.yml` | Runs validation on every change and the link check quarterly |
| `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/` | How to propose corrections and additions |
| `source-inventory.json` | The 107-document source check behind v0.2: document numbers, dates, status, official URLs and how each was verified. Broader than the graph; use it to add nodes. |

## Data model

**Node kinds**

| kind | meaning |
|---|---|
| `milestone` | Development gate (discovery → nonclinical → CTA/IND → phases → filing → lifecycle) |
| `legal_act` | Binding law or regulation (e.g. Reg (EC) 1901/2006, 21 CFR 312) |
| `guideline` | ICH / agency guidance, incl. oligo-specific guidance |
| `pharmacopoeia` | Ph. Eur. / USP texts |
| `programme` | Designations and pathways (PRIME, Breakthrough, orphan, stepwise PIP) |
| `consideration` | Oligo-specific scientific/regulatory topic (off-target, immunostimulation, impurities, delivery) |

**Node placement (0.3)**

| field | meaning |
|---|---|
| `domain` | `quality`, `nonclin`, `clinical`, `paed`, `rare`, `auth`; `spine` for gates, `consideration` for topics |
| `gate_from`, `gate_to` | first and last development gate at which the document applies (0 Discovery … 7 Post-approval; see `meta.gates`) |
| `key` | short unique citation key used in figures and the register |
| `group` | series id (`meta.groups`) drawn as one bar in the figure |
| `triggers` | programme types that additionally engage the document: `paed_onc`, `aoc`, `lnp`, `galnac`, `intrathecal`, `individualised` |
| `last_checked` | date of the last source check (ISO) |

**Edge relations**

| rel | direction | meaning |
|---|---|---|
| `prerequisite_for` | milestone → milestone | development spine |
| `supersedes` | document → document | newer text replaces an older one |
| `applies_at` (derived) | document → gate | regenerated from `gate_from`/`gate_to`; in `derived`, not `edges` |
| `informs` | consideration → milestone | topic shapes the work at this gate |
| `addresses` | document → consideration | document covers this topic |
| `supports` | programme → milestone | incentive or pathway available here |
| `references` | document → document | cross-reference |
| `amends` | act → act | legislative change |

**Status** — `in_force`, `draft`, `pending` (adopted but not yet in force), `programme`,
`guidance` (non-binding consensus), `verify` (status not confirmed). `status_note`
carries the full text, e.g. consultation periods or what a document supersedes.

**Verification provenance** (`verification`, document nodes only)

- `page` — the official page or PDF was opened during the check.
- `secondary` — a non-official source (law-firm summary, library record) was opened because the primary text could not be reached.
- `search` — the URL surfaced on the official domain; the page itself was not opened.
- `knowledge` — not checked against a live source. Treat as a lead.

**Confidence**

- `high` — identity, reference and status are well established; URL points to the official landing page.
- `medium` — document exists; exact current version, number or URL should be checked.
- `low` / `status: verify` — reported or expected document whose current status could not be confirmed. Do not cite without checking.

## Using the data

```python
import json, networkx as nx
g = json.load(open("graph.json"))
G = nx.DiGraph()
G.add_nodes_from((n["id"], n) for n in g["nodes"])
G.add_edges_from((e["source"], e["target"], {"rel": e["rel"]}) for e in g["edges"])
# everything that applies at the IND/CTA-enabling nonclinical gate (gate index 1)
[n["key"] for n in g["nodes"] if n["domain"] not in ("spine","consideration") and n["gate_from"] <= 1 <= n["gate_to"]]
```

## Using the page

- **Filters** apply to all views. *Dim* keeps non-matching documents at low opacity; *Hide* removes them, turns a programme-type selection into a filter, and closes up empty rows and lanes.
- **Presets**: one built-in preset per programme type (jurisdictions, gate range, programme type, Hide). *Save as preset* stores the current filters for the selected programme type in this browser only; *Built-in presets* forgets saved ones.
- **Export**: *Copy SVG* (current theme and filter state), *Copy CSV* (register rows currently shown, all data fields), *Copy JSON* (the whole graph). *Print* renders Figure 1, Panel 1 and the filtered Table 1 on A4.
- **Keyboard**: Tab moves between bars in Figure 1, ←/→ between keys of a series bar, Enter opens the detail sheet, Esc closes it; ←/→ also move between the view tabs.
- **Links**: `index.html#register` opens the register; `#open` jumps to the open items.

## Contributing

See `CONTRIBUTING.md` and the issue templates under `.github/ISSUE_TEMPLATE/`.

Corrections are most valuable for nodes with `confidence` below `high`. For each
correction, give the official URL, document number, date and current status.
Node ids are stable; do not rename them, add new ones instead.

## How to cite

> Hakimeh, Dani. *Oligonucleotide Regulatory Requirements Graph* (v0.4.2). Zenodo, 2026. https://doi.org/10.5281/zenodo.23818609

This concept DOI always resolves to the latest release. To cite a specific release, use its version DOI (v0.4.0: https://doi.org/10.5281/zenodo.23818610); each later release gets its own version DOI on Zenodo. GitHub shows the citation under “Cite this repository” (from `CITATION.cff`).

## Licence

Data (`*.json`, `*.csv`): CC BY 4.0. Code (`build.py`, `build_page.py`, `validate.py`, the page logic in `index.html`): MIT.
See `LICENSE`. Please cite using `CITATION.cff`.
