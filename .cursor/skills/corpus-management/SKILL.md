---
name: corpus-management
description: Acquire, parse, version and validate the IP-SAKTI legal corpus. Use when downloading statutes, managing source manifests, running the ingestion pipeline, updating corpus versions, or verifying sources against the approved P0/P1 list. Also use when the user mentions source acquisition, YAML manifests, corpus versioning, CorpusVersion model, or legal document parsing.
disable-model-invocation: true
---

# IP-SAKTI Corpus Management

## Source priority tiers
| Tier | Examples | Action |
|------|----------|--------|
| P0 (must have for MVP) | Patents Act 1970, GI Act 1999, BD Act 2002+2023, D&C Act 1940, D&C Rules 1945, Ayurveda Aahara Regs 2022, TKDL, TRIPS/CBD/Nagoya/WIPO GRATK | Acquire before Day 3 |
| P1 (should have) | Patents Rules 2003+2024, BD Rules 2024, NDCT Rules 2019, D&C Rules Schedule T, DPDP Act 2023 | Acquire in Days 2-5 |

## Source manifest YAML (one file per source, in `data/manifests/`)
```yaml
source_id: patents-act-1970          # lowercase-hyphen, unique
title: The Patents Act, 1970
authority: Legislative Department / India Code
jurisdiction: IN
ip_type: [patents]
landing_url: https://indiacode.gov.in/
download_url: ""                      # fill after download
locator_status: verified              # verified | pending | broken
retrieved_at: 2026-09-08
effective_from: 1970-09-19
effective_status: current             # current | amended | repealed | draft
reuse_basis: public-statute           # public-statute | official-open | verify-and-record
sha256: ""                            # fill after download
reviewer: ""                          # team member name
notes: ""
```

## Acquisition workflow (per source)
```
[ ] 1. Verify landing_url is live → update locator_status
[ ] 2. Download PDF to data/raw/<source_id>.pdf
[ ] 3. sha256sum → fill manifest sha256
[ ] 4. Review reuse_basis (public-statute needs no further licence step)
[ ] 5. Fill reviewer name + retrieved_at
[ ] 6. Move to data/staging/ when manifest is complete
[ ] 7. Run: python scripts/parse_chunk.py data/staging/<source_id>.pdf
[ ] 8. Inspect 5 random chunks for OCR quality
[ ] 9. Run golden-set retrieval test with this source
[ ] 10. Move to data/corpus/ on pass
```

## Known tricky sources
| Source | Issue | Workaround |
|--------|-------|------------|
| India Code Patents Act | `indiacode.nic.in` → migrated to `indiacode.gov.in` | Use migrated portal; search by exact title |
| NBA / BD Rules 2024 | Old `nbaindia.org/blog/...` is 404 | Try `nbaindia.org/statutory-rules` or e-Gazette |
| D&C Rules 1945 (Schedule T) | Deep in compiled rules PDF | Extract pages 400+ of CDSCO compilation |
| Patents Rules 2024 | Two separate notifications (Mar 15 + Mar 16 2024) | Download both from `ipindia.gov.in/pages/patents/publications/rules` |
| WIPO GRATK Treaty | Adopted May 24, 2024; not yet in force for India | Label `effective_status: signed-not-in-force` |

## CorpusVersion lifecycle
```
building → validated → active → retired
                     ↓
                   failed
```
- Only one `active` version at a time; all others are `retired` or `failed`
- Swap via Django management command: `python manage.py activate_corpus_version <version>`
- `chroma_collection` field names the Chroma collection (`ip_sakti_v{version}`)

## Ingestion script (`scripts/ingest.ps1`)
```powershell
# Run offline, outside the running Django app
python manage.py build_corpus_version --sources data/corpus/ --version 1
# This: parses PDFs, chunks, embeds (bge-m3), writes ip_sakti_v1 in Chroma
# Then run validation:
python manage.py validate_corpus_version --version 1
# On pass:
python manage.py activate_corpus_version --version 1
```

## Parsing notes for Indian legal PDFs
- Section headers: `r'^\s*(Section|Rule|Article|Clause|Schedule)\s+[\dA-Z]+'` (multiline)
- Provisos start with "Provided that" — keep attached to parent section chunk
- Explanations marked "Explanation" — keep attached to parent section chunk
- Amendment insertions: look for "(inserted by Act ... w.e.f. ...)" — record in `effective_from`
- OCR artifacts: double-check section numbers, "I" vs "1", "O" vs "0", negation words

## Evaluation gate before corpus activation
- Run 30-question golden set: `pytest tests/test_corpus_golden.py`
- Accept if ≥ 25/30 pass (citation present + correct source_id)
- Reject if any P0 source is missing from retrieved results
