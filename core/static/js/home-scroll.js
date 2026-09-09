/**
 * IP-SAKTI home motion — GSAP + ScrollTrigger (self-hosted).
 * Hero timeline, scrubbed statute rail, soft-pin header,
 * ScrollTrigger.batch on statute cards, CSS-perspective card tilt.
 */
'use strict';

function reducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
}

function waitForGsap(timeoutMs = 4000) {
  return new Promise((resolve) => {
    if (window.gsap) {
      resolve(window.gsap);
      return;
    }
    const start = Date.now();
    const id = setInterval(() => {
      if (window.gsap) {
        clearInterval(id);
        resolve(window.gsap);
      } else if (Date.now() - start > timeoutMs) {
        clearInterval(id);
        resolve(null);
      }
    }, 40);
  });
}

function setupCardTilt(cards) {
  if (reducedMotion()) return;
  if (window.matchMedia?.('(pointer: coarse)').matches) return;

  cards.forEach((card) => {
    card.addEventListener('pointermove', (e) => {
      const r = card.getBoundingClientRect();
      const nx = (e.clientX - r.left) / Math.max(r.width, 1) - 0.5;
      const ny = (e.clientY - r.top) / Math.max(r.height, 1) - 0.5;
      card.style.transform = `rotateY(${nx * 7}deg) rotateX(${-ny * 6}deg) translateZ(0)`;
    });
    card.addEventListener('pointerleave', () => {
      card.style.transform = '';
    });
  });
}

/** Respectful emblem motion: cursor tilt + scroll lift (no WebGL). */
function setupEmblemMotion(gsap, ST) {
  const el = document.querySelector('[data-home-emblem]');
  if (!el || reducedMotion()) return;

  const host = el.closest('.home-hero') || el;
  if (!window.matchMedia?.('(pointer: coarse)').matches) {
    host.addEventListener('pointermove', (e) => {
      const r = host.getBoundingClientRect();
      const nx = (e.clientX - r.left) / Math.max(r.width, 1) - 0.5;
      const ny = (e.clientY - r.top) / Math.max(r.height, 1) - 0.5;
      el.style.transform = `rotateY(${nx * 10}deg) rotateX(${-ny * 7}deg)`;
    });
    host.addEventListener('pointerleave', () => {
      el.style.transform = '';
    });
  }

  if (!ST) return;
  gsap.fromTo(
    el,
    { y: 0 },
    {
      y: -28,
      ease: 'none',
      scrollTrigger: {
        trigger: '.home-hero',
        start: 'top top',
        end: 'bottom top',
        scrub: 0.7,
      },
    },
  );
}

async function initHomeMotion() {
  if (!document.body.classList.contains('page-home') && !document.querySelector('.home-hero')) {
    return;
  }

  const gsap = await waitForGsap();
  if (!gsap) {
    document.documentElement.classList.remove('js-home-motion');
    return;
  }

  const ST = window.ScrollTrigger;
  if (ST) gsap.registerPlugin(ST);

  document.documentElement.classList.add('js-home-motion');

  const heroEls = gsap.utils.toArray('.js-home-hero');
  const cards = gsap.utils.toArray('.home-card');
  const prompts = gsap.utils.toArray('.js-home-prompt');
  const railTrack = document.querySelector('.home-rail__track');
  const pinEl = document.querySelector('[data-home-pin]');
  const corpus = document.querySelector('[data-home-corpus]');

  if (reducedMotion()) {
    gsap.set([...heroEls, ...cards, ...prompts], { opacity: 1, clearProps: 'transform' });
    gsap.set('.home-card__rail', { scaleY: 1 });
    gsap.set('.home-card__cite', { opacity: 1, y: 0 });
    document.documentElement.classList.remove('js-home-motion');
    return;
  }

  // Hero entrance
  if (heroEls.length) {
    gsap.set(heroEls, { opacity: 0, y: 28 });
    gsap.timeline({ defaults: { ease: 'power3.out' } }).to(heroEls, {
      opacity: 1,
      y: 0,
      duration: 0.65,
      stagger: 0.09,
      clearProps: 'transform',
    });
  }

  setupEmblemMotion(gsap, ST);

  if (!ST) {
    gsap.to([...cards, ...prompts], { opacity: 1, duration: 0.35, stagger: 0.05 });
    gsap.set('.home-card__rail', { scaleY: 1 });
    return;
  }

  // Scrubbed statute rail — scroll progress through rail section
  if (railTrack) {
    gsap.fromTo(
      railTrack,
      { x: 0 },
      {
        x: () => Math.min(0, window.innerWidth - railTrack.scrollWidth - 48),
        ease: 'none',
        scrollTrigger: {
          trigger: '.home-rail',
          start: 'top bottom',
          end: 'bottom top',
          scrub: 0.6,
          invalidateOnRefresh: true,
        },
      },
    );
  }

  // Soft pin section header while cards approach
  if (pinEl) {
    ScrollTrigger.create({
      trigger: pinEl,
      start: 'top top+=72',
      end: '+=220',
      pin: true,
      pinSpacing: true,
    });
  }

  // Quick suggestions — alternate x settle
  if (prompts.length) {
    gsap.set(prompts, { opacity: 0, x: (i) => (i % 2 === 0 ? -16 : 16) });
    ScrollTrigger.batch(prompts, {
      start: 'top 90%',
      once: true,
      onEnter: (batch) => {
        gsap.to(batch, {
          opacity: 1,
          x: 0,
          duration: 0.45,
          stagger: 0.07,
          ease: 'power2.out',
          clearProps: 'transform',
        });
      },
    });
  }

  // Statute cards — batch + rail scaleY + cite follow
  if (cards.length) {
    gsap.set(cards, { opacity: 0, y: 36, rotateX: 8 });
    gsap.set('.home-card__rail', { scaleY: 0 });
    gsap.set('.home-card__cite', { opacity: 0, y: 10 });

    ScrollTrigger.batch(cards, {
      start: 'top 85%',
      once: true,
      onEnter: (batch) => {
        const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
        tl.to(batch, {
          opacity: 1,
          y: 0,
          rotateX: 0,
          duration: 0.55,
          stagger: 0.1,
          clearProps: 'transform',
        })
          .to(
            batch.map((c) => c.querySelector('.home-card__rail')).filter(Boolean),
            { scaleY: 1, duration: 0.4, stagger: 0.1 },
            '-=0.35',
          )
          .to(
            batch.map((c) => c.querySelector('.home-card__cite')).filter(Boolean),
            { opacity: 1, y: 0, duration: 0.35, stagger: 0.1 },
            '-=0.25',
          );
      },
    });

    setupCardTilt(cards);
  }

  // Corpus strip reveal
  if (corpus) {
    gsap.fromTo(
      corpus,
      { opacity: 0, y: 24, clipPath: 'inset(0 12% 0 0)' },
      {
        opacity: 1,
        y: 0,
        clipPath: 'inset(0 0% 0 0)',
        duration: 0.7,
        ease: 'power2.out',
        scrollTrigger: {
          trigger: corpus,
          start: 'top 88%',
          once: true,
        },
      },
    );
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initHomeMotion);
} else {
  initHomeMotion();
}
