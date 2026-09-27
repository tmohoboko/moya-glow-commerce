let accessToken = null;
export function setToken(value) { accessToken = value; }
export async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {'Content-Type': 'application/json', ...(accessToken ? {Authorization: `Bearer ${accessToken}`} : {}), ...options.headers},
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  if (!response.headers.get('content-type')?.includes('application/json') && response.status !== 204) {
    throw new Error('Account services are unavailable on this host. Please try again later.');
  }
  const data = response.status === 204 ? null : await response.json();
  if (!response.ok) {
    const message = typeof data.detail === 'string' ? data.detail : data.detail?.map(e => `${e.field}: ${e.message}`).join(';');
    const error = new Error(`${message || 'Request failed'}${data.request_id ? ` (reference ${data.request_id})` : ''}`);
    error.status = response.status;
    throw error;
  }
  return data;
}
