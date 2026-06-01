let rowCount = 1;

document.getElementById('add-row-btn')?.addEventListener('click', () => {
  if (rowCount >= MAX_ROWS) return;
  const container = document.getElementById('product-rows');
  const first = container.querySelector('.product-row');
  const clone = first.cloneNode(true);
  rowCount += 1;
  clone.dataset.row = rowCount - 1;
  clone.querySelector('h3').textContent = `Product ${rowCount}`;
  clone.querySelectorAll('input').forEach(i => { i.value = ''; });
  container.appendChild(clone);
  if (rowCount >= MAX_ROWS) {
    document.getElementById('add-row-btn').disabled = true;
  }
});

document.getElementById('manual-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const rows = document.querySelectorAll('.product-row');
  const products = [];

  rows.forEach(row => {
    const get = name => row.querySelector(`[name="${name}"]`)?.value?.trim();
    const ref = get('reference');
    if (!ref) return;
    products.push({
      reference: ref,
      collection: get('collection'),
      gender: get('gender'),
      movement: get('movement'),
      kind: get('kind'),
      dial: get('dial') || null,
      bracelet: get('bracelet') || null,
      color: get('color') || null,
      case_size: get('case_size') || null,
    });
  });

  const resultEl = document.getElementById('manual-result');
  if (!products.length) {
    showMessage(resultEl, 'Please fill in at least one product reference.', true);
    return;
  }

  const data = await postJSON('/api/products/manual', { products });
  if (data.error) {
    showMessage(resultEl, data.error, true);
    return;
  }
  showMessage(resultEl, `<strong>Saved!</strong> ${formatSummary(data.insert_summary)}`);
});
