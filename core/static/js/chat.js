/**
 * IP-SAKTI Sahayak — Chat page interactions
 *
 * Handles:
 *  - Textarea auto-resize as the user types
 *  - Character counter (max 1000 chars)
 *  - Ctrl+Enter / Cmd+Enter keyboard shortcut to submit
 *  - Citation expand / collapse toggles
 *  - Copy citation text to clipboard
 *  - Scroll chat history to bottom on new messages
 *  - Cancel button visibility tied to HTMX loading state
 *  - Session-clear confirmation dialog
 *  - request_id UUID generation and tracking per submission
 */

'use strict';

// ── Module state ─────────────────────────────────────────────────────────────

/** UUID of the most recently submitted request (updated on each submit). */
let currentRequestId = null;

// ── Textarea auto-resize ─────────────────────────────────────────────────────

/**
 * Resizes *textarea* to fit its current content.
 * @param {HTMLTextAreaElement} textarea
 */
function autoResize(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = `${textarea.scrollHeight}px`;
}

/**
 * Attaches auto-resize behaviour to every `.js-auto-resize` textarea.
 * Also fires once on load to handle pre-filled values.
 */
function initTextareaAutoResize() {
  document.querySelectorAll('textarea.js-auto-resize').forEach((ta) => {
    ta.addEventListener('input', () => autoResize(/** @type {HTMLTextAreaElement} */ (ta)));
    autoResize(/** @type {HTMLTextAreaElement} */ (ta));
  });
}

// ── Character counter ────────────────────────────────────────────────────────

/**
 * Wires a live character counter for every textarea that declares a
 * `data-char-counter="<counterId>"` attribute.
 *
 * The counter element receives the remaining characters and a `.warn` class
 * when fewer than 50 characters remain.
 */
function initCharCounter() {
  document.querySelectorAll('textarea[data-char-counter]').forEach((ta) => {
    const maxLen = parseInt(ta.getAttribute('maxlength') ?? '1000', 10);
    const counter = document.getElementById(/** @type {string} */ (ta.dataset.charCounter ?? ''));

    if (!counter) return;

    const update = () => {
      const remaining = maxLen - ta.value.length;
      counter.textContent = String(remaining);
      counter.classList.toggle('warn', remaining < 50);
      counter.setAttribute('aria-label', `${remaining} characters remaining`);
    };

    ta.addEventListener('input', update);
    update();
  });
}

// ── Keyboard shortcuts ───────────────────────────────────────────────────────

/**
 * Ctrl+Enter (or Cmd+Enter on macOS) programmatically clicks the submit
 * button of the form that contains the focused textarea.
 */
function initKeyboardShortcuts() {
  document.addEventListener('keydown', (evt) => {
    if (!(evt.ctrlKey || evt.metaKey) || evt.key !== 'Enter') return;

    const active = document.activeElement;
    if (active?.tagName !== 'TEXTAREA') return;

    const form = active.closest('form');
    const submitBtn = form?.querySelector('[type="submit"]:not([disabled])');
    submitBtn?.click();
  });
}

// ── Citation toggles ─────────────────────────────────────────────────────────

/**
 * Handles click-to-expand / collapse for `.js-citation-toggle` buttons.
 * Each toggle must carry a `data-target="<elementId>"` attribute pointing
 * to the details container to show or hide.
 */
function initCitationToggles() {
  document.body.addEventListener('click', (evt) => {
    const toggle = evt.target.closest('.js-citation-toggle');
    if (!toggle) return;

    const targetEl = toggle.dataset.target
      ? document.getElementById(toggle.dataset.target)
      : null;
    if (!targetEl) return;

    const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
    targetEl.hidden = isExpanded;
    targetEl.classList.toggle('hidden', isExpanded);
    toggle.setAttribute('aria-expanded', String(!isExpanded));
  });
}

// ── Copy citation ────────────────────────────────────────────────────────────

/**
 * Copies citation text to the clipboard when a `.js-copy-citation` button
 * is clicked. The text is taken from:
 *   - `data-copy-text` (inline attribute), or
 *   - the `textContent` of the element identified by `data-copy-from`.
 *
 * On success the button label briefly changes to "✓ Copied".
 */
