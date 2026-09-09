/**
 * IP-SAKTI — cinematic 3D scenes (self-hosted three.js, Iris Xe safe).
 *
 * Auto-inits every [data-scene3d] container:
 *   data-scene3d="hero"  → full-bleed gyroscope Chakra + starfield
 *   data-scene3d="chat"  → compact floating Chakra for the empty state
 *
 * No EffectComposer / bloom (too heavy for Intel Iris Xe). Depth comes from
 * MeshPhysicalMaterial, orbiting point lights, and opposite-spin gyro rings.
 */
import * as THREE from '/static/js/vendor/three.module.min.js';

function webglAvailable() {
  try {
    const c = document.createElement('canvas');
    return !!(window.WebGLRenderingContext &&
      (c.getContext('webgl2') || c.getContext('webgl')));
  } catch { return false; }
}

function reducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
}

function physical(color, extras = {}) {
  return new THREE.MeshPhysicalMaterial({
    color,
    metalness: extras.metalness ?? 0.85,
    roughness: extras.roughness ?? 0.22,
    clearcoat: extras.clearcoat ?? 0.6,
    clearcoatRoughness: 0.2,
    emissive: extras.emissive ?? 0x000000,
    emissiveIntensity: extras.emissiveIntensity ?? 0,
    transparent: extras.opacity != null,
    opacity: extras.opacity ?? 1,
  });
}

function buildChakra(scale = 1) {
  const g = new THREE.Group();

  const gold = physical(0xffb347, { metalness: 0.9, roughness: 0.18, emissive: 0x4a2200, emissiveIntensity: 0.15 });
  const silver = physical(0xdbe7f5, { metalness: 0.8, roughness: 0.25 });
  const navy = physical(0x1a4a8a, { metalness: 0.7, roughness: 0.3, emissive: 0x003087, emissiveIntensity: 0.25 });
  const green = physical(0x2e8b57, { metalness: 0.75, roughness: 0.28, emissive: 0x0a3d1a, emissiveIntensity: 0.2 });

  const outer = new THREE.Mesh(new THREE.TorusGeometry(4.6 * scale, 0.18 * scale, 20, 96), gold);
  const mid = new THREE.Mesh(new THREE.TorusGeometry(3.55 * scale, 0.08 * scale, 16, 80), silver);
  const hubRing = new THREE.Mesh(new THREE.TorusGeometry(0.55 * scale, 0.08 * scale, 12, 48), navy);
  const hub = new THREE.Mesh(new THREE.IcosahedronGeometry(0.42 * scale, 1), navy);
  g.add(outer, mid, hubRing, hub);

  const spokeGeo = new THREE.CylinderGeometry(0.045 * scale, 0.045 * scale, 3.15 * scale, 8);
  for (let i = 0; i < 24; i++) {
    const spoke = new THREE.Mesh(spokeGeo, i % 2 === 0 ? silver : gold);
    const a = (i / 24) * Math.PI * 2;
    spoke.position.set(Math.cos(a) * 1.95 * scale, Math.sin(a) * 1.95 * scale, 0);
    spoke.rotation.z = a + Math.PI / 2;
    g.add(spoke);
  }

  // Gyro rings (depth — the “3D” the previous scene lacked)
  const gyroA = new THREE.Mesh(
    new THREE.TorusGeometry(5.15 * scale, 0.035 * scale, 10, 80),
    physical(0xff9933, { metalness: 0.6, roughness: 0.35, opacity: 0.7 }),
  );
  gyroA.rotation.x = Math.PI / 2.4;
  const gyroB = new THREE.Mesh(
    new THREE.TorusGeometry(5.15 * scale, 0.035 * scale, 10, 80),
    green,
  );
  gyroB.rotation.y = Math.PI / 2.2;
  g.add(gyroA, gyroB);
  g.userData.gyroA = gyroA;
  g.userData.gyroB = gyroB;
  return g;
}

