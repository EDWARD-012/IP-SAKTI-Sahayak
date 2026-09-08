# IP-SAKTI Animation Assets

All animations must be downloaded **before the demo** and placed in this folder.
LottieFiles free animations are licensed under the **Lottie Simple License** — commercial use
allowed, no attribution required (but credit the creator when shown publicly).

---

## Download list

Run this checklist during corpus-acquisition sprint (Days 1–2).

### Priority 1 — Must have for MVP demo

| File to save as | LottieFiles URL | Usage in product |
|---|---|---|
| `justice-scale.lottie` | https://lottiefiles.com/free-animation/justice-balance-law-rT06jeQVju | Homepage hero / loading splash |
| `document-search.lottie` | https://lottiefiles.com/free-animation/law-scale-OQC2ci7HaO | Chat empty state |
| `thinking-dots.lottie` | https://lottiefiles.com/free-animation/loading-pSObk0LNXM | Inline "model thinking" state |

**How to download:**
1. Open the URL
2. Click **Download → dotLottie (.lottie)**  ← use `.lottie` format, not JSON
3. Save to `core/static/animations/<filename>`
4. Verify the file opens in [LottieFiles Preview](https://lottiefiles.com/preview)

### Priority 2 — Should have

| File | URL | Usage |
|---|---|---|
| `document-check.lottie` | https://lottiefiles.com/free-animation/law-and-justice-RLXP4Z76rg | Source verified tick |
| `empty-search.lottie` | https://lottiefiles.com/free-animation/justice-NPX2kHj01Z | No results state |

---

## Integration in Django templates

### 1. Load the player (in `base.html` `<head>`)
```html
<!-- dotlottie-player web component — self-host for offline use -->
<!-- Download from: https://unpkg.com/@dotlottie/player-component@latest/dist/dotlottie-player.mjs -->
<!-- Save to: core/static/js/dotlottie-player.mjs -->
<script type="module" src="{% static 'js/dotlottie-player.mjs' %}"></script>
```

### 2. Use in templates
```html
<!-- Hero animation -->
<dotlottie-player
  class="lottie-anim"
  src="{% static 'animations/justice-scale.lottie' %}"
  autoplay
  loop
  style="width: 180px; height: 180px;"
  aria-hidden="true">
</dotlottie-player>

<!-- Inline thinking indicator (HTMX loading) -->
<div id="thinking-dots" class="ip-thinking htmx-indicator" aria-live="polite" aria-label="Thinking…">
  <span class="ip-thinking__dot"></span>
  <span class="ip-thinking__dot"></span>
  <span class="ip-thinking__dot"></span>
</div>
```

### 3. CSS fallback (if Lottie doesn't load)
The `tokens.css` already defines `.ip-thinking` with pure CSS bouncing dots.
That serves as the fallback — just keep `#thinking-dots` in the DOM always.

---

## GSAP (page entrance only)

Download: https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js
Save to: `core/static/js/gsap.min.js`

Usage (one tween, page load only):
```js
// core/static/js/app.js
import { gsap } from "/static/js/gsap.min.js";

document.addEventListener("DOMContentLoaded", () => {
  gsap.from(".ip-fade-in", {
    duration: 0.4,
    y: 8,
    opacity: 0,
    stagger: 0.08,
    ease: "power2.out",
    clearProps: "all"
  });
});
```

---

## File checklist before demo

```
core/static/
  css/
    tokens.css                 ✅ created
  animations/
    justice-scale.lottie       [ ] download
    document-search.lottie     [ ] download
    thinking-dots.lottie       [ ] download
    document-check.lottie      [ ] download
    empty-search.lottie        [ ] download
    ASSETS.md                  ✅ this file
  js/
    dotlottie-player.mjs       [ ] download
    gsap.min.js                [ ] download
    app.js                     [ ] create during frontend sprint
```