function initCopyCitation() {
  document.body.addEventListener('click', async (evt) => {
    const btn = evt.target.closest('.js-copy-citation');
    if (!btn) return;

    let text = btn.dataset.copyText ?? '';
    if (!text && btn.dataset.copyFrom) {
      text = document.getElementById(btn.dataset.copyFrom)?.textContent?.trim() ?? '';
    }
    if (!text) return;

    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Clipboard API unavailable (HTTP or non-secure context) — silent fail
      return;
    }

    const original = btn.textContent;
    const originalLabel = btn.getAttribute('aria-label');
    btn.textContent = '✓ Copied';
    btn.setAttribute('aria-label', 'Copied to clipboard');
    setTimeout(() => {
      btn.textContent = original;
      if (originalLabel) btn.setAttribute('aria-label', originalLabel);
      else btn.removeAttribute('aria-label');
    }, 2000);
  });
}

// ── Cancel button ─────────────────────────────────────────────────────────────

/**
 * Shows / hides the `.js-cancel-btn` in sync with HTMX loading state and
 * aborts the in-flight request when the button is clicked.
 */
function initCancelButton() {
  document.body.addEventListener('htmx:beforeRequest', (evt) => {
    const form = evt.detail.elt?.closest('form');
    const btn = form?.querySelector('.js-cancel-btn');
    if (!btn) return;
    btn.hidden = false;
    btn.classList.remove('hidden');
  });

  document.body.addEventListener('htmx:afterRequest', (evt) => {
    const form = evt.detail.elt?.closest('form');
    const btn = form?.querySelector('.js-cancel-btn');
    if (!btn) return;
    btn.hidden = true;
    btn.classList.add('hidden');
  });

  document.body.addEventListener('click', (evt) => {
    const btn = evt.target.closest('.js-cancel-btn');
    if (!btn) return;

    // Ask HTMX to abort the in-flight request on the enclosing form
    const form = btn.closest('form');
    if (form && typeof htmx !== 'undefined') {
      htmx.trigger(form, 'htmx:abort');
    }

    btn.hidden = true;
    btn.classList.add('hidden');
  });
}

// ── Session clear ────────────────────────────────────────────────────────────

/**
 * Intercepts clicks on `.js-session-clear` elements and presents a
 * confirmation dialog before allowing the action to proceed.
 */
function initSessionClear() {
  document.body.addEventListener('click', (evt) => {
    const btn = evt.target.closest('.js-session-clear');
    if (!btn) return;

    const message =
      btn.dataset.confirmMessage ??
      'Clear all chat history for this session? This cannot be undone.';

    if (!window.confirm(message)) {
      evt.preventDefault();
      evt.stopImmediatePropagation();
    }
  });
}

// ── Auto-scroll ───────────────────────────────────────────────────────────────

/**
 * Scrolls *container* to its very bottom.
 * @param {Element|null} [container] Defaults to `#chat-history`.
 */
function scrollToBottom(container) {
  const el = container ?? document.getElementById('chat-history');
  if (!el) return;
  el.scrollTop = el.scrollHeight;
}

/**
 * Scrolls chat history to the bottom on load and after every HTMX swap that
 * targets `#chat-history` or one of its descendants.
 */
function initAutoScroll() {
  const history = document.getElementById('chat-history');
  if (!history) return;

  scrollToBottom(history);

  document.body.addEventListener('htmx:afterSwap', (evt) => {
    const target = evt.detail.target;
    if (target && (history.contains(target) || target === history)) {
      scrollToBottom(history);
    }
  });
}

// ── Request-ID tracking ───────────────────────────────────────────────────────

/**
 * Generates a new UUID v4.
 * @returns {string}
 */
function generateRequestId() {
  return crypto.randomUUID();
}

/**
 * Updates `currentRequestId` before each HTMX request on forms marked with
 * `data-request-id-form`, and writes the UUID into both the request parameters
 * and the `#request-id-field` hidden input.
 */
function initRequestIdTracking() {
  document.body.addEventListener('htmx:configRequest', (evt) => {
    const form = evt.detail.elt?.closest('form[data-request-id-form]');
    if (!form) return;

    currentRequestId = generateRequestId();
    evt.detail.parameters['request_id'] = currentRequestId;

    const field = form.querySelector('#request-id-field');
    if (field) field.value = currentRequestId;
  });
}

// ── Boot ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  initTextareaAutoResize();
  initCharCounter();
  initKeyboardShortcuts();
  initCitationToggles();
  initCopyCitation();
  initCancelButton();
  initSessionClear();
  initAutoScroll();
  initRequestIdTracking();
});

export { generateRequestId, scrollToBottom, currentRequestId };
