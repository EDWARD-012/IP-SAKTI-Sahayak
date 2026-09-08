---
name: frontend-theme
description: IP-SAKTI light/dark theme toggle. Use when changing colors, tokens, a11y bar, or the Dark/Light switch. Theme is opt-in via html[data-theme], never prefers-color-scheme.
---

# IP-SAKTI theme system

## Rule

Theme is **opt-in**. Never auto-invert with `@media (prefers-color-scheme: dark)` — that broke the GOI header. Use `html[data-theme="dark"]` only.

## Tokens

- Light defaults live on `:root` in `core/static/css/tokens.css`
- Dark overrides live on `html[data-theme="dark"]`
- Chrome (header / nav / footer) uses `--color-chrome` and `--color-nav` — these stay navy in both themes
- Page surfaces (`--color-bg`, `--color-surface`, `--color-text`) flip
- Links use `--color-link` (navy in light, `#8bb6ff` in dark)

## Toggle

- Button `#theme-toggle` in the accessibility bar (`base.html`)
- FOUC-prevention script in `<head>` reads `localStorage.ipSaktiTheme` before CSS
- `setupThemeToggle()` in `core/static/js/app.js` persists the choice and updates `aria-pressed` / label

## Do not

- Hardcode hex in templates or component CSS — use tokens
- Change `--color-primary` on the header (use `--color-chrome`)
- Drive theme from OS dark mode
