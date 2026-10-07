/**
 * Stage-0 REST wrappers — same contracts as legacy index.html.
 */

function authHeaders(token) {
  const h = { 'Content-Type': 'application/json' };
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

export async function fetchProject(projectId, token) {
  const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}`, {
    headers: authHeaders(token),
  });
  return res.json();
}

export async function fetchProbeGuide(projectId, token) {
  const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/probe/guide`, {
    headers: authHeaders(token),
  });
  return res.json();
}

export async function fetchOutputFile(projectId, filename, token) {
  const res = await fetch(
    `/api/projects/${encodeURIComponent(projectId)}/output/${encodeURIComponent(filename)}`,
    { headers: authHeaders(token) },
  );
  return res.json();
}

export async function deleteOutputFile(projectId, filename, token) {
  const res = await fetch(
    `/api/projects/${encodeURIComponent(projectId)}/output/${encodeURIComponent(filename)}`,
    { method: 'DELETE', headers: authHeaders(token) },
  );
  return res.json();
}

export async function generateScript(projectId, token) {
  const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/probe/script`, {
    method: 'POST',
    headers: authHeaders(token),
    body: '{}',
  });
  return res.json();
}

export async function previewProbeDisk(projectId, file, token) {
  const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/probe/preview-disk`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ file }),
  });
  return res.json();
}

export async function applyProbeDisk(projectId, payload, token) {
  const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/probe/apply-disk`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function previewProbeUpload(projectId, probe, token) {
  const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/probe/preview`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ probe }),
  });
  return res.json();
}

export async function applyProbeUpload(projectId, payload, token) {
  const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/probe/apply`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function fetchAuthStatus(token) {
  const res = await fetch('/api/auth/status', {
    headers: authHeaders(token),
  });
  return res.json();
}
