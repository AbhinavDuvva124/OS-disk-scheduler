/* ── TOAST NOTIFICATIONS ── */
const Toast = {
  container: null,
  init() {
    this.container = document.getElementById('toast-container');
  },
  show(msg, type = 'info', duration = 3500) {
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
    this.container.appendChild(el);
    setTimeout(() => el.remove(), duration);
  },
};

/* ── GANTT CHART RENDERER ── */
const Gantt = {
  COLORS: ['#8b5cf6','#06b6d4','#10b981','#f59e0b','#ec4899','#3b82f6','#a78bfa','#34d399','#fbbf24','#f87171'],
  pidColor: {},
  colorIdx: 0,

  getColor(pid) {
    if (pid === 'IDLE') return '#1e1e2e';
    if (!this.pidColor[pid]) {
      this.pidColor[pid] = this.COLORS[this.colorIdx % this.COLORS.length];
      this.colorIdx++;
    }
    return this.pidColor[pid];
  },

  render(containerId, ganttData) {
    const el = document.getElementById(containerId);
    if (!el || !ganttData?.length) return;
    this.pidColor = {}; this.colorIdx = 0;

    const maxTime = Math.max(...ganttData.map(b => b.end));
    const minW = 40;

    let html = '<div class="gantt-chart">';
    ganttData.forEach(b => {
      const dur = b.end - b.start;
      const w = Math.max(minW, dur * 28);
      const color = this.getColor(b.pid);
      html += `<div class="gantt-block" style="min-width:${w}px;background:${color}20;border:1px solid ${color}60" title="${b.pid}: ${b.start}→${b.end}">
        <span style="color:${color}">${b.pid}</span>
        <span class="gantt-time">${b.start}-${b.end}</span>
      </div>`;
    });
    html += '</div>';

    // Timeline ticks
    const times = [...new Set(ganttData.flatMap(b => [b.start, b.end]))].sort((a, b) => a - b);
    html += '<div class="gantt-timeline">';
    times.forEach(t => html += `<div class="gantt-tick">${t}</div>`);
    html += '</div>';

    el.innerHTML = html;
  },
};

/* ── DISK VISUALIZER ── */
const DiskViz = {
  render(containerId, data, diskSize = 200) {
    const el = document.getElementById(containerId);
    if (!el || !data) return;
    el.innerHTML = '';

    const track = document.createElement('div');
    track.className = 'disk-track';
    track.innerHTML = '<div class="disk-track-line"></div>';

    const toPos = (t) => `${5 + (t / (diskSize - 1)) * 90}%`;

    // Draw request dots
    const seq = data.seek_sequence || [];
    seq.forEach((t, i) => {
      const dot = document.createElement('div');
      dot.className = 'disk-request-dot' + (i === 0 ? '' : i < seq.length - 1 ? '' : ' visited');
      dot.style.left = toPos(t);
      dot.title = `Track ${t}`;
      track.appendChild(dot);
    });

    // Animated head
    const head = document.createElement('div');
    head.className = 'disk-head';
    head.style.left = toPos(data.head_start);
    track.appendChild(head);

    el.appendChild(track);

    // Animate head through sequence
    let step = 0;
    const animate = () => {
      if (step >= seq.length) return;
      head.style.left = toPos(seq[step]);
      step++;
      setTimeout(animate, 400);
    };
    setTimeout(animate, 300);
  },
};

