async function loadFilters() {
  const res = await fetch('/api/filters');
  const data = await res.json();

  fillSelect('filter-shop', data.shops, s => s.shop_id, s => `${s.shop_id} — ${s.mall_name}`);
  fillSelect('filter-city', data.cities, c => c, c => c);
  fillSelect('filter-kind', data.kinds, k => k, k => k);
  fillSelect('filter-collection', data.collections, c => c, c => c);
  fillSelect('filter-month-from', data.sale_months, m => m, m => m.slice(0, 7));
  fillSelect('filter-month-to', data.sale_months, m => m, m => m.slice(0, 7));
}

function fillSelect(id, items, valFn, labelFn) {
  const sel = document.getElementById(id);
  if (!sel || !items) return;
  const first = sel.options[0];
  sel.innerHTML = '';
  sel.appendChild(first);
  items.forEach(item => {
    const opt = document.createElement('option');
    opt.value = valFn(item);
    opt.textContent = labelFn(item);
    sel.appendChild(opt);
  });
}

function getFilterParams() {
  const params = new URLSearchParams();
  ['shop', 'city', 'kind', 'collection'].forEach(key => {
    const val = document.getElementById(`filter-${key}`)?.value;
    if (val) params.set(key === 'shop' ? 'shop_id' : key, val);
  });
  const from = document.getElementById('filter-month-from')?.value;
  const to = document.getElementById('filter-month-to')?.value;
  if (from) params.set('month_from', from + '-01');
  if (to) params.set('month_to', to + '-01');
  return params;
}

async function loadChart(chartId, btn) {
  document.querySelectorAll('.btn-chart').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const params = getFilterParams();
  const area = document.getElementById('chart-area');
  area.innerHTML = '<p class="muted">Loading chart…</p>';

  const res = await fetch(`/api/analytics/${chartId}?${params}`);
  const data = await res.json();

  if (data.error) {
    area.innerHTML = `<p class="error">${data.error}</p>`;
    return;
  }

  const chartData = JSON.parse(data.chart);
  Plotly.newPlot('chart-area', chartData.data, chartData.layout, { responsive: true });

  const tableArea = document.getElementById('table-area');
  if (!data.rows || !data.rows.length) {
    tableArea.innerHTML = '<p class="muted">No data for the selected filters.</p>';
    return;
  }

  const keys = Object.keys(data.rows[0]);
  let html = '<table><thead><tr>' + keys.map(k => `<th>${k}</th>`).join('') + '</tr></thead><tbody>';
  data.rows.forEach(row => {
    html += '<tr>' + keys.map(k => `<td>${row[k]}</td>`).join('') + '</tr>';
  });
  html += '</tbody></table>';
  tableArea.innerHTML = html;
}

document.querySelectorAll('.btn-chart').forEach(btn => {
  btn.addEventListener('click', () => loadChart(btn.dataset.chart, btn));
});

loadFilters();
