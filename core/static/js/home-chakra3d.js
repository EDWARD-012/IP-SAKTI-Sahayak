/**
 * IP-SAKTI — live 3D Ashoka Chakra for the light editorial home hero.
 * Self-hosted three.js. Scroll + cursor drive orientation; idle spin.
 * Falls back to SVG if WebGL is unavailable.
 */
import * as THREE from '/static/js/vendor/three.module.min.js';

const state = {
  scrollSpin: 0, // extra Z from page scroll (radians)
  scrollTip: 0, // tip toward viewer
  cursorNX: 0,
  cursorNY: 0,
};

/** @type {typeof state} */
window.__ipSaktiChakra = state;

function webglOk() {
  try {
    const c = document.createElement('canvas');
    return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl')));
  } catch {
    return false;
  }
}

function reduced() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
}

function navyMat(extras = {}) {
  return new THREE.MeshPhysicalMaterial({
    color: extras.color ?? 0x003087,
    metalness: extras.metalness ?? 0.55,
    roughness: extras.roughness ?? 0.28,
    clearcoat: 0.85,
    clearcoatRoughness: 0.18,
    emissive: extras.emissive ?? 0x001433,
    emissiveIntensity: extras.emissiveIntensity ?? 0.12,
  });
}

function buildAshoka(scale = 1) {
  const g = new THREE.Group();
  const navy = navyMat();
  const deep = navyMat({ color: 0x001a4d, metalness: 0.65, roughness: 0.22 });
  const rim = navyMat({
    color: 0x1a4a8a,
    emissive: 0xff9933,
    emissiveIntensity: 0.08,
    metalness: 0.4,
    roughness: 0.35,
  });
  const hubMat = navyMat({ color: 0x002466, metalness: 0.7, roughness: 0.2, emissiveIntensity: 0.2 });

  // Outer rim (torus) + face disc for “seal” thickness
  const outer = new THREE.Mesh(new THREE.TorusGeometry(4.4 * scale, 0.22 * scale, 24, 96), navy);
  const face = new THREE.Mesh(
    new THREE.CylinderGeometry(4.15 * scale, 4.15 * scale, 0.12 * scale, 64),
    deep,
  );
  face.rotation.x = Math.PI / 2;
  const inner = new THREE.Mesh(new THREE.TorusGeometry(1.05 * scale, 0.1 * scale, 16, 64), rim);
  const hub = new THREE.Mesh(new THREE.SphereGeometry(0.55 * scale, 32, 24), hubMat);
  g.add(outer, face, inner, hub);

  // 24 spokes
  const spokeGeo = new THREE.BoxGeometry(0.1 * scale, 3.0 * scale, 0.14 * scale);
  for (let i = 0; i < 24; i++) {
    const spoke = new THREE.Mesh(spokeGeo, i % 2 === 0 ? navy : rim);
    const a = (i / 24) * Math.PI * 2;
    spoke.position.set(Math.cos(a) * 2.55 * scale, Math.sin(a) * 2.55 * scale, 0.02 * scale);
    spoke.rotation.z = a + Math.PI / 2;
    g.add(spoke);

    // Edge knobs on outer rim (Ashoka detail)
    const knob = new THREE.Mesh(
      new THREE.SphereGeometry(0.12 * scale, 12, 10),
      rim,
    );
    knob.position.set(Math.cos(a) * 4.4 * scale, Math.sin(a) * 4.4 * scale, 0);
    g.add(knob);
  }

  // Thin gyro rings for depth (subtle, institutional saffron/green)
  const gyroS = new THREE.Mesh(
    new THREE.TorusGeometry(4.95 * scale, 0.03 * scale, 10, 80),
    navyMat({ color: 0xff9933, metalness: 0.3, roughness: 0.45, emissive: 0xff9933, emissiveIntensity: 0.15 }),
  );
  gyroS.rotation.x = Math.PI / 2.5;
  const gyroG = new THREE.Mesh(
    new THREE.TorusGeometry(4.95 * scale, 0.03 * scale, 10, 80),
    navyMat({ color: 0x138808, metalness: 0.35, roughness: 0.4, emissive: 0x138808, emissiveIntensity: 0.12 }),
  );
  gyroG.rotation.y = Math.PI / 2.3;
  g.add(gyroS, gyroG);
  g.userData.gyroS = gyroS;
  g.userData.gyroG = gyroG;
  return g;
}