/* ── COMPARISON TABLE ── */
const CompareTable = {
  render(containerId, results, isMetric = true) {
    const el = document.getElementById(containerId);
    if (!el) return;

    if (isMetric) {
      const algos = Object.keys(results);
      const metrics = ['avg_waiting_time', 'avg_turnaround_time', 'avg_response_time', 'cpu_utilization', 'throughput'];
      const labels = { avg_waiting_time: 'Avg Wait', avg_turnaround_time: 'Avg TAT', avg_response_time: 'Avg RT', cpu_utilization: 'CPU %', throughput: 'Throughput' };

      // Find best per metric
      const best = {};
      metrics.forEach(m => {
        const vals = algos.map(a => ({ a, v: results[a]?.metrics?.[m] ?? (m === 'cpu_utilization' || m === 'throughput' ? 0 : Infinity) }));
        best[m] = (m === 'cpu_utilization' || m === 'throughput')
          ? vals.reduce((a, b) => a.v > b.v ? a : b).a
          : vals.reduce((a, b) => a.v < b.v ? a : b).a;
      });

      let html = `<table class="compare-table"><thead><tr><th>Metric</th>${algos.map(a => `<th>${a}</th>`).join('')}</tr></thead><tbody>`;
      metrics.forEach(m => {
        html += `<tr><td style="color:var(--text-secondary)">${labels[m]}</td>`;
        algos.forEach(a => {
          const v = results[a]?.metrics?.[m];
          const isBest = best[m] === a;
          html += `<td class="${isBest ? 'best' : ''}">${v != null ? v : '-'}</td>`;
        });
        html += '</tr>';
      });
      html += '</tbody></table>';
      el.innerHTML = html;
    } else {
      // Disk comparison
      const algos = Object.keys(results);
      let html = `<table class="compare-table"><thead><tr><th>Algorithm</th><th>Total Seek</th><th>Avg Seek</th></tr></thead><tbody>`;
      const minSeek = Math.min(...algos.map(a => results[a].total_seek));
      algos.forEach(a => {
        const d = results[a];
        const best = d.total_seek === minSeek;
        html += `<tr><td>${a}</td><td class="${best ? 'best' : ''}">${d.total_seek}</td><td>${d.avg_seek}</td></tr>`;
      });
      html += '</tbody></table>';
      el.innerHTML = html;
    }
  },
};

/* ── CHART HELPERS (Chart.js wrappers) ── */
const Charts = {
  instances: {},

  destroy(id) {
    if (this.instances[id]) { this.instances[id].destroy(); delete this.instances[id]; }
  },

  line(id, labels, datasets, opts = {}) {
    this.destroy(id);
    const ctx = document.getElementById(id)?.getContext('2d');
    if (!ctx) return;
    this.instances[id] = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true, maintainAspectRatio: false,
        animation: { duration: 600 },
        plugins: { legend: { labels: { color: '#94a3b8', font: { size: 11 } } } },
        scales: {
          x: { ticks: { color: '#475569' }, grid: { color: 'rgba(255,255,255,0.04)' } },
          y: { ticks: { color: '#475569' }, grid: { color: 'rgba(255,255,255,0.04)' }, min: 0, max: opts.maxY || 100 },
        },
        ...opts,
      },
    });
  },

  bar(id, labels, datasets, opts = {}) {
    this.destroy(id);
    const ctx = document.getElementById(id)?.getContext('2d');
    if (!ctx) return;
    this.instances[id] = new Chart(ctx, {
      type: 'bar',
      data: { labels, datasets },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#94a3b8', font: { size: 11 } } } },
        scales: {
          x: { ticks: { color: '#475569' }, grid: { color: 'rgba(255,255,255,0.04)' } },
          y: { ticks: { color: '#475569' }, grid: { color: 'rgba(255,255,255,0.04)' }, beginAtZero: true },
        },
        ...opts,
      },
    });
  },

  doughnut(id, labels, data, colors) {
    this.destroy(id);
    const ctx = document.getElementById(id)?.getContext('2d');
    if (!ctx) return;
    this.instances[id] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{ data, backgroundColor: colors, borderWidth: 0 }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        cutout: '70%',
        plugins: { legend: { position: 'right', labels: { color: '#94a3b8', font: { size: 11 }, padding: 12 } } },
      },
    });
  },

  updateLine(id, label, value) {
    const chart = this.instances[id];
    if (!chart) return;
    const maxPoints = 30;
    chart.data.labels.push(label);
    chart.data.datasets[0].data.push(value);
    if (chart.data.labels.length > maxPoints) {
      chart.data.labels.shift();
      chart.data.datasets[0].data.shift();
    }
    chart.update('none');
  },
};
