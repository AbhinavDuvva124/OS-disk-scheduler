/* ── API MODULE ── */
const API = {
  base: '',

  async get(path) {
    const r = await fetch(this.base + path);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json();
  },

  async post(path, body) {
    const r = await fetch(this.base + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const json = await r.json();
    if (!r.ok) throw new Error(json.message || `HTTP ${r.status}`);
    return json;
  },

  system: {
    overview: () => API.get('/api/system/overview'),
    cpu: () => API.get('/api/system/cpu'),
    memory: () => API.get('/api/system/memory'),
    processes: () => API.get('/api/system/processes'),
  },

  cpu: {
    schedule: (body) => API.post('/api/cpu/schedule', body),
    compare: (body) => API.post('/api/cpu/compare', body),
  },

  disk: {
    schedule: (body) => API.post('/api/disk/schedule', body),
    compare: (body) => API.post('/api/disk/compare', body),
  },

  process: {
    presets: () => API.get('/api/process/presets'),
    diskPresets: () => API.get('/api/process/disk-presets'),
  },
};