function init(el) {
  const reduce = reduced();
  const fallback = el.querySelector('.home-chakra__fallback');

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 60);
  camera.position.set(0, 0.2, 12.5);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  el.appendChild(renderer.domElement);
  el.classList.add('home-chakra--live');
  if (fallback) fallback.hidden = true;

  // Soft studio lighting for light page
  scene.add(new THREE.HemisphereLight(0xffffff, 0xd8e4d4, 0.85));
  const key = new THREE.DirectionalLight(0xffffff, 1.35);
  key.position.set(4, 6, 8);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xffe0b8, 0.55);
  fill.position.set(-5, -1, 3);
  scene.add(fill);

  const cursorLight = new THREE.PointLight(0xffb347, 1.4, 22);
  cursorLight.position.set(2, 2, 6);
  scene.add(cursorLight);

  // Soft ground shadow disc
  const shadow = new THREE.Mesh(
    new THREE.CircleGeometry(4.2, 48),
    new THREE.MeshBasicMaterial({ color: 0x003087, transparent: true, opacity: 0.08 }),
  );
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.y = -4.6;
  scene.add(shadow);

  const wheel = buildAshoka(1.0);
  wheel.rotation.x = 0.22;
  wheel.rotation.y = -0.35;
  scene.add(wheel);

  let targetRX = wheel.rotation.x;
  let targetRY = wheel.rotation.y;
  const host = el.closest('.home-hero') || el;

  if (!reduce) {
    host.addEventListener('pointermove', (e) => {
      const rect = el.getBoundingClientRect();
      const nx = (e.clientX - rect.left) / Math.max(rect.width, 1) - 0.5;
      const ny = (e.clientY - rect.top) / Math.max(rect.height, 1) - 0.5;
      state.cursorNX = nx;
      state.cursorNY = ny;
      targetRY = -0.35 + nx * 0.85;
      targetRX = 0.22 + ny * 0.55;
      cursorLight.position.x = nx * 6;
      cursorLight.position.y = -ny * 4 + 1;
      cursorLight.intensity = 1.2 + Math.abs(nx) * 0.8;
    });
    host.addEventListener('pointerleave', () => {
      targetRY = -0.35 + state.scrollTip * 0.15;
      targetRX = 0.22;
    });
  }

  function resize() {
    const w = el.clientWidth || 1;
    const h = el.clientHeight || 1;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  resize();
  if (typeof ResizeObserver !== 'undefined') new ResizeObserver(resize).observe(el);

  let running = true;
  let raf = 0;
  const clock = new THREE.Clock();

  function frame() {
    const t = clock.getElapsedTime();
    const idle = reduce ? 0 : t * 0.18;
    const spin = idle + state.scrollSpin;

    wheel.rotation.z = spin;
    wheel.rotation.y += (targetRY + state.scrollTip * 0.25 - wheel.rotation.y) * 0.06;
    wheel.rotation.x += (targetRX + state.scrollTip * 0.35 - wheel.rotation.x) * 0.06;
    wheel.position.y = Math.sin(t * 0.7) * 0.18;
    wheel.position.z = state.scrollTip * 0.6;

    if (wheel.userData.gyroS) wheel.userData.gyroS.rotation.z = t * 0.4;
    if (wheel.userData.gyroG) wheel.userData.gyroG.rotation.x = t * -0.32;

    shadow.scale.setScalar(1 + Math.sin(t * 0.7) * 0.04);
    shadow.material.opacity = 0.07 + Math.abs(state.cursorNX) * 0.04;

    renderer.render(scene, camera);
    if (running) raf = requestAnimationFrame(frame);
  }

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      running = false;
      cancelAnimationFrame(raf);
    } else if (!running) {
      running = true;
      clock.getDelta();
      raf = requestAnimationFrame(frame);
    }
  });

  if (reduce) {
    renderer.render(scene, camera);
  } else {
    frame();
  }
}

const mount = document.getElementById('home-chakra3d');
if (mount && webglOk()) {
  init(mount);
} else if (mount) {
  mount.classList.add('home-chakra--fallback');
}
