/**
 * IP-SAKTI Sahayak — Wizard page interactions
 *
 * Handles:
 *  - Radio card selection visual feedback (highlight selected `.gov-card`)
 *  - Smooth GSAP step-transition animation (fade-out old, fade-in new)
 *  - Progress bar update after each HTMX step swap
 */

'use strict';

// ── GSAP loader ──────────────────────────────────────────────────────────────

/** @type {object|null} */
let gsap = null;

/**
 * Loads GSAP: local vendor copy first, CDN fallback, then classic script tag.
 * @returns {Promise<object|null>}
 */
async function loadGsap() {
  try {
    const mod = await import('/static/js/vendor/gsap.esm.js');
    return mod.gsap ?? mod.default ?? null;
  } catch { /* not available locally */ }

  try {
    const mod = await import('https://cdn.skypack.dev/gsap@3.12.5?min');
    return mod.gsap ?? mod.default ?? null;
  } catch { /* CDN blocked */ }

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

// ── Radio card selection ──────────────────────────────────────────────────────

/**
 * Highlights the `.gov-card` parent of *radio* and removes the highlight
 * from all other cards in the same radio group.
 *
 * @param {HTMLInputElement} radio
 */
function selectRadioCard(radio) {
  const name = radio.name;
  if (!name) return;

  document
    .querySelectorAll(`input[type="radio"][name="${CSS.escape(name)}"]`)
    .forEach((r) => {
      const card = r.closest('.gov-card');
      if (!card) return;
      card.classList.remove('selected', 'ring-2', 'ring-navy');
      card.removeAttribute('aria-selected');
    });

  const selected = radio.closest('.gov-card');
  if (selected) {
    selected.classList.add('selected', 'ring-2', 'ring-navy');
    selected.setAttribute('aria-selected', 'true');
  }
}

/**
 * Attaches delegated change listeners for radio inputs inside `.gov-card`
 * containers and reflects the initial checked state on page load.
 */
function initRadioCardSelection() {
  document.body.addEventListener('change', (evt) => {
    const radio = /** @type {HTMLInputElement} */ (evt.target);
    if (radio.type !== 'radio') return;
    if (!radio.closest('.gov-card')) return;
    selectRadioCard(radio);
  });

  // Reflect any pre-checked inputs on page load
  document
    .querySelectorAll('input[type="radio"].gov-card-radio:checked')
    .forEach((r) => selectRadioCard(/** @type {HTMLInputElement} */ (r)));
}

// ── Step transition animation ─────────────────────────────────────────────────

const STEP_SELECTOR = '#wizard-step';

/**
 * Fades the wizard step container out before an HTMX request on a
 * `[data-wizard-form]` and fades it back in after the swap completes.
 */
function initStepTransitions() {
  document.body.addEventListener('htmx:beforeRequest', async (evt) => {
    const trigger = /** @type {Element|null} */ (evt.detail.elt);
    if (!trigger?.closest('[data-wizard-form]')) return;

    const stepEl = document.querySelector(STEP_SELECTOR);
    if (!stepEl) return;

    if (!gsap) gsap = await loadGsap();
    gsap?.to(stepEl, { opacity: 0, y: -6, duration: 0.2, ease: 'power1.in' });
  });

  document.body.addEventListener('htmx:afterSwap', async (evt) => {
    const target = /** @type {Element} */ (evt.detail.target);
    const stepEl =
      target.matches(STEP_SELECTOR)
        ? target
        : target.closest(STEP_SELECTOR) ?? document.querySelector(STEP_SELECTOR);

    if (!stepEl) return;

    if (!gsap) gsap = await loadGsap();
    if (!gsap) return;

    gsap.fromTo(
      stepEl,
      { opacity: 0, y: 8 },
      {
        opacity: 1,
        y: 0,
        duration: 0.35,
        ease: 'power2.out',
        clearProps: 'transform,opacity',
      }
    );
  });
}

// ── Progress bar ───────────────────────────────────────────────────────────────

/**
 * Updates the `#wizard-progress` `<progress>` element after each HTMX swap.
 *
 * The server must include a `data-wizard-step` attribute on the swapped-in
 * content (e.g. `<div data-wizard-step="2" data-wizard-total="5">`).
 * `data-wizard-total` defaults to 5 if absent.
 */
function initProgressBar() {
  const bar = /** @type {HTMLProgressElement|null} */ (
    document.getElementById('wizard-progress')
  );
  if (!bar) return;

  document.body.addEventListener('htmx:afterSwap', (evt) => {
    const swapped = /** @type {Element} */ (evt.detail.target);

    // Find the data attributes on the swapped content or its children
    const dataEl =
      swapped.dataset?.wizardStep != null
        ? swapped
        : swapped.querySelector('[data-wizard-step]');

    if (!dataEl) return;

    const step  = parseInt(/** @type {HTMLElement} */ (dataEl).dataset.wizardStep  ?? '1', 10);
    const total = parseInt(/** @type {HTMLElement} */ (dataEl).dataset.wizardTotal ?? '5', 10);
    const pct   = Math.round((step / total) * 100);

    bar.value = pct;
    bar.setAttribute('aria-valuenow',  String(pct));
    bar.setAttribute('aria-valuetext', `Step ${step} of ${total}`);

    const label = document.getElementById('wizard-step-label');
    if (label) label.textContent = `Step ${step} of ${total}`;
  });
}

// ── Boot ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  initRadioCardSelection();
  initStepTransitions();
  initProgressBar();
});
