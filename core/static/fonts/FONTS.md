# Offline Font Setup — IP-SAKTI Sahayak

All 22 Eighth Schedule languages need correct script rendering for the demo.
Use **Fontsource** npm packages to bundle WOFF2 files locally (no CDN needed offline).

Licence: OFL-1.1 (SIL Open Font Licence) — open-source, commercial use allowed.

---

## Step 1: Create a minimal Node.js project for font extraction

```powershell
cd C:\IP-SAKTI-Sahayak
npm init -y
```

## Step 2: Install all needed Noto Sans script packages

```powershell
npm install --save-dev `
  @fontsource/noto-sans `
  @fontsource/noto-sans-devanagari `
  @fontsource/noto-sans-bengali `
  @fontsource/noto-sans-tamil `
  @fontsource/noto-sans-telugu `
  @fontsource/noto-sans-gujarati `
  @fontsource/noto-sans-kannada `
  @fontsource/noto-sans-malayalam `
  @fontsource/noto-sans-oriya `
  @fontsource/noto-sans-gurmukhi `
  @fontsource/noto-sans-arabic `
  @fontsource/noto-sans-meetei-mayek `
  @fontsource/noto-sans-ol-chiki
```

## Step 3: Copy WOFF2 files to Django static folder

```powershell
# Run this script once after npm install:
python scripts/copy_fonts.py
```

`scripts/copy_fonts.py` content:
```python
import shutil, pathlib

NODE_MODULES = pathlib.Path("node_modules")
STATIC_FONTS = pathlib.Path("core/static/fonts")
STATIC_FONTS.mkdir(parents=True, exist_ok=True)

PACKAGES = [
    "@fontsource/noto-sans",
    "@fontsource/noto-sans-devanagari",
    "@fontsource/noto-sans-bengali",
    "@fontsource/noto-sans-tamil",
    "@fontsource/noto-sans-telugu",
    "@fontsource/noto-sans-gujarati",
    "@fontsource/noto-sans-kannada",
    "@fontsource/noto-sans-malayalam",
    "@fontsource/noto-sans-oriya",
    "@fontsource/noto-sans-gurmukhi",
    "@fontsource/noto-sans-arabic",    # Urdu, Sindhi, Kashmiri (Perso-Arabic)
    "@fontsource/noto-sans-meetei-mayek",  # Manipuri (Meitei script)
    "@fontsource/noto-sans-ol-chiki",   # Santali (Ol Chiki script)
]

WEIGHTS = ["400", "600"]  # Normal + semibold only — minimize payload

for pkg in PACKAGES:
    src_dir = NODE_MODULES / pkg / "files"
    if not src_dir.exists():
        print(f"Missing: {pkg}")
        continue
    for woff2 in src_dir.glob("*-{" + ",".join(WEIGHTS) + "}*.woff2"):
        dest = STATIC_FONTS / woff2.name
        shutil.copy2(woff2, dest)
        print(f"Copied: {woff2.name}")

print("Done. Update fonts.css with the copied files.")
```

---

## Step 4: Generate fonts.css

The `copy_fonts.py` script prints copied filenames. Use them to build `core/static/css/fonts.css`:

```css
/* Noto Sans — Latin + Extended (base) */
@font-face {
  font-family: "Noto Sans";
  font-style: normal;
  font-weight: 400;
  src: url("../fonts/noto-sans-latin-400-normal.woff2") format("woff2");
  unicode-range: U+0000-00FF;
}
/* Devanagari (Hindi, Marathi, Sanskrit, Maithili, Dogri, Nepali) */
@font-face {
  font-family: "Noto Sans Devanagari";
  font-style: normal;
  font-weight: 400;
  src: url("../fonts/noto-sans-devanagari-devanagari-400-normal.woff2") format("woff2");
  unicode-range: U+0900-097F;
}
/* Add remaining scripts following the same pattern. */
```

---

## Script–Language mapping

| Script | Fontsource package | Languages covered |
|---|---|---|
| Devanagari | `noto-sans-devanagari` | Hindi, Marathi, Sanskrit, Maithili, Dogri, Nepali, Bodo (also Devanagari) |
| Bengali | `noto-sans-bengali` | Bengali, Assamese |
| Tamil | `noto-sans-tamil` | Tamil |
| Telugu | `noto-sans-telugu` | Telugu |
| Gujarati | `noto-sans-gujarati` | Gujarati |
| Kannada | `noto-sans-kannada` | Kannada |
| Malayalam | `noto-sans-malayalam` | Malayalam |
| Oriya | `noto-sans-oriya` | Odia |
| Gurmukhi | `noto-sans-gurmukhi` | Punjabi |
| Arabic | `noto-sans-arabic` | Urdu, Sindhi, Kashmiri (Perso-Arabic) |
| Meetei Mayek | `noto-sans-meetei-mayek` | Manipuri |
| Ol Chiki | `noto-sans-ol-chiki` | Santali |

English uses the standard `noto-sans` package. Kashmiri in Devanagari script uses `noto-sans-devanagari`.

---

## Checklist

```
[ ] npm install (all packages above)
[ ] python scripts/copy_fonts.py
[ ] Create core/static/css/fonts.css with @font-face rules
[ ] Add fonts.css link to base.html <head> BEFORE tokens.css
[ ] Test RTL rendering: Urdu (ur), Sindhi (sd), Kashmiri Perso-Arabic (ks)
[ ] Verify Ol Chiki renders for Santali — very few browsers have it natively
```
