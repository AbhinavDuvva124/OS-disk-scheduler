/* ── CPU SCHEDULER MODULE ── */
const CpuModule = {
  processes: [],
  lastResults: null,
  lastCompare: null,
  simInterval: null,
  simStep: 0,
  simGantt: [],
  simSpeed: 600,
  simRunning: false,

  init() {
    this.loadPresets();
    this.bindEvents();
    this.addProcessRow(); // start with 1 row
  },

  bindEvents() {
    document.getElementById('cpu-add-proc')?.addEventListener('click', () => this.addProcessRow());
    document.getElementById('cpu-run')?.addEventListener('click', () => this.runSchedule());
    document.getElementById('cpu-compare')?.addEventListener('click', () => this.runCompare());
    document.getElementById('cpu-clear')?.addEventListener('click', () => this.clearProcesses());
    document.getElementById('cpu-preset-select')?.addEventListener('change', e => this.applyPreset(e.target.value));
    document.getElementById('cpu-sim-start')?.addEventListener('click', () => this.startSimulation());
    document.getElementById('cpu-sim-pause')?.addEventListener('click', () => this.pauseSimulation());
    document.getElementById('cpu-sim-step')?.addEventListener('click', () => this.stepSimulation());
    document.getElementById('cpu-sim-reset')?.addEventListener('click', () => this.resetSimulation());
    document.getElementById('cpu-speed')?.addEventListener('input', e => {
      this.simSpeed = 1100 - parseInt(e.target.value) * 100;
      document.getElementById('cpu-speed-label').textContent = e.target.value + 'x';
    });
  },

  async loadPresets() {
    try {
      const res = await API.process.presets();
      if (res.status !== 'ok') return;
      const sel = document.getElementById('cpu-preset-select');
      if (!sel) return;
      sel.innerHTML = '<option value="">-- Load Preset --</option>';
      res.data.forEach((p, i) => {
        const o = document.createElement('option');
        o.value = i; o.textContent = p.name;
        sel.appendChild(o);
      });
      this._presets = res.data;
    } catch (e) { console.warn('Preset load error', e); }
  },

  applyPreset(idx) {
    if (idx === '' || !this._presets) return;
    const preset = this._presets[parseInt(idx)];
    if (!preset) return;
    this.clearProcesses();
    preset.processes.forEach(p => this.addProcessRow(p));
    Toast.show(`Loaded preset: ${preset.name}`, 'info');
  },

  addProcessRow(data = null) {
    const tbody = document.getElementById('cpu-proc-tbody');
    if (!tbody) return;
    const idx = tbody.children.length + 1;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input type="text" value="${data?.pid || 'P' + idx}" class="pid-input" placeholder="PID"/></td>
      <td><input type="number" value="${data?.arrival_time ?? 0}" class="at-input" min="0" placeholder="0"/></td>
      <td><input type="number" value="${data?.burst_time ?? 4}" class="bt-input" min="1" placeholder="4"/></td>
      <td><input type="number" value="${data?.priority ?? 1}" class="pri-input" min="1" placeholder="1"/></td>
      <td><button class="btn btn-danger btn-sm" onclick="this.closest('tr').remove()">✕</button></td>`;
    tbody.appendChild(tr);
  },

  clearProcesses() {
    const tbody = document.getElementById('cpu-proc-tbody');
    if (tbody) tbody.innerHTML = '';
  },

  gatherProcesses() {
    const rows = document.querySelectorAll('#cpu-proc-tbody tr');
    return Array.from(rows).map(r => ({
      pid: r.querySelector('.pid-input')?.value || 'P?',
      arrival_time: parseInt(r.querySelector('.at-input')?.value) || 0,
      burst_time: parseInt(r.querySelector('.bt-input')?.value) || 1,
      priority: parseInt(r.querySelector('.pri-input')?.value) || 1,
    }));
  },

  async runSchedule() {
    const procs = this.gatherProcesses();
    const algo = document.getElementById('cpu-algo-select')?.value || 'fcfs';
    const quantum = parseInt(document.getElementById('cpu-quantum')?.value) || 2;
    if (!procs.length) { Toast.show('Add at least one process', 'error'); return; }
    this.setLoading('cpu-run', true);
    try {
      const res = await API.cpu.schedule({ processes: procs, algorithm: algo, quantum });
      this.lastResults = res.data;
      this.renderResults(res.data);
      this.resetSimulation();
      this.simGantt = res.data.gantt;
      Toast.show('Simulation ready — press Start', 'success');
    } catch (e) {
      Toast.show(e.message, 'error');
    } finally {
      this.setLoading('cpu-run', false);
    }
  },

  async runCompare() {
    const procs = this.gatherProcesses();
    const quantum = parseInt(document.getElementById('cpu-quantum')?.value) || 2;
    if (!procs.length) { Toast.show('Add at least one process', 'error'); return; }
    this.setLoading('cpu-compare', true);
    try {
      const res = await API.cpu.compare({ processes: procs, quantum });
      this.lastCompare = res;
      this.renderCompare(res.data, res.analysis);
      Toast.show('Comparison complete', 'success');
    } catch (e) {
      Toast.show(e.message, 'error');
    } finally {
      this.setLoading('cpu-compare', false);
    }
  },

  renderResults(data) {
    // Results table
    const tbody = document.getElementById('cpu-results-tbody');
    if (tbody && data.processes) {
      tbody.innerHTML = data.processes.map(p => `
        <tr>
          <td class="mono">${p.pid}</td>
          <td class="mono">${p.arrival_time}</td>
          <td class="mono">${p.burst_time}</td>
          <td class="mono">${p.priority}</td>
          <td class="mono">${p.start_time ?? '-'}</td>
          <td class="mono">${p.finish_time ?? '-'}</td>
          <td class="mono">${p.waiting_time}</td>
          <td class="mono">${p.turnaround_time}</td>
          <td class="mono">${p.response_time ?? '-'}</td>
        </tr>`).join('');
    }

    // Metrics
    const m = data.metrics;
    if (m) {
      this.setText('cpu-avg-wait', m.avg_waiting_time);
      this.setText('cpu-avg-tat', m.avg_turnaround_time);
      this.setText('cpu-avg-rt', m.avg_response_time);
      this.setText('cpu-util', m.cpu_utilization + '%');
      this.setText('cpu-throughput', m.throughput);
    }

    // Show results section
    document.getElementById('cpu-results-section')?.classList.remove('hidden');
  },

  renderCompare(results, analysis) {
    CompareTable.render('cpu-compare-table', results, true);
    document.getElementById('cpu-compare-section')?.classList.remove('hidden');

    if (analysis) {
      this.setText('cpu-best-algo', analysis.overall_best);
      const insightsEl = document.getElementById('cpu-insights');
      if (insightsEl && analysis.insights) {
        insightsEl.innerHTML = analysis.insights.map(i => `<div class="insight-item">💡 ${i}</div>`).join('');
      }
      const recEl = document.getElementById('cpu-recommendation');
      if (recEl) recEl.textContent = analysis.recommendation;

      // Score bar chart
      if (analysis.scores) {
        const algos = Object.keys(analysis.scores);
        const scores = algos.map(a => analysis.scores[a]);
        Charts.bar('cpu-score-chart', algos, [{
          label: 'Score', data: scores,
          backgroundColor: ['#8b5cf6', '#06b6d4', '#10b981', '#f59e0b'],
          borderRadius: 6,
        }]);
      }
    }
  },

  // ── Simulation Controls ──
  startSimulation() {
    if (!this.simGantt.length) { Toast.show('Run a schedule first', 'error'); return; }
    this.simRunning = true;
    this.simInterval = setInterval(() => this.stepSimulation(), this.simSpeed);
    this.setBtnState(true);
  },

  pauseSimulation() {
    clearInterval(this.simInterval);
    this.simRunning = false;
    this.setBtnState(false);
  },

  stepSimulation() {
    if (this.simStep >= this.simGantt.length) {
      this.pauseSimulation();
      Toast.show('Simulation complete!', 'success');
      return;
    }
    const block = this.simGantt[this.simStep];
    this.renderSimStep(block, this.simStep);
    this.simStep++;
  },

  resetSimulation() {
    this.pauseSimulation();
    this.simStep = 0;
    document.getElementById('cpu-gantt-container').innerHTML = '';
    this.updateQueues([], null, []);
    this.setBtnState(false);
  },

  renderSimStep(block, stepIdx) {
    // Gantt incremental
    const container = document.getElementById('cpu-gantt-container');
    if (container) {
      const colors = Gantt.COLORS;
      const color = block.pid === 'IDLE' ? '#1e1e2e' : colors[Object.keys(Gantt.pidColor).length % colors.length];
      if (!Gantt.pidColor[block.pid]) Gantt.pidColor[block.pid] = color;
      const c = Gantt.pidColor[block.pid] || color;
      const w = Math.max(40, (block.end - block.start) * 28);
      const div = document.createElement('div');
      div.className = 'gantt-block';
      div.style.cssText = `min-width:${w}px;background:${c}25;border:1px solid ${c}80;animation:fadeIn 0.3s ease`;
      div.innerHTML = `<span style="color:${c};font-weight:700">${block.pid}</span><span class="gantt-time">${block.start}→${block.end}</span>`;
      // Wrap in flex
      if (!container.querySelector('.gantt-chart')) {
        const row = document.createElement('div'); row.className = 'gantt-chart';
        container.appendChild(row);
      }
      container.querySelector('.gantt-chart').appendChild(div);
    }

    // Queue animation
    const done = this.simGantt.slice(0, stepIdx + 1).map(b => b.pid).filter(p => p !== 'IDLE');
    const future = this.simGantt.slice(stepIdx + 1).map(b => b.pid).filter(p => p !== 'IDLE');
    this.updateQueues(future, block.pid === 'IDLE' ? null : block.pid, done);
  },

  updateQueues(ready, running, done) {
    const renderQ = (id, items, cls) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.innerHTML = items.length
        ? [...new Set(items)].map(p => `<div class="queue-item ${cls}">${p}</div>`).join('')
        : '<div style="color:var(--text-muted);font-size:0.75rem;padding:8px">Empty</div>';
    };
    renderQ('queue-ready', ready, 'ready');
    renderQ('queue-running', running ? [running] : [], 'running');
    renderQ('queue-done', done, 'done');
  },

  setBtnState(running) {
    const startBtn = document.getElementById('cpu-sim-start');
    const pauseBtn = document.getElementById('cpu-sim-pause');
    if (startBtn) startBtn.disabled = running;
    if (pauseBtn) pauseBtn.disabled = !running;
  },

  setLoading(id, on) {
    const btn = document.getElementById(id);
    if (!btn) return;
    btn.disabled = on;
    btn.innerHTML = on ? '<span class="loading-spinner"></span> Running…' : btn.dataset.label;
  },

  setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; },
};
