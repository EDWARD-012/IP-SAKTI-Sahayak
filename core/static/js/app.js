/**
 * IP-SAKTI Sahayak — Main application JS entrypoint
 *
 * Responsibilities:
 *  - GSAP page-entrance animation (respects prefers-reduced-motion)
 *  - HTMX lifecycle event listeners (before / after request, afterSwap)
 *  - Font-size A+ / A / A- controls with localStorage persistence
 *  - UUID-based request_id injection for every chat form submission
 *  - dotLottie player initialisation
 */

'use strict';

// ── GSAP loader ──────────────────────────────────────────────────────────────

/** @type {object|null} */
let gsap = null;

/**
 * Loads GSAP by trying, in order:
 *   1. Local static vendor copy at /static/js/vendor/gsap.esm.js
 *   2. Skypack CDN ES module shim
 *   3. Classic <script> tag → window.gsap (cdnjs)
 *
 * @returns {Promise<object|null>}
 */
async function loadGsap() {
  // ① Local vendor copy (placed by a build / vendor-copy step)
  try {
    const mod = await import('/static/js/vendor/gsap.esm.js');
    return mod.gsap ?? mod.default ?? null;
  } catch { /* not available locally */ }

  // ② Skypack CDN ES module
  try {
    const mod = await import('https://cdn.skypack.dev/gsap@3.12.5?min');
    return mod.gsap ?? mod.default ?? null;
  } catch { /* CDN blocked or offline */ }

  // ③ Classic script-tag injection → window.gsap
  await new Promise((resolve) => {
    if (window.gsap) { resolve(); return; }
    const s = document.createElement('script');
    s.src = 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js';
    s.crossOrigin = 'anonymous';
    s.referrerPolicy = 'no-referrer';
    s.onload = resolve;
    s.onerror = resolve;
    document.head.appendChild(s);
  });
  return window.gsap ?? null;
}

// ── Reduced-motion check ─────────────────────────────────────────────────────

/**
 * Returns true when the user's OS/browser requests minimal motion.
 * @returns {boolean}
 */
function prefersReducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
}

// ── Page entrance animation ──────────────────────────────────────────────────

/**
 * Runs the staggered entrance animation on all `.ip-fade-in` elements.
 * Silently skips when prefers-reduced-motion is active or GSAP fails to load.
 *
 * @returns {Promise<void>}
 */
async function pageEntrance() {
  if (prefersReducedMotion()) return;

  const elements = document.querySelectorAll('.ip-fade-in');
  if (!elements.length) return;

  if (!gsap) gsap = await loadGsap();
  if (!gsap) return;

  gsap.from(elements, {
    y: 8,
    opacity: 0,
    duration: 0.4,
    stagger: 0.08,
    ease: 'power2.out',
    clearProps: 'transform,opacity',
  });
}

// ── HTMX event listeners ─────────────────────────────────────────────────────

/**
 * Wires HTMX lifecycle hooks onto document.body:
 *  - `htmx:beforeRequest`  → disable submit button, reveal cancel button
 *  - `htmx:afterRequest`   → re-enable submit, hide cancel button
 *  - `htmx:afterSwap`      → scroll swapped element into view + entrance anim
 */
function setupHtmxListeners() {
  document.body.addEventListener('htmx:beforeRequest', (evt) => {
    const form = evt.detail.elt?.closest('form');
    if (!form) return;

    form.querySelector('[type="submit"]')?.setAttribute('disabled', 'true');
    const cancel = form.querySelector('.js-cancel-btn');
    if (cancel) {
      cancel.hidden = false;
      cancel.classList.remove('hidden');
    }
  });

  document.body.addEventListener('htmx:afterRequest', (evt) => {
    const form = evt.detail.elt?.closest('form');
    if (!form) return;

    form.querySelector('[type="submit"]')?.removeAttribute('disabled');
    const cancel = form.querySelector('.js-cancel-btn');
    if (cancel) {
      cancel.hidden = true;
      cancel.classList.add('hidden');
    }
  });

  document.body.addEventListener('htmx:afterSwap', async (evt) => {
    const target = evt.detail.target;
    if (!target) return;

    // Smooth-scroll the newly swapped content into view
    target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // Run entrance animation on .ip-fade-in children inside the swapped region
    if (!prefersReducedMotion()) {
      const fresh = target.querySelectorAll('.ip-fade-in');
      if (fresh.length) {
        if (!gsap) gsap = await loadGsap();
        if (!gsap) return;

        gsap.from(fresh, {
          y: 8,
          opacity: 0,
          duration: 0.4,
          stagger: 0.08,
          ease: 'power2.out',
          clearProps: 'transform,opacity',
        });
      }
    }
  });
}

// ── Font-size controls ───────────────────────────────────────────────────────

/** @type {Record<string, string>} */
const FONT_SIZES = { large: '118%', normal: '100%', small: '88%' };
const FONT_LS_KEY = 'ipSaktiFontSize';

/**
 * Applies a named font-size level to `<html>`, updates button aria-pressed
 * states, and persists the choice to localStorage.
 *
 * @param {'large'|'normal'|'small'} level
 */
function applyFontSize(level) {
  const size = FONT_SIZES[level] ?? FONT_SIZES.normal;
  document.documentElement.style.fontSize = size;

  document.querySelectorAll('.js-font-btn').forEach((btn) => {
    const isActive = btn.dataset.fontSize === level;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-pressed', String(isActive));
  });

  try {
    localStorage.setItem(FONT_LS_KEY, level);
  } catch { /* private browsing / storage quota */ }
}

/**
 * Initialises the A+ / A / A- font-size toolbar and restores the last saved
 * preference from localStorage.
 */
function setupFontSizeControls() {
  const saved = (() => {
    try { return localStorage.getItem(FONT_LS_KEY); } catch { return null; }
  })();

  applyFontSize(saved ?? 'normal');

  document.querySelectorAll('.js-font-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      applyFontSize(btn.dataset.fontSize ?? 'normal');
    });
  });
}

// ── Request-ID injection ─────────────────────────────────────────────────────

/**
 * Generates a new UUID v4 before every HTMX request on forms marked with
 * `data-request-id-form`, injects it as `request_id` in the request params,
 * and writes it into the `#request-id-field` hidden input.
 */
function setupRequestId() {
  document.body.addEventListener('htmx:configRequest', (evt) => {
    const form = evt.detail.elt?.closest('form[data-request-id-form]');
    if (!form) return;

    const requestId = crypto.randomUUID();
    evt.detail.parameters['request_id'] = requestId;

    const hidden = form.querySelector('#request-id-field');
    if (hidden) hidden.value = requestId;
  });
}

// ── dotLottie player initialisation ─────────────────────────────────────────

/**
 * Waits for the `dotlottie-player` custom element to be registered, then
 * calls `.load(src)` on every `<dotlottie-player data-src="…">` in the page.
 */
function initLottie() {
  const players = /** @type {NodeListOf<HTMLElement>} */ (
    document.querySelectorAll('dotlottie-player[data-src]')
  );
  if (!players.length) return;

  const tryInit = () => {
    if (customElements.get('dotlottie-player')) {
      players.forEach((player) => {
        const src = /** @type {string|undefined} */ (player.dataset.src);
        if (src && typeof (/** @type {any} */ (player)).load === 'function') {
          /** @type {any} */ (player).load(src);
        }
      });
    } else {
      // Custom element not yet defined — retry on the next animation frame
      requestAnimationFrame(tryInit);
    }
  };

  tryInit();
}

// ── Boot ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  pageEntrance();
  setupHtmxListeners();
  setupFontSizeControls();
  setupRequestId();
  initLottie();
});