function starfield(count, spread) {
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const palette = [
    [1, 0.6, 0.2],
    [1, 1, 1],
    [0.18, 0.53, 0.32],
    [0.55, 0.72, 1],
  ];
  for (let i = 0; i < count; i++) {
    positions[i * 3]     = (Math.random() - 0.5) * spread[0];
    positions[i * 3 + 1] = (Math.random() - 0.5) * spread[1];
    positions[i * 3 + 2] = (Math.random() - 0.5) * spread[2];
    const c = palette[i % palette.length];
    colors[i * 3] = c[0]; colors[i * 3 + 1] = c[1]; colors[i * 3 + 2] = c[2];
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  const mat = new THREE.PointsMaterial({
    size: 0.055, vertexColors: true, transparent: true,
    opacity: 0.85, sizeAttenuation: true, depthWrite: false,
  });
  return new THREE.Points(geo, mat);
}

function initScene(el) {
  const mode = el.dataset.scene3d || 'hero';
  const isHero = mode === 'hero';
  const reduced = reducedMotion();

  const scene = new THREE.Scene();
  if (isHero) scene.fog = new THREE.FogExp2(0x001433, 0.028);

  const camera = new THREE.PerspectiveCamera(isHero ? 42 : 50, 1, 0.1, 80);
  camera.position.set(0, 0, isHero ? 13.5 : 11);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  el.appendChild(renderer.domElement);

  scene.add(new THREE.HemisphereLight(0x9ecbff, 0x0a1a10, 0.55));
  const key = new THREE.DirectionalLight(0xffffff, 1.8);
  key.position.set(5, 7, 9);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xff9933, 1.1);
  fill.position.set(-7, -2, 4);
  scene.add(fill);
  const hubLight = new THREE.PointLight(0xffc857, 2.4, 18);
  scene.add(hubLight);

  const scale = isHero ? 1.05 : 0.72;
  const wheel = buildChakra(scale);
  if (isHero) {
    wheel.position.set(3.6, 0.15, 0);
    wheel.rotation.y = -0.55;
    wheel.rotation.x = 0.18;
  }
  scene.add(wheel);

  const stars = starfield(isHero ? 520 : 180, isHero ? [36, 20, 16] : [16, 12, 10]);
  scene.add(stars);

  let targetRX = wheel.rotation.x;
  let targetRY = wheel.rotation.y;
  const host = el.closest('.gov-hero, .chat-empty-state, .site-main') || el;
  if (!reduced) {
    host.addEventListener('mousemove', (e) => {
      const rect = el.getBoundingClientRect();
      const nx = (e.clientX - rect.left) / Math.max(rect.width, 1) - 0.5;
      const ny = (e.clientY - rect.top) / Math.max(rect.height, 1) - 0.5;
      targetRY = (isHero ? -0.55 : 0) + nx * 0.55;
      targetRX = (isHero ? 0.18 : 0) + ny * 0.35;
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

  let running = !reduced;
  let rafId = 0;
  const clock = new THREE.Clock();

  function frame() {
    const t = clock.getElapsedTime();
    wheel.rotation.z = t * 0.12;
    wheel.rotation.y += (targetRY - wheel.rotation.y) * 0.045;
    wheel.rotation.x += (targetRX - wheel.rotation.x) * 0.045;
    wheel.position.y = (isHero ? 0.15 : 0) + Math.sin(t * 0.55) * 0.28;
    if (wheel.userData.gyroA) wheel.userData.gyroA.rotation.z = t * 0.35;
    if (wheel.userData.gyroB) wheel.userData.gyroB.rotation.x = t * -0.28;
    hubLight.position.copy(wheel.position);
    hubLight.intensity = 2.1 + Math.sin(t * 2.2) * 0.5;
    stars.rotation.y = t * 0.012;
    stars.rotation.x = Math.sin(t * 0.08) * 0.04;
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

  frame();
  el.closest('.gov-hero')?.classList.add('hero3d-active');
}

if (webglAvailable()) {
  document.querySelectorAll('[data-scene3d]').forEach(initScene);
}
