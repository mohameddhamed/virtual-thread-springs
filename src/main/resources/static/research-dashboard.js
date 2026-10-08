(() => {
  const $ = id => document.getElementById(id);
  const fmt = (v, unit = '') => v == null ? '—' : `${Number(v).toLocaleString(undefined,{maximumFractionDigits:2})}${unit}`;
  let data, records, filtered;
  fetch('/data/normalized-evidence.json').then(r => r.json()).then(d => {
    data = d; records = d.records; filtered = records;
    $('generated').textContent = `dataset generated ${new Date(d.generated_at).toLocaleString()}`;
    $('record-count').textContent = `${records.length} measured records`;
    const options = (key) => [...new Set(records.map(r => r[key]).filter(Boolean))].sort();
    [['family-filter','family'],['jdk-filter','jdk_major'],['condition-filter','condition_label'],['thread-filter','execution_mode']].forEach(([id,key]) => options(key).forEach(v => $(id).insertAdjacentHTML('beforeend', `<option value="${v}">${v}</option>`)));
    ['family-filter','jdk-filter','condition-filter','thread-filter'].forEach(id => $(id).addEventListener('change', render));
    render();
    renderFindings();
    renderSections();
    $('limitations').innerHTML = d.limitations.map(x => `<div>${x}</div>`).join('');
  }).catch(e => $('record-count').textContent = `Dataset unavailable: ${e.message}`);
  function render() {
    const vals = {family:$('family-filter').value,jdk_major:$('jdk-filter').value,condition_label:$('condition-filter').value,execution_mode:$('thread-filter').value};
    filtered = records.filter(r => Object.entries(vals).every(([k,v]) => !v || r[k] === v));
    $('trial-body').innerHTML = filtered.map((r,i) => `<tr data-index="${i}"><td><b>${r.trial_id || r.run_id}</b><br><small>${r.run_id}</small></td><td>${r.condition_label}<br><small>${r.family}</small></td><td>${r.jdk_major}</td><td>${fmt(r.metrics.requests)}</td><td>${fmt(r.metrics.median_ms,' ms')}</td><td>${fmt(r.metrics.p95_ms,' ms')}</td><td>${r.jfr.count == null ? '—' : r.jfr.count}</td></tr>`).join('') || '<tr><td colspan="7">No matching records.</td></tr>';
    $('trial-body').querySelectorAll('tr[data-index]').forEach(row => row.addEventListener('click', () => detail(filtered[Number(row.dataset.index)])));
  }
  function detail(r) {
    $('trial-detail').innerHTML = `<b>${r.condition_label} · trial ${r.trial_id}</b><br><span class="muted">${r.timestamp_utc || 'standalone control'} · ${r.jdk || 'JDK not recorded'} · ${r.target_vus || '—'} VUs</span><br><br>Raw result: <code>${r.provenance.result || 'not available'}</code> · JFR: <code>${r.provenance.jfr || 'not available'}</code><br><span class="muted">Classifications: trial=${r.classification.trial}, metrics=${r.classification.metrics}, JFR=${r.classification.jfr}</span>`;
  }
  function renderFindings() {
    const sync = records.filter(r => r.family === 'synchronization');
    const pinned = sync.filter(r => r.jfr.count > 0).length;
    const jni = records.filter(r => r.family === 'jni-boundary' && r.condition_id === 'blocking-jni');
    $('headline-findings').innerHTML = `<div class="finding"><b>${sync.length}</b><span>Java 21 synchronization trials preserved</span></div><div class="finding"><b>${pinned ? `${pinned}/${sync.length}` : '0'}</b><span>sync trials with observed JFR pinning</span></div><div class="finding"><b>${jni.filter(r => r.jfr.count === 0).length}/${jni.length}</b><span>blocking-JNI trials with explicit zero JFR events</span></div>`;
  }
  function cards(selector, groups) { $(selector).innerHTML = groups.map(g => `<div class="summary-card"><b>${g.value}</b><span>${g.label}</span></div>`).join(''); }
  function renderSections() {
    const sync = records.filter(r => r.family === 'synchronization');
    const jni = records.filter(r => r.family === 'jni-boundary');
    cards('sync-summary', [{value:sync.length,label:'measured trials'},{value:fmt(sync.reduce((a,r)=>a+r.metrics.requests,0)/sync.length),label:'mean requests / trial'},{value:`${sync.filter(r=>r.jfr.count>0).length}/${sync.length}`,label:'trials with pinned events'}]);
    cards('jni-summary', [{value:jni.length,label:'measured trials'},{value:`${jni.filter(r=>r.jfr.count===0).length}/${jni.length}`,label:'explicit zero JFR counts'},{value:'21 · 24 · 25',label:'runtime boundary'}]);
    const cpu = records.find(r => r.condition_id === 'cpu-control');
    if (cpu) $('cpu-control').textContent = `${fmt(cpu.metrics.requests)} requests; median ${fmt(cpu.metrics.median_ms,' ms')} from ${cpu.provenance.result}.`;
  }
})();
