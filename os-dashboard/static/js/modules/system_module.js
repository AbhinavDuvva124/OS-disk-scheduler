/* ── SYSTEM MONITOR MODULE ── */
const SystemModule = {
  intervalId: null,
  cpuHistory: [],
  memHistory: [],
  timestamps: [],
  maxHistory: 30,

  init() {
    this.startPolling();
  },

  startPolling() {
    this.fetchData();
    this.intervalId = setInterval(() => this.fetchData(), 2000);
  },

  stopPolling() {
    clearInterval(this.intervalId);
  },

  async fetchData() {
    try {
      const res = await API.system.overview();
      if (res.status === 'ok') this.render(res.data);
    } catch (e) {
      console.warn('System fetch error:', e.message);
    }
  },

  render(data) {
    const { cpu, memory, disk, network, uptime, process_count, top_processes } = data;

    // Update metric cards
    this.setText('cpu-overall', `${cpu.overall.toFixed(1)}%`);
    this.setText('mem-percent', `${memory.percent.toFixed(1)}%`);
    this.setText('mem-used', `${memory.used_gb} GB`);
    this.setText('proc-count', process_count);
    this.setText('uptime-val', uptime);
    this.setText('cpu-freq', `${cpu.frequency.current} MHz`);

    // Progress bars
    this.setProgress('cpu-bar', cpu.overall);
    this.setProgress('mem-bar', memory.percent);

    // Disk partitions
    if (disk.partitions?.length) {
      const p = disk.partitions[0];
      this.setText('disk-used', `${p.used_gb} GB`);
      this.setText('disk-total', `${p.total_gb} GB`);
      this.setProgress('disk-bar', p.percent);
    }

    // Network
    this.setText('net-sent', `${network.bytes_sent_mb} MB`);
    this.setText('net-recv', `${network.bytes_recv_mb} MB`);

    // CPU cores
    this.renderCores(cpu.per_core);

    // History charts
    const now = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    this.timestamps.push(now);
    this.cpuHistory.push(cpu.overall);
    this.memHistory.push(memory.percent);

    if (this.timestamps.length > this.maxHistory) {
      this.timestamps.shift(); this.cpuHistory.shift(); this.memHistory.shift();
    }

    // Init or update charts
    if (!Charts.instances['cpu-history-chart']) {
      Charts.line('cpu-history-chart', [...this.timestamps], [{
        label: 'CPU %', data: [...this.cpuHistory],
        borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.1)',
        fill: true, tension: 0.4, pointRadius: 0,
      }], { maxY: 100 });
    } else {
      Charts.updateLine('cpu-history-chart', now, cpu.overall);
    }

    if (!Charts.instances['mem-donut-chart']) {
      Charts.doughnut('mem-donut-chart',
        ['Used', 'Available'],
        [memory.used_gb, memory.available_gb],
        ['#8b5cf6', 'rgba(255,255,255,0.06)']
      );
    } else {
      const chart = Charts.instances['mem-donut-chart'];
      chart.data.datasets[0].data = [memory.used_gb, memory.available_gb];
      chart.update('none');
    }

    // Top processes table
    this.renderProcessTable(top_processes);
  },

  renderCores(perCore) {
    const el = document.getElementById('core-grid');
    if (!el || !perCore) return;
    el.innerHTML = perCore.map((v, i) =>
      `<div class="core-item">
        <div class="core-label">C${i}</div>
        <div class="core-value">${v.toFixed(0)}%</div>
        <div class="progress-track" style="margin-top:4px">
          <div class="progress-fill" style="width:${v}%;background:${v>80?'#ec4899':v>60?'#f59e0b':'#8b5cf6'}"></div>
        </div>
      </div>`
    ).join('');
  },

  renderProcessTable(procs) {
    const tbody = document.getElementById('sys-proc-tbody');
    if (!tbody || !procs) return;
    tbody.innerHTML = procs.map(p => `
      <tr>
        <td class="mono">${p.pid}</td>
        <td>${p.name}</td>
        <td><span class="badge ${p.status === 'running' ? 'badge-green' : p.status === 'sleeping' ? 'badge-blue' : 'badge-yellow'}">${p.status}</span></td>
        <td class="mono">${p.cpu_percent}%</td>
        <td class="mono">${p.memory_percent.toFixed(2)}%</td>
        <td class="mono">${p.threads}</td>
      </tr>`
    ).join('');
  },

  setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  },

  setProgress(id, pct) {
    const el = document.getElementById(id);
    if (el) el.style.width = `${Math.min(100, pct)}%`;
  },
};
