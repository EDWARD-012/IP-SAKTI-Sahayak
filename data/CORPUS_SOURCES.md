# Corpus Sources — Acquisition Guide

The IP-SAKTI corpus is assembled **only from open, authoritative, public**
Government of India / UN sources. Every document has a manifest in
`data/manifests/<source_id>.yaml`. To ingest, download each document as
`data/raw/<source_id>.pdf` (filename **must** match the `source_id`), then run:

```powershell
python manage.py build_corpus_version 1.0
python manage.py validate_corpus_version 1.0
python manage.py activate_corpus_version 1.0
```

> `data/raw/` is git-ignored — source documents are never committed, only the
> manifests (with SHA-256 recorded after ingestion) and the built index.

---

## Authoritative source portals

| Portal | URL | What to get |
|---|---|---|
| **India Code** | https://www.indiacode.nic.in/ | Consolidated Acts & Rules (statutes) |
| **IP India** | https://ipindia.gov.in/ | Patent/GI/TM/Design rules, forms, InPASS search, GI Registry |
| **National Biodiversity Authority** | https://nbaindia.org/ | ABS guidelines, NBA forms, biodiversity rules |
| **TKDL** | https://www.tkdl.res.in/ | Traditional Knowledge Digital Library (public/about material only) |
| **FSSAI** | https://www.fssai.gov.in/ | Ayurveda Aahara Regulations 2022 |
| **Ministry of Ayush** | https://ayush.gov.in/ | ASU drug licensing, policy |
| **CDSCO** | https://cdsco.gov.in/ | Drugs & Cosmetics regulation |
| **WTO** | https://www.wto.org/ | TRIPS Agreement (official text) |
| **CBD Secretariat (UN)** | https://www.cbd.int/abs/ | Nagoya Protocol (official text) |

---

## Per-document checklist

| source_id | Title | Primary source | Notes |
|---|---|---|---|
| `patents-act-1970` | Patents Act, 1970 (amended) | India Code | Focus: §3(p), §25; Patent Rules on ipindia.gov.in |
| `gi-act-1999` | GI (Registration & Protection) Act, 1999 | India Code | §11–12 registration; GI Registry on ipindia.gov.in |
| `biological-diversity-act-2002` | Biological Diversity Act, 2002 (amended 2023) | India Code | §3, §7 ABS; NBA guidelines on nbaindia.org |
| `drugs-cosmetics-act-1940` | Drugs & Cosmetics Act 1940 + Rules 1945 | India Code | ASU drugs §33C–33O, Schedule T (GMP), Schedule E(1) |
| `ayurveda-aahara-regs-2022` | FSS (Ayurveda Aahara) Regulations, 2022 | FSSAI | Labelling/claims; gazette notification PDF |
| `nagoya-protocol` | Nagoya Protocol on ABS | CBD (UN) | Art. 5, 6; freely reproducible UN treaty |
| `trips-agreement` | TRIPS Agreement | WTO | Art. 22–24 (GI), 27–34 (patents), 39 |
| `tkdl` | Traditional Knowledge Digital Library | TKDL | **PUBLIC/about material only** — DB records are access-restricted |

---

## Licence / reuse notes (see also `LICENCES.md`)

- **Statutes & rules** (India Code): Government works — reproducible with
  attribution. `reuse_basis: public-statute`.
- **UN/WTO treaties** (Nagoya, TRIPS): official texts freely reproducible.
  `reuse_basis: official-open`.
- **TKDL**: the full database is **access-restricted** (patent-office access
  agreements). Ingest **only** public descriptive pages, and record the licence
  of each captured page. `reuse_basis: verify-and-record`.
- Always record the **retrieval date** and **SHA-256** (ingestion does the
  latter automatically and writes it back to the `SourceManifest` row).

---

## Testing without the real PDFs

For a pipeline smoke-test you can drop small **plain-text excerpts** as
`data/raw/<source_id>.txt` (e.g. a paragraph containing "Section 3(p) …").
The ingestion pipeline treats `.txt` and `.pdf` identically, so you can verify
chunking → embedding → retrieval end-to-end before sourcing full documents.
