/** Shared helpers for all pages */

function showMessage(el, html, isError = false) {
  el.classList.remove('hidden', 'error', 'success');
  el.classList.add(isError ? 'error' : 'success');
  el.innerHTML = html;
}

function formatSummary(summary) {
  if (!summary) return '';
  return `Inserted: ${summary.inserted || 0}, Skipped: ${summary.skipped || 0}, Conflicts: ${summary.conflict || 0}`;
}

async function postJSON(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res.json();
}
