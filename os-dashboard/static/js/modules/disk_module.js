/* ── ENHANCED DISK MODULE ── */
const DiskModule = {
  _presets: [],
  _liveRequests: [],
  _raceInterval: null,
  _raceStep: 0,
  _raceData: null,
  _heatmap: new Array(200).fill(0),

  init() {
    this.loadPresets();
    this.bindEvents();
    this.renderHeatmap();
  },

  bindEvents() {
    document.getElementById('disk-run')?.addEventListener('click', () => this.runSchedule());
    document.getElementById('disk-compare')?.addEventListener('click', () => this.runCompare());
    document.getElementById('disk-race')?.addEventListener('click', () => this.runRace());
    document.getElementById('disk-recommend')?.addEventListener('click', () => this.runRecommend());
    document.getElementById('disk-preset-select')?.addEventListener('change', e => this.applyPreset(e.target.value));
    document.getElementById('disk-gen-random')?.addEventListener('click', () => this.generateWorkload('random'));
    document.getElementById('disk-gen-sequential')?.addEventListener('click', () => this.generateWorkload('sequential'));
    document.getElementById('disk-gen-clustered')?.addEventListener('click', () => this.generateWorkload('clustered'));
    document.getElementById('disk-gen-heavy')?.addEventListener('click', () => this.generateWorkload('heavy'));
    document.getElementById('disk-gen-scatter')?.addEventListener('click', () => this.generateWorkload('scatter'));
    document.getElementById('disk-add-live')?.addEventListener('click', () => this.addLiveRequest());
    document.getElementById('disk-priority-run')?.addEventListener('click', () => this.runPriority());
    document.getElementById('disk-algo-select')?.addEventListener('change', e => {
      const dirWrap = document.getElementById('direction-wrap');
      const nWrap = document.getElementById('nstep-wrap');
      if (dirWrap) dirWrap.style.display = ['scan','look'].includes(e.target.value) ? 'flex' : 'none';
      if (nWrap) nWrap.style.display = e.target.value === 'nstep' ? 'flex' : 'none';
    });
  },

  async loadPresets() {
    try {
      const res = await API.process.diskPresets();
      if (res.status !== 'ok') return;
      this._presets = res.data;
      const sel = document.getElementById('disk-preset-select');
      if (!sel) return;
      sel.innerHTML = '<option value="">-- Load Preset --</option>';
      res.data.forEach((p, i) => {
        const o = document.createElement('option');
        o.value = i; o.textContent = p.name; sel.appendChild(o);
      });
    } catch(e) { console.warn(e); }
  },

  applyPreset(idx) {
    if (idx === '') return;
    const p = this._presets[parseInt(idx)];
    if (!p) return;
    document.getElementById('disk-requests').value = p.requests.join(', ');
    document.getElementById('disk-head').value = p.head;
    document.getElementById('disk-size').value = p.disk_size;
    this.updateHeatmap(p.requests);
    Toast.show(`Loaded: ${p.name}`, 'info');
  },

  async generateWorkload(pattern) {
    const diskSize = parseInt(document.getElementById('disk-size')?.value) || 200;
    try {
      const res = await API.post('/api/disk/generate', { pattern, count: 12, disk_size: diskSize });
      if (res.status === 'ok') {
        document.getElementById('disk-requests').value = res.data.requests.join(', ');
        document.getElementById('disk-head').value = res.data.head;
        this.updateHeatmap(res.data.requests);
        Toast.show(`Generated ${pattern} workload`, 'info');
      }
    } catch(e) { Toast.show(e.message, 'error'); }
  },

  gatherInput() {
    const reqStr = document.getElementById('disk-requests')?.value || '';
    const requests = reqStr.split(/[\s,]+/).map(Number).filter(n => !isNaN(n) && n >= 0);
    return {
      requests,
      head: parseInt(document.getElementById('disk-head')?.value) || 50,
      algorithm: document.getElementById('disk-algo-select')?.value || 'fcfs',
      disk_size: parseInt(document.getElementById('disk-size')?.value) || 200,
      direction: document.getElementById('disk-direction')?.value || 'right',
      n_step: parseInt(document.getElementById('disk-nstep')?.value) || 4,
    };
  },

  async runSchedule() {
    const body = this.gatherInput();
    if (!body.requests.length) { Toast.show('Enter disk requests', 'error'); return; }
    this.setBtnLoading('disk-run', true);
    try {
      const res = await API.post('/api/disk/schedule', body);
      this.renderResults(res.data, body.disk_size);
      this.updateHeatmap(body.requests);
      document.getElementById('disk-results-section')?.classList.remove('hidden');
      Toast.show('Simulation complete', 'success');
    } catch(e) { Toast.show(e.message, 'error'); }
    finally { this.setBtnLoading('disk-run', false); }
  },

  async runCompare() {
    const body = this.gatherInput();
    if (!body.requests.length) { Toast.show('Enter disk requests', 'error'); return; }
    this.setBtnLoading('disk-compare', true);
    try {
      const res = await API.post('/api/disk/compare', body);
      this.renderCompare(res.data, res.analysis);
      document.getElementById('disk-compare-section')?.classList.remove('hidden');
      Toast.show('Comparison complete', 'success');
    } catch(e) { Toast.show(e.message, 'error'); }
    finally { this.setBtnLoading('disk-compare', false); }
  },

  async runRace() {
    const body = this.gatherInput();
    if (!body.requests.length) { Toast.show('Enter disk requests', 'error'); return; }
    this.setBtnLoading('disk-race', true);
    try {
      const res = await API.post('/api/disk/race', body);
      this._raceData = res;
      this.renderRace(res.data, res.ranking, res.analysis);
      document.getElementById('disk-race-section')?.classList.remove('hidden');
      Toast.show('Race mode complete!', 'success');
    } catch(e) { Toast.show(e.message, 'error'); }
    finally { this.setBtnLoading('disk-race', false); }
  },

  async runRecommend() {
    const body = this.gatherInput();
    if (!body.requests.length) { Toast.show('Enter disk requests', 'error'); return; }
    try {
      const res = await API.post('/api/disk/recommend', body);
      this.renderRecommendation(res.data);
      document.getElementById('disk-rec-section')?.classList.remove('hidden');
    } catch(e) { Toast.show(e.message, 'error'); }
  },

  async runPriority() {
    const rows = document.querySelectorAll('#disk-priority-tbody tr');
    if (!rows.length) { Toast.show('Add priority requests', 'error'); return; }
    const requests = Array.from(rows).map(r => ({
      track: parseInt(r.querySelector('.pri-track')?.value) || 0,
      priority: parseInt(r.querySelector('.pri-level')?.value) || 1,
      deadline: parseFloat(r.querySelector('.pri-deadline')?.value) || 99,
    }));
    const head = parseInt(document.getElementById('disk-head')?.value) || 50;
    const mode = document.getElementById('disk-priority-mode')?.value || 'priority';
    try {
      const res = await API.post('/api/disk/priority', { requests, head, mode });
      this.renderResults(res.data, parseInt(document.getElementById('disk-size')?.value) || 200);
      document.getElementById('disk-results-section')?.classList.remove('hidden');
      Toast.show(`${mode === 'deadline' ? 'EDF' : 'Priority'} scheduling done`, 'success');
    } catch(e) { Toast.show(e.message, 'error'); }
  },

  addLiveRequest() {
    const track = parseInt(document.getElementById('disk-live-track')?.value);
    const diskSize = parseInt(document.getElementById('disk-size')?.value) || 200;
    if (isNaN(track) || track < 0 || track >= diskSize) {
      Toast.show('Invalid track number', 'error'); return;
    }
    this._liveRequests.push(track);
    const existing = document.getElementById('disk-requests')?.value || '';
    const all = existing ? existing + ', ' + track : String(track);
    document.getElementById('disk-requests').value = all;
    this.updateHeatmap([track]);
    this.renderLiveTag(track);
    Toast.show(`Added track ${track} to queue`, 'success');
  },

  renderLiveTag(track) {
    const el = document.getElementById('live-queue-tags');
    if (!el) return;
    const tag = document.createElement('span');
    tag.className = 'live-tag';
    tag.textContent = track;
    el.appendChild(tag);
  },

  // ── Results ──────────────────────────────────────────────────────────────
  renderResults(data, diskSize = 200) {
    document.getElementById('disk-total-seek').textContent = data.total_seek ?? '—';
    document.getElementById('disk-avg-seek').textContent = data.avg_seek ?? '—';
    document.getElementById('disk-algo-name').textContent = data.algorithm ?? '—';
    document.getElementById('disk-max-seek').textContent = data.max_seek ?? '—';
    document.getElementById('disk-variance').textContent = data.seek_variance ?? '—';
    document.getElementById('disk-fairness').textContent = data.fairness_index ?? '—';
    document.getElementById('disk-time-ms').textContent = data.total_time_ms ? data.total_time_ms + ' ms' : '—';

    // Starvation warnings
    const sw = document.getElementById('disk-starvation-warn');
    if (sw) {
      const warns = data.starvation_warnings || [];
      sw.innerHTML = warns.length
        ? warns.map(w => `<div class="starvation-alert">⚠ Track <b>${w.track}</b> waited ${w.wait_steps} steps — starvation risk!</div>`).join('')
        : '';
      sw.style.display = warns.length ? 'block' : 'none';
    }

    // Seek sequence
    const seqEl = document.getElementById('disk-sequence');
    if (seqEl && data.seek_sequence) {
      seqEl.innerHTML = data.seek_sequence.map((t, i) =>
        `<span class="seq-token ${i === 0 ? 'seq-head' : ''}">${t}</span>`
      ).join('<span class="seq-arrow">→</span>');
    }

    // Disk visualizer
    this.animateDiskHead(data, diskSize);

    // Movement line chart
    if (data.seek_sequence) {
      Charts.line('disk-movement-chart',
        data.seek_sequence.map((_, i) => `${i}`),
        [{ label: 'Head Position', data: data.seek_sequence,
           borderColor: '#06b6d4', backgroundColor: 'rgba(6,182,212,0.1)',
           fill: true, tension: 0.3, pointRadius: 3, pointBackgroundColor: '#06b6d4' }],
        { maxY: diskSize }
      );
    }

    // Seek per move bar chart
    if (data.movements) {
      const nonWrap = data.movements.filter(m => !m.wrap);
      Charts.bar('disk-seek-bar-chart',
        nonWrap.map((_, i) => `M${i+1}`),
        [{ label: 'Seek Distance', data: nonWrap.map(m => m.seek),
           backgroundColor: nonWrap.map(m => m.seek > 50 ? '#ec4899' : m.seek > 20 ? '#f59e0b' : '#10b981'),
           borderRadius: 4 }]
      );
    }
  },

  animateDiskHead(data, diskSize) {
    const el = document.getElementById('disk-viz');
    if (!el) return;
    const toP = t => `${5 + (t / (diskSize - 1)) * 90}%`;

    el.innerHTML = `
      <div class="disk-track" id="disk-track-bar">
        <div class="disk-track-line"></div>
        <div class="disk-ruler">${[0,50,100,150,diskSize-1].map(v=>`<span style="left:${toP(v)}">${v}</span>`).join('')}</div>
      </div>`;
    const bar = el.querySelector('#disk-track-bar');

    // Draw request dots
    const all = [...new Set(data.seek_sequence)];
    all.forEach(t => {
      const dot = document.createElement('div');
      dot.className = 'disk-req-dot'; dot.style.left = toP(t);
      dot.title = `Track ${t}`; bar.appendChild(dot);
    });

    // Animated head
    const head = document.createElement('div');
    head.className = 'disk-head-marker'; head.style.left = toP(data.head_start);
    bar.appendChild(head);

    // Animate step-by-step
    const seq = data.seek_sequence;
    let step = 0;
    const animate = () => {
      if (step >= seq.length) return;
      head.style.left = toP(seq[step]);
      // Mark visited
      bar.querySelectorAll('.disk-req-dot').forEach(d => {
        if (parseFloat(d.style.left) === parseFloat(toP(seq[step])))
          d.classList.add('visited');
      });
      step++;
      setTimeout(animate, 350);
    };
    setTimeout(animate, 400);
  },

  // ── Compare ───────────────────────────────────────────────────────────────
  renderCompare(results, analysis) {
    const algos = Object.keys(results);
    const metrics = ['total_seek','avg_seek','max_seek','seek_variance','fairness_index','total_time_ms'];
    const labels  = { total_seek:'Total Seek', avg_seek:'Avg Seek', max_seek:'Max Seek',
                      seek_variance:'Variance', fairness_index:'Fairness ↑', total_time_ms:'Time (ms)' };
    const higherBetter = new Set(['fairness_index']);

    // Best per metric
    const best = {};
    metrics.forEach(m => {
      const vals = algos.map(a => ({ a, v: results[a][m] ?? (higherBetter.has(m) ? 0 : Infinity) }));
      best[m] = higherBetter.has(m)
        ? vals.reduce((a,b) => a.v > b.v ? a : b).a
        : vals.reduce((a,b) => a.v < b.v ? a : b).a;
    });

    const el = document.getElementById('disk-compare-table');
    if (el) {
      let html = `<table class="compare-table"><thead><tr><th>Metric</th>${algos.map(a=>`<th>${a}</th>`).join('')}</tr></thead><tbody>`;
      metrics.forEach(m => {
        html += `<tr><td style="color:var(--text-secondary)">${labels[m]}</td>`;
        algos.forEach(a => {
          const v = results[a][m];
          html += `<td class="${best[m]===a?'best':''}">${v!=null?v:'—'}</td>`;
        });
        html += '</tr>';
      });
      html += '</tbody></table>';
      el.innerHTML = html;
    }

    // Bar charts
    Charts.bar('disk-compare-chart', algos,
      [{ label:'Total Seek', data: algos.map(a=>results[a].total_seek),
         backgroundColor:['#8b5cf6','#06b6d4','#10b981','#f59e0b','#ec4899','#3b82f6','#a78bfa','#34d399'],
         borderRadius:6 }]
    );

    // Fairness radar-style (use bar)
    Charts.bar('disk-fairness-chart', algos,
      [{ label:'Fairness Index', data: algos.map(a=>results[a].fairness_index||0),
         backgroundColor:'rgba(16,185,129,0.6)', borderRadius:6 }]
    );

    if (analysis) {
      document.getElementById('disk-best-algo').textContent = analysis.overall_best;
      const ins = document.getElementById('disk-insights');
      if (ins) ins.innerHTML = (analysis.insights||[]).map(i=>`<div class="insight-item">${i}</div>`).join('');
      const rec = document.getElementById('disk-recommendation');
      if (rec) rec.textContent = analysis.recommendation;

      // Starvation
      const sw = document.getElementById('disk-compare-starvation');
      if (sw && analysis.starvation_warnings?.length) {
        sw.innerHTML = analysis.starvation_warnings.map(w =>
          `<div class="starvation-alert">⚠ [${w.algorithm}] Track ${w.track} waited ${w.wait_steps} steps</div>`
        ).join('');
        sw.style.display = 'block';
      }
    }
  },

  // ── Race Mode ─────────────────────────────────────────────────────────────
  renderRace(results, ranking, analysis) {
    const el = document.getElementById('disk-race-results');
    if (!el) return;
    let html = '';
    ranking.forEach((r, i) => {
      const data = results[r.algo];
      const pct = ranking[0].total_seek > 0 ? (r.total_seek / ranking[0].total_seek) * 100 : 100;
      const medal = ['🥇','🥈','🥉'][i] || `#${i+1}`;
      html += `
        <div class="race-card">
          <div class="race-header">
            <span class="race-medal">${medal}</span>
            <span class="race-algo-name">${r.algo}</span>
            <span class="race-seek">${r.total_seek} cyl</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill race-fill-${i}" style="width:${pct}%;transition:width 1s ease ${i*0.15}s"></div>
          </div>
          <div class="race-meta">
            <span>⏱ ${r.total_time_ms} ms</span>
            <span>⚖ Fairness: ${r.fairness_index}</span>
          </div>
        </div>`;
    });
    el.innerHTML = html;

    // Seek distance comparison chart
    Charts.bar('disk-race-chart', ranking.map(r => r.algo),
      [{ label:'Total Seek', data: ranking.map(r => r.total_seek),
         backgroundColor: ranking.map((_, i) => ['#fbbf24','#94a3b8','#b45309','#8b5cf6','#06b6d4','#10b981','#ec4899','#3b82f6'][i]),
         borderRadius: 6 }]
    );
  },

  // ── Smart Recommendation ──────────────────────────────────────────────────
  renderRecommendation(data) {
    document.getElementById('rec-pattern').textContent    = data.pattern;
    document.getElementById('rec-spread').textContent     = data.spread + ' cylinders';
    document.getElementById('rec-density').textContent    = data.density;
    document.getElementById('rec-avg-dist').textContent   = data.avg_dist_from_head;
    document.getElementById('rec-algo').textContent       = data.recommended_algorithm;
    document.getElementById('rec-reason').textContent     = data.reason;
  },

  // ── Heatmap ───────────────────────────────────────────────────────────────
  updateHeatmap(requests) {
    requests.forEach(r => {
      const idx = Math.min(Math.floor(r), 199);
      this._heatmap[idx] = (this._heatmap[idx] || 0) + 1;
    });
    this.renderHeatmap();
  },

  renderHeatmap() {
    const el = document.getElementById('disk-heatmap');
    if (!el) return;
    const max = Math.max(1, ...this._heatmap);
    const buckets = 50;
    const size = Math.ceil(200 / buckets);
    const bucketData = Array.from({ length: buckets }, (_, i) => {
      const slice = this._heatmap.slice(i * size, (i + 1) * size);
      return slice.reduce((a, b) => a + b, 0);
    });
    const bmax = Math.max(1, ...bucketData);
    el.innerHTML = bucketData.map((v, i) => {
      const intensity = v / bmax;
      const alpha = intensity * 0.9 + 0.05;
      const color = intensity > 0.7 ? `rgba(236,72,153,${alpha})`
                  : intensity > 0.4 ? `rgba(245,158,11,${alpha})`
                  : intensity > 0.1 ? `rgba(139,92,246,${alpha})`
                  : `rgba(255,255,255,0.04)`;
      return `<div class="heatmap-cell" style="background:${color}" title="Tracks ${i*size}-${(i+1)*size-1}: ${v} requests"></div>`;
    }).join('');
  },

  addPriorityRow() {
    const tbody = document.getElementById('disk-priority-tbody');
    if (!tbody) return;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input type="number" class="form-input pri-track" value="${Math.floor(Math.random()*200)}" min="0" style="width:70px"/></td>
      <td><select class="form-select pri-level" style="width:80px">
        <option value="3">High</option><option value="2" selected>Med</option><option value="1">Low</option>
      </select></td>
      <td><input type="number" class="form-input pri-deadline" value="${Math.floor(Math.random()*20+5)}" min="1" style="width:70px"/></td>
      <td><button class="btn btn-danger btn-sm" onclick="this.closest('tr').remove()">✕</button></td>`;
    tbody.appendChild(tr);
  },

  setBtnLoading(id, on) {
    const btn = document.getElementById(id);
    if (!btn) return;
    btn.disabled = on;
    if (on) { btn.dataset.orig = btn.textContent; btn.innerHTML = '<span class="loading-spinner"></span>'; }
    else btn.textContent = btn.dataset.orig || btn.textContent;
  },
};
