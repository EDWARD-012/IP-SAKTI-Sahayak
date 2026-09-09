/**
 * IP-SAKTI Sahayak — 3D hero scene (self-hosted three.js, offline-safe)
 *
 * Renders behind the homepage hero:
 *  - A 3D Ashoka-Chakra-inspired wheel (torus ring + 24 spokes + hub)
 *  - A slow-drifting tricolor particle field (saffron / white / green)
 *  - Mouse parallax on desktop
 *
 * Graceful degradation:
 *  - No WebGL            → container stays empty, CSS fallback chakra shows
 *  - prefers-reduced-motion → renders a single static frame (no loop)
 *  - Tab hidden          → animation loop pauses
 */

import * as THREE from '/static/js/vendor/three.module.min.js';

const container = document.getElementById('hero3d');

function webglAvailable() {
  try {
    const c = document.createElement('canvas');
    return !!(window.WebGLRenderingContext &&
      (c.getContext('webgl2') || c.getContext('webgl')));
  } catch { return false; }
}

if (container && webglAvailable()) {
  init(container);
  container.closest('.gov-hero')?.classList.add('hero3d-active');
}

function init(el) {
  const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
  camera.position.set(0, 0, 14);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  el.appendChild(renderer.domElement);

  // ── Lights ──
  scene.add(new THREE.AmbientLight(0xbfd4ff, 0.7));
  const key = new THREE.DirectionalLight(0xffffff, 1.6);
  key.position.set(4, 6, 8);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0xff9933, 0.8);   // saffron rim light
  rim.position.set(-6, -3, -4);
  scene.add(rim);

  // ── Chakra wheel group ──
  const wheel = new THREE.Group();

  const ringMat = new THREE.MeshStandardMaterial({
    color: 0xe8f0f9, metalness: 0.55, roughness: 0.3,
  });
  const spokeMat = new THREE.MeshStandardMaterial({
    color: 0xdbe7f5, metalness: 0.45, roughness: 0.4,
  });

  // Outer rim
  wheel.add(new THREE.Mesh(new THREE.TorusGeometry(4.4, 0.16, 24, 96), ringMat));
  // Inner rim
  wheel.add(new THREE.Mesh(new THREE.TorusGeometry(3.4, 0.07, 16, 96), ringMat));
  // Hub
  wheel.add(new THREE.Mesh(new THREE.SphereGeometry(0.42, 24, 24), ringMat));

  // 24 spokes
  const spokeGeo = new THREE.CylinderGeometry(0.05, 0.05, 3.0, 8);
  for (let i = 0; i < 24; i++) {
    const spoke = new THREE.Mesh(spokeGeo, spokeMat);
    const angle = (i / 24) * Math.PI * 2;
    spoke.position.set(Math.cos(angle) * 1.9, Math.sin(angle) * 1.9, 0);
    spoke.rotation.z = angle + Math.PI / 2;
    wheel.add(spoke);
  }

  wheel.position.x = 3.2;           // sits on the right side of the hero
  wheel.rotation.y = -0.35;
  scene.add(wheel);

  // ── Tricolor particle field ──
  const COLORS = [0xff9933, 0xffffff, 0x2e8b57];  // saffron, white, sea-green
  const particleGroups = COLORS.map((color) => {
    const count = 160;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      positions[i * 3]     = (Math.random() - 0.5) * 30;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 16;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 12 - 2;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({
      color, size: 0.06, transparent: true, opacity: 0.75,
      sizeAttenuation: true, depthWrite: false,
    });
    const points = new THREE.Points(geo, mat);
    scene.add(points);
    return points;
  });

  // ── Mouse parallax ──
  let targetRX = 0, targetRY = 0;
  if (!reduced) {
    el.closest('.gov-hero')?.addEventListener('mousemove', (e) => {
      const rect = el.getBoundingClientRect();
      const nx = (e.clientX - rect.left) / rect.width - 0.5;
      const ny = (e.clientY - rect.top) / rect.height - 0.5;
      targetRY = nx * 0.35;
      targetRX = ny * 0.25;
    });
  }

  // ── Resize ──
  function resize() {
    const w = el.clientWidth || 1;
    const h = el.clientHeight || 1;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  resize();
  new ResizeObserver(resize).observe(el);

  // ── Animation loop ──
  let running = !reduced;
  let rafId = 0;
  const clock = new THREE.Clock();

  function frame() {
    const t = clock.getElapsedTime();

    wheel.rotation.z = t * 0.15;                              // slow dharma-wheel spin
    wheel.rotation.y += (targetRY - 0.35 - wheel.rotation.y) * 0.04;
    wheel.rotation.x += (targetRX - wheel.rotation.x) * 0.04;
    wheel.position.y = Math.sin(t * 0.5) * 0.25;              // gentle float

    particleGroups.forEach((p, i) => {
      p.rotation.y = t * 0.015 * (i + 1);
      p.position.y = Math.sin(t * 0.2 + i * 2) * 0.4;
    });

    renderer.render(scene, camera);
    if (running) rafId = requestAnimationFrame(frame);
  }

  document.addEventListener('visibilitychange', () => {
    if (reduced) return;
    if (document.hidden) {
      running = false;
      cancelAnimationFrame(rafId);
    } else if (!running) {
      running = true;
      clock.getDelta();
      rafId = requestAnimationFrame(frame);
    }
  });

  frame();  // reduced-motion: single static frame; otherwise starts the loop
}
