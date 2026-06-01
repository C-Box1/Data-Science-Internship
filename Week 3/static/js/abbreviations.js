async function loadAbbrevTable() {
  const wrap = document.getElementById('abbrev-table-wrap');
  const rows = await fetch('/api/abbreviations').then(r => r.json());

  if (rows.error) {
    wrap.innerHTML = `<p class="error">${rows.error}</p>`;
    return;
  }

  if (!rows.length) {
    wrap.innerHTML = '<p class="muted">No abbreviations yet. Run seed_abbreviations.sql or add some above.</p>';
    return;
  }

  let html = '<table><thead><tr><th>Abbreviation</th><th>Full Term</th><th>Field</th></tr></thead><tbody>';
  rows.forEach(r => {
    html += `<tr><td>${r.abbreviation}</td><td>${r.full_term}</td><td>${r.field_category}</td></tr>`;
  });
  html += '</tbody></table>';
  wrap.innerHTML = html;
}

document.getElementById('add-abbrev-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = e.target;
  const body = {
    action: 'add',
    abbreviation: form.abbreviation.value,
    full_term: form.full_term.value,
    field_category: form.field_category.value,
  };
  const data = await postJSON('/api/abbreviations', body);
  if (data.error) {
    alert(data.error);
    return;
  }
  form.reset();
  loadAbbrevTable();
});

loadAbbrevTable();
