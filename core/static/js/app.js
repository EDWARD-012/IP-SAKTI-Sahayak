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
  // Local self-hosted UMD build → window.gsap (offline-safe, no CDN)
  await new Promise((resolve) => {
    if (window.gsap) { resolve(); return; }
    const s = document.createElement('script');
    s.src = '/static/js/gsap.min.js';
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

// ── 3D card tilt ─────────────────────────────────────────────────────────────

/**
 * Adds a perspective tilt-on-hover effect to every `.gov-card`.
 * Skipped for touch devices and when prefers-reduced-motion is set.
 */
function setupCardTilt() {
  if (prefersReducedMotion()) return;
  if (window.matchMedia?.('(hover: none)').matches) return;

  document.querySelectorAll('.gov-card').forEach((card) => {
    card.style.transformStyle = 'preserve-3d';
    card.style.willChange = 'transform';

    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const px = (e.clientX - rect.left) / rect.width - 0.5;
      const py = (e.clientY - rect.top) / rect.height - 0.5;
      card.style.transform =
        `perspective(800px) rotateY(${px * 8}deg) rotateX(${py * -8}deg) translateY(-4px) scale(1.015)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.transition = 'transform 0.45s cubic-bezier(0.22, 1, 0.36, 1)';
      card.style.transform = 'perspective(800px) rotateY(0) rotateX(0) translateY(0) scale(1)';
      setTimeout(() => { card.style.transition = ''; }, 500);
    });
  });
}

// ── Scroll reveal ────────────────────────────────────────────────────────────

/**
 * Fades in elements marked `.reveal-on-scroll` (and `.gov-card`) as they
 * enter the viewport, with a small stagger per sibling group.
 */
function setupScrollReveal() {
  if (prefersReducedMotion()) return;

  const targets = document.querySelectorAll('.reveal-on-scroll, .gov-card');
  if (!targets.length || !('IntersectionObserver' in window)) return;

  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-revealed');
      io.unobserve(entry.target);
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  targets.forEach((el, i) => {
    el.classList.add('reveal-pending');
    el.style.transitionDelay = `${Math.min(i % 6, 5) * 60}ms`;
    io.observe(el);
  });
}

// ── Theme toggle (light / dark, opt-in, localStorage) ────────────────────────

const THEME_LS_KEY = 'ipSaktiTheme';

function currentTheme() {
  return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
}

function applyTheme(theme) {
  const next = theme === 'dark' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', next);
  try { localStorage.setItem(THEME_LS_KEY, next); } catch { /* private browsing */ }

  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  const isDark = next === 'dark';
  btn.setAttribute('aria-pressed', String(isDark));
  btn.setAttribute('aria-label', isDark ? 'Switch to light theme' : 'Switch to dark theme');
  const label = btn.querySelector('.gov-theme-toggle__text');
  if (label) label.textContent = isDark ? 'Light' : 'Dark';
}

function setupThemeToggle() {
  applyTheme(currentTheme());
  document.documentElement.classList.add('theme-ready');
  document.getElementById('theme-toggle')?.addEventListener('click', () => {
    applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
  });
}

document.addEventListener('DOMContentLoaded', () => {
  setupThemeToggle();
  pageEntrance();
  setupHtmxListeners();
  setupFontSizeControls();
  setupRequestId();
  setupCardTilt();
  setupScrollReveal();
});
