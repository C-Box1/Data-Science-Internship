let pendingAbbrevQueue = [];

async function uploadFile(endpoint, fileInput, resultEl) {
  const file = fileInput.files[0];
  if (!file) {
    showMessage(resultEl, 'Please choose a file first.', true);
    return;
  }

  showMessage(resultEl, 'Uploading and cleaning…');
  const form = new FormData();
  form.append('file', file);

  const res = await fetch(endpoint, { method: 'POST', body: form });
  const data = await res.json();

  if (!res.ok || data.error) {
    showMessage(resultEl, data.error || 'Upload failed.', true);
    return;
  }

  let html = `<strong>Done!</strong> Products loaded: ${data.products_loaded ?? '—'}. ${formatSummary(data.insert_summary)}`;
  if (data.sold_records !== undefined) {
    html = `<strong>Done!</strong> Sales records: ${data.sold_records}, Stock records: ${data.present_records}. Format: ${data.format}`;
  }
  showMessage(resultEl, html);

  if (data.unknown_abbreviations && data.unknown_abbreviations.length) {
    pendingAbbrevQueue = data.unknown_abbreviations;
    showAbbrevPrompt();
  }
}

document.getElementById('upload-products-btn')?.addEventListener('click', () => {
  uploadFile('/api/upload/products', document.getElementById('product-file'), document.getElementById('product-result'));
});

document.getElementById('upload-report-btn')?.addEventListener('click', () => {
  uploadFile('/api/upload/monthly-report', document.getElementById('report-file'), document.getElementById('report-result'));
});

async function showAbbrevPrompt() {
  if (!pendingAbbrevQueue.length) return;
  const item = pendingAbbrevQueue[0];
  const modal = document.getElementById('abbrev-prompt');
  document.getElementById('abbrev-context').textContent =
    `"${item.token}" found in ${item.field} (reference ${item.reference || 'unknown'}). What does it mean?`;

  const select = document.getElementById('abbrev-existing');
  select.innerHTML = '<option value="">— select existing term —</option>';
  const terms = await fetch(`/api/abbreviations/full-terms/${item.field_category}`).then(r => r.json());
  terms.forEach(t => {
    const opt = document.createElement('option');
    opt.value = t;
    opt.textContent = t;
    select.appendChild(opt);
  });

  modal.classList.remove('hidden');
}

document.getElementById('abbrev-save')?.addEventListener('click', async () => {
  const item = pendingAbbrevQueue[0];
  const existing = document.getElementById('abbrev-existing').value;
  const newTerm = document.getElementById('abbrev-new-term').value.trim();
  const fullTerm = existing || newTerm;
  if (!fullTerm) return;

  await postJSON('/api/abbreviations', {
    action: 'add',
    abbreviation: item.token,
    full_term: fullTerm,
    field_category: item.field_category,
  });

  pendingAbbrevQueue.shift();
  document.getElementById('abbrev-prompt').classList.add('hidden');
  if (pendingAbbrevQueue.length) showAbbrevPrompt();
});

document.getElementById('abbrev-ignore')?.addEventListener('click', async () => {
  await postJSON('/api/abbreviations', { action: 'ignore' });
  pendingAbbrevQueue.shift();
  document.getElementById('abbrev-prompt').classList.add('hidden');
  if (pendingAbbrevQueue.length) showAbbrevPrompt();
});
