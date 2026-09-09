/**
 * IP-SAKTI — 3D corpus shelf (rectangular statute slabs).
 * No circles. Cursor parallax + scroll fans the stack open.
 */
import * as THREE from '/static/js/vendor/three.module.min.js';

const state = {
  scrollOpen: 0, // 0 stacked → 1 fanned
  cursorNX: 0,
  cursorNY: 0,
};
window.__ipSaktiCorpus3d = state;

const ACTS = [
  { title: 'Patents Act', year: '1970', color: 0x003087 },
  { title: 'GI Act', year: '1999', color: 0x1a4a8a },
  { title: 'Biodiversity', year: '2002', color: 0x0d5c2e },
  { title: 'Drugs & Cosmetics', year: '1940', color: 0xb45309 },
  { title: 'Ayurveda Aahara', year: '2022', color: 0x138808 },
  { title: 'Nagoya / TRIPS', year: 'Treaty', color: 0x7c2d12 },
];

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

function makeLabelTexture(title, year, baseColor) {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 288;
  const ctx = canvas.getContext('2d');
  const r = (baseColor >> 16) & 255;
  const g = (baseColor >> 8) & 255;
  const b = baseColor & 255;
  ctx.fillStyle = `rgb(${r},${g},${b})`;
  ctx.fillRect(0, 0, 512, 288);
  // tricolor hairline
  ctx.fillStyle = '#ff9933';
  ctx.fillRect(0, 0, 512, 8);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 8, 512, 6);
  ctx.fillStyle = '#138808';
  ctx.fillRect(0, 14, 512, 8);
  ctx.fillStyle = 'rgba(255,255,255,0.92)';
  ctx.font = 'bold 42px system-ui,Segoe UI,sans-serif';
  ctx.fillText(title, 36, 120);
  ctx.font = '600 28px system-ui,Segoe UI,sans-serif';
  ctx.fillStyle = 'rgba(255,255,255,0.7)';
  ctx.fillText(year, 36, 170);
  ctx.font = '600 18px system-ui,Segoe UI,sans-serif';
  ctx.fillStyle = 'rgba(255,255,255,0.45)';
  ctx.fillText('IP-SAKTI corpus', 36, 240);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function buildSlab(act, i) {
  const group = new THREE.Group();
  const w = 3.6;
  const h = 2.05;
  const d = 0.08;
  const geo = new THREE.BoxGeometry(w, h, d);
  const front = new THREE.MeshStandardMaterial({
    map: makeLabelTexture(act.title, act.year, act.color),
    roughness: 0.45,
    metalness: 0.15,
  });
  const side = new THREE.MeshStandardMaterial({
    color: act.color,
    roughness: 0.5,
    metalness: 0.2,
  });
  const mesh = new THREE.Mesh(geo, [side, side, side, side, front, side]);
  group.add(mesh);
  group.userData.index = i;
  return group;
}

function init(el) {
  const reduce = reduced();
  const fallback = el.querySelector('.home-shelf__fallback');

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 80);
  camera.position.set(0, 0.4, 11);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  el.appendChild(renderer.domElement);
  el.classList.add('home-shelf--live');
  if (fallback) fallback.hidden = true;

  scene.add(new THREE.HemisphereLight(0xffffff, 0xc5d4c8, 0.9));
  const key = new THREE.DirectionalLight(0xffffff, 1.25);
  key.position.set(5, 8, 6);
  scene.add(key);
  const cursorLight = new THREE.PointLight(0xffb347, 1.1, 24);
  cursorLight.position.set(2, 2, 5);
  scene.add(cursorLight);

  const root = new THREE.Group();
  root.rotation.y = -0.35;
  root.rotation.x = 0.18;
  scene.add(root);

  const slabs = ACTS.map((act, i) => {
    const s = buildSlab(act, i);
    root.add(s);
    return s;
  });

  // Angular accent planes (not circles)
  const accentGeo = new THREE.PlaneGeometry(8, 0.08);
  const saffron = new THREE.Mesh(
    accentGeo,
    new THREE.MeshBasicMaterial({ color: 0xff9933, transparent: true, opacity: 0.55 }),
  );
  saffron.position.set(0, -3.2, -1);
  saffron.rotation.z = -0.12;
  root.add(saffron);
  const green = new THREE.Mesh(
    accentGeo,
    new THREE.MeshBasicMaterial({ color: 0x138808, transparent: true, opacity: 0.45 }),
  );
  green.position.set(0.4, -3.45, -1.1);
  green.rotation.z = 0.08;
  root.add(green);

  let targetRX = root.rotation.x;
  let targetRY = root.rotation.y;
  const host = el.closest('.home-hero') || el;

  if (!reduce) {
    host.addEventListener('pointermove', (e) => {
      const rect = el.getBoundingClientRect();
      const nx = (e.clientX - rect.left) / Math.max(rect.width, 1) - 0.5;
      const ny = (e.clientY - rect.top) / Math.max(rect.height, 1) - 0.5;
      state.cursorNX = nx;
      state.cursorNY = ny;
      targetRY = -0.35 + nx * 0.7;
      targetRX = 0.18 + ny * 0.45;
      cursorLight.position.set(nx * 7, -ny * 4 + 2, 5);
      cursorLight.intensity = 1.0 + Math.abs(nx) * 0.9;
    });
    host.addEventListener('pointerleave', () => {
      targetRY = -0.35;
      targetRX = 0.18;
    });
  }

  function layoutSlabs(open, t) {
    const n = slabs.length;
    slabs.forEach((s, i) => {
      const mid = (n - 1) / 2;
      const k = i - mid;
      // stacked → fanned diagonal shelf
      const x = k * (0.15 + open * 0.95);
      const y = -k * (0.12 + open * 0.55) + Math.sin(t * 0.8 + i) * 0.04 * (1 - open * 0.5);
      const z = -i * (0.12 + open * 0.35);
      const rotY = k * open * 0.18;
      const rotZ = k * open * -0.04;
      s.position.set(x, y, z);
      s.rotation.set(0.05 * open, rotY, rotZ);
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
    const open = reduce ? 0.55 : state.scrollOpen;

    root.rotation.y += (targetRY - root.rotation.y) * 0.06;
    root.rotation.x += (targetRX - root.rotation.x) * 0.06;
    root.position.y = Math.sin(t * 0.55) * 0.12;

    layoutSlabs(open, t);
    saffron.position.x = Math.sin(t * 0.3) * 0.15;
    green.position.x = 0.4 + Math.cos(t * 0.25) * 0.12;

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

  layoutSlabs(reduce ? 0.55 : 0, 0);
  if (reduce) renderer.render(scene, camera);
  else frame();
}

const mount = document.getElementById('home-corpus3d');
if (mount && webglOk()) init(mount);
else if (mount) mount.classList.add('home-shelf--fallback');
