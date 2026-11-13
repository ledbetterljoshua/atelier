(() => {
  const root = document.documentElement;

  // Light and dark. The choice is remembered; until one is made the system decides.
  const mq = matchMedia('(prefers-color-scheme:dark)');
  const stored = () => { try { return localStorage.getItem('atelier-theme'); } catch (e) { return null; } };
  mq.addEventListener('change', () => { if (!stored()) root.dataset.theme = mq.matches ? 'dark' : 'light'; });
  document.querySelector('.theme')?.addEventListener('click', () => {
    const t = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = t;
    try { localStorage.setItem('atelier-theme', t); } catch (e) {}
  });

  // Opened from disk there is no server to turn a directory into its index.html.
  if (location.protocol === 'file:') {
    document.querySelectorAll('a[href]').forEach(a => {
      const h = a.getAttribute('href');
      if (/^(https?:|#|mailto:)/.test(h)) return;
      const [path, hash] = h.split('#');
      if (path === '' || path.endsWith('/')) a.setAttribute('href', path + 'index.html' + (hash ? '#' + hash : ''));
    });
  }

  const data = document.getElementById('work');
  if (!data) return;
  const work = JSON.parse(data.textContent);
  const stages = work.stages, last = stages.length - 1;
  const base = document.querySelector('.canvas .base'), over = document.querySelector('.canvas .over');
  const now = document.querySelector('.hung .now'), buttons = [...document.querySelectorAll('.stages button')];
  const play = document.querySelector('.play');
  const fmt = n => n.toLocaleString('en-GB');
  let cur = last, timer = null, warmed = false, token = 0;

  const warm = () => { if (warmed) return; warmed = true; stages.forEach(s => { new Image().src = s.file; }); };
  const caption = i => i === last ? (work.marks ? `Finished · ${fmt(stages[i].strokes)} ${work.marks}` : 'Finished') : `Stage ${i + 1} of ${stages.length}: ${stages[i].name}`;

  function show(i, quick) {
    i = Math.max(0, Math.min(last, i));
    if (i === cur) return;
    cur = i;
    buttons.forEach((b, j) => j === i ? b.setAttribute('aria-current', 'true') : b.removeAttribute('aria-current'));
    now.textContent = caption(i);
    const mine = ++token, src = stages[i].file, img = new Image();
    img.onload = () => {
      if (mine !== token) return;
      if (quick) { base.removeAttribute('srcset'); base.src = src; over.classList.remove('on'); return; }
      over.hidden = false; over.src = src; over.classList.remove('on');
      void over.offsetWidth;
      over.classList.add('on');
      setTimeout(() => { if (mine !== token) return; base.removeAttribute('srcset'); base.src = src; }, 460);
    };
    img.src = src;
  }

  function stop() { clearInterval(timer); timer = null; play.textContent = 'Play'; play.setAttribute('aria-pressed', 'false'); }
  play.addEventListener('click', () => {
    if (timer) return stop();
    warm();
    play.textContent = 'Pause'; play.setAttribute('aria-pressed', 'true');
    show(0, true); cur = 0;
    buttons[0].setAttribute('aria-current', 'true');
    timer = setInterval(() => { if (cur >= last) return stop(); show(cur + 1); }, 1500);
  });
  buttons.forEach((b, i) => {
    b.addEventListener('click', () => { stop(); warm(); show(i); });
    b.addEventListener('pointerenter', warm, { once: true });
  });
  document.querySelector('.making').addEventListener('touchstart', warm, { once: true, passive: true });

  // Close view: the full board, pan and zoom.
  const dlg = document.querySelector('.viewer'), vp = dlg.querySelector('.v-stage'), vimg = vp.querySelector('img');
  const pct = dlg.querySelector('.v-pct'), vname = dlg.querySelector('.v-stage-name');
  const W = work.w, H = work.h;
  let s = 1, x = 0, y = 0, fit = 1, max = 3, raf = 0;
  vimg.width = W; vimg.height = H; vimg.style.width = W + 'px'; vimg.style.height = H + 'px';

  const measure = () => {
    const r = vp.getBoundingClientRect();
    fit = Math.min(r.width / W, (r.height - 64) / H);
    max = Math.max(3, fit * 4);
    return r;
  };
  function paint() {
    const r = vp.getBoundingClientRect(), w = W * s, h = H * s;
    x = w <= r.width ? (r.width - w) / 2 : Math.min(0, Math.max(r.width - w, x));
    const room = r.height - 64;
    y = h <= room ? (room - h) / 2 : Math.min(0, Math.max(r.height - 64 - h, y));
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => { vimg.style.transform = `translate3d(${x}px,${y}px,0) scale(${s})`; });
    pct.textContent = Math.abs(s - fit) < 1e-3 ? 'Fit' : Math.round(s * 100) + '%';
    vimg.style.imageRendering = s > 2.5 ? 'pixelated' : '';
  }
  function zoomTo(ns, cx, cy) {
    const r = vp.getBoundingClientRect();
    if (cx == null) { cx = r.width / 2; cy = r.height / 2; }
    ns = Math.max(fit, Math.min(max, ns));
    x = cx - (cx - x) * ns / s; y = cy - (cy - y) * ns / s; s = ns;
    paint();
  }
  function open(e) {
    e?.preventDefault();
    stop();
    if (!dlg.showModal) { location.href = work.full; return; }
    vname.textContent = cur === last ? '' : `Stage ${cur + 1} of ${stages.length}: ${stages[cur].name}`;
    vimg.src = stages[cur].file;
    dlg.showModal();
    measure(); s = fit; x = y = 0; paint();
    if (cur === last) {
      const full = new Image();
      full.onload = () => { if (dlg.open && cur === last) vimg.src = work.full; };
      full.src = work.full;
    }
  }
  document.querySelector('.canvas').addEventListener('click', open);
  document.querySelector('.zoom').addEventListener('click', open);
  dlg.addEventListener('click', e => {
    const z = e.target.closest('[data-z]')?.dataset.z;
    if (z === 'close') dlg.close();
    else if (z === 'in') zoomTo(s * 1.6);
    else if (z === 'out') zoomTo(s / 1.6);
    else if (z === 'fit') zoomTo(Math.abs(s - fit) < 1e-3 ? Math.max(1, fit * 2.5) : fit);
  });
  addEventListener('resize', () => { if (dlg.open) { const was = Math.abs(s - fit) < 1e-3; measure(); if (was || s < fit) s = fit; paint(); } });
  vp.addEventListener('wheel', e => {
    e.preventDefault();
    const r = vp.getBoundingClientRect();
    if (e.ctrlKey || Math.abs(e.deltaY) >= 40 || s === fit && !e.deltaX) zoomTo(s * Math.exp(-e.deltaY * (e.ctrlKey ? 0.012 : 0.0022)), e.clientX - r.left, e.clientY - r.top);
    else { x -= e.deltaX; y -= e.deltaY; paint(); }
  }, { passive: false });

  const pts = new Map();
  let pinch = 0, moved = 0, tapAt = 0, tapX = 0, tapY = 0;
  vp.addEventListener('pointerdown', e => {
    vp.setPointerCapture(e.pointerId);
    pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
    moved = 0; vp.classList.add('drag');
    if (pts.size === 2) { const [a, b] = [...pts.values()]; pinch = Math.hypot(a.x - b.x, a.y - b.y); }
  });
  vp.addEventListener('pointermove', e => {
    const p = pts.get(e.pointerId);
    if (!p) return;
    const dx = e.clientX - p.x, dy = e.clientY - p.y;
    p.x = e.clientX; p.y = e.clientY; moved += Math.abs(dx) + Math.abs(dy);
    if (pts.size === 1) { x += dx; y += dy; paint(); }
    else if (pts.size === 2) {
      const [a, b] = [...pts.values()], d = Math.hypot(a.x - b.x, a.y - b.y), r = vp.getBoundingClientRect();
      x += dx / 2; y += dy / 2;
      if (pinch) zoomTo(s * d / pinch, (a.x + b.x) / 2 - r.left, (a.y + b.y) / 2 - r.top);
      pinch = d;
    }
  });
  const up = e => {
    if (!pts.delete(e.pointerId)) return;
    if (pts.size < 2) pinch = 0;
    if (pts.size) return;
    vp.classList.remove('drag');
    if (moved > 8 || e.type === 'pointercancel') return;
    const t = performance.now(), r = vp.getBoundingClientRect();
    if (t - tapAt < 320 && Math.hypot(e.clientX - tapX, e.clientY - tapY) < 30) {
      zoomTo(s > fit * 1.05 ? fit : Math.max(1, fit * 2.5), e.clientX - r.left, e.clientY - r.top);
      tapAt = 0;
    } else { tapAt = t; tapX = e.clientX; tapY = e.clientY; }
  };
  vp.addEventListener('pointerup', up);
  vp.addEventListener('pointercancel', up);

  addEventListener('keydown', e => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (dlg.open) {
      const step = 80;
      if (e.key === '+' || e.key === '=') zoomTo(s * 1.4);
      else if (e.key === '-') zoomTo(s / 1.4);
      else if (e.key === '0') zoomTo(fit);
      else if (e.key === 'ArrowLeft') { x += step; paint(); }
      else if (e.key === 'ArrowRight') { x -= step; paint(); }
      else if (e.key === 'ArrowUp') { y += step; paint(); }
      else if (e.key === 'ArrowDown') { y -= step; paint(); }
      else return;
      e.preventDefault();
    } else if (!/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || '')) {
      if (e.key === 'ArrowLeft') { stop(); warm(); show(cur - 1); }
      else if (e.key === 'ArrowRight') { stop(); warm(); show(cur + 1); }
    }
  });
})();
