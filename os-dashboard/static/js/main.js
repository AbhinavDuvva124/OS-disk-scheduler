/* ── MAIN APP ENTRY POINT ── */
document.addEventListener('DOMContentLoaded', () => {
  Toast.init();

  // ── Main tab navigation ──
  const tabs = document.querySelectorAll('.nav-tab');
  const sections = document.querySelectorAll('.section');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      sections.forEach(s => s.classList.remove('active'));
      tab.classList.add('active');
      const target = document.getElementById(tab.dataset.section);
      if (target) target.classList.add('active');
      if (tab.dataset.section === 'section-system') SystemModule.startPolling();
      else SystemModule.stopPolling();
    });
  });

  // ── Disk sub-tab navigation ──
  document.querySelectorAll('.disk-subtab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.disk-subtab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.disk-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const panel = document.getElementById(btn.dataset.panel);
      if (panel) panel.classList.add('active');
    });
  });

  // ── Init modules ──
  SystemModule.init();
  CpuModule.init();
  DiskModule.init();

  // Seed 3 priority rows
  for (let i = 0; i < 3; i++) DiskModule.addPriorityRow();

  // ── CPU quantum visibility ──
  document.getElementById('cpu-algo-select')?.addEventListener('change', e => {
    const qWrap = document.getElementById('quantum-wrap');
    if (qWrap) qWrap.style.display = e.target.value === 'rr' ? 'flex' : 'none';
  });

  // ── Set data-label on buttons ──
  document.querySelectorAll('.btn[id]').forEach(btn => {
    btn.dataset.label = btn.textContent.trim();
  });

  console.log('OS Dashboard initialized');
});

