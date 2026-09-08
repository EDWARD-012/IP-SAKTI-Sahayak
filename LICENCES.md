# Corpus Licence Manifest — IP-SAKTI Sahayak

This file tracks the reuse basis for every source document in the corpus.
Update this file whenever a new source is added or its licence status changes.

## Source Inventory

| source_id | title (short) | reuse_basis | effective_status | note |
|---|---|---|---|---|
| patents-act-1970 | The Patents Act, 1970 | public-statute | current | Indian statute — public domain |
| gi-act-1999 | GI of Goods Act, 1999 | public-statute | current | Indian statute — public domain |
| biological-diversity-act-2002 | Biological Diversity Act, 2002 | public-statute | amended | Indian statute — amended 2023 — public domain |

## Reuse Basis Definitions

- **public-statute**: Acts of Parliament of India published on indiacode.gov.in.
  Indian statutes are in the public domain; no licence is required.
- **official-open**: Released by the originating authority under an explicit open
  licence (e.g. CC BY 4.0, Open Government Licence India). Record the licence
  URL in the `notes` field of the source manifest YAML.
- **verify-and-record**: Licence status is unclear or not yet confirmed. Do **not**
  ingest this source until the licence is verified. Record evidence (URL, email,
  or document reference) in the YAML `notes` field and update this table once
  confirmed.

## Policy

1. Every file in `data/corpus/` must have a corresponding entry in
   `data/manifests/<source_id>.yaml` and a row in this table.
2. Only `public-statute` and `official-open` sources may be ingested without
   further review.
3. `verify-and-record` sources must be approved before ingestion.
   Open an issue referencing the source manifest and link the licence evidence.
