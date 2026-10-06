const BASE_URL = '';

const _getToken = () => {
  try { return localStorage.getItem('token') || ''; } catch (e) { return ''; }
};

const _clearToken = () => {
  try { localStorage.removeItem('token'); } catch (e) {}
};

const _setToken = (token) => {
  try { localStorage.setItem('token', token); } catch (e) {}
};

const _headers = () => {
  const headers = { 'Content-Type': 'application/json' };
  const token = _getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
};

const _handleError = (res) => {
  if (!res.ok) {
    return res.json().then(data => {
      throw Object.assign(new Error('HTTP ' + res.status), { status: res.status, data });
    }).catch(() => {
      throw new Error('HTTP ' + res.status);
    });
  }
  return res.json();
};

const _jsonOrText = (res) => res.json().catch(() => res.text());

const _request = async (method, path, body = null) => {
  const url = BASE_URL + path;
  const options = { method, headers: _headers() };
  if (body !== null) options.body = JSON.stringify(body);
  const res = await fetch(url, options);
  const data = await _handleError(res);
  return data;
};

const api = {
  get: (path) => _request('GET', path),
  post: (path, body) => _request('POST', path, body),
  put: (path, body) => _request('PUT', path, body),
  delete: (path) => _request('DELETE', path),

  login(username, password) {
    return _request('POST', '/auth/login', { username, password });
  },
  register(username, password) {
    return _request('POST', '/auth/register', { username, password });
  },

  getToken: _getToken,
  setToken: _setToken,
  clearToken: _clearToken,

  checkAuth: () => {
    return !!_getToken();
  },

  request: (method, path, body) => _request(method, path, body)
};
