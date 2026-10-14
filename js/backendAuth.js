/* Backend-backed authentication, separate from the legacy local demo accounts. */
const AUTH_TOKEN_KEY = 'train_api_access_token';

function getApiToken() {
  return sessionStorage.getItem(AUTH_TOKEN_KEY);
}

function getApiUser() {
  const token = getApiToken();
  if (!token) return null;
  try {
    const user = JSON.parse(sessionStorage.getItem('train_api_user') || 'null');
    return user ? { ...user, fullName: user.full_name, backendAccount: true } : null;
  } catch {
    return null;
  }
}

function storeApiSession(result) {
  sessionStorage.setItem(AUTH_TOKEN_KEY, result.access_token);
  sessionStorage.setItem('train_api_user', JSON.stringify(result.user));
}

function clearApiSession() {
  sessionStorage.removeItem(AUTH_TOKEN_KEY);
  sessionStorage.removeItem('train_api_user');
}

async function apiLoginForm(event) {
  event.preventDefault();
  const error = document.getElementById('user-login-error');
  error.textContent = '';
  try {
    const result = await trainApi.login({
      email: document.getElementById('user-login-email').value.trim(),
      password: document.getElementById('user-login-password').value,
    });
    storeApiSession(result);
    closeAuth();
    updateUI();
  } catch (err) {
    error.textContent = err.message;
  }
}

async function apiRegisterForm(event) {
  event.preventDefault();
  const error = document.getElementById('user-register-error');
  error.textContent = '';
  try {
    const result = await trainApi.register({
      full_name: document.getElementById('user-reg-name').value.trim(),
      email: document.getElementById('user-reg-email').value.trim(),
      phone: document.getElementById('user-reg-phone').value.trim() || null,
      nin: document.getElementById('user-reg-nin').value.trim() || null,
      password: document.getElementById('user-reg-password').value,
    });
    storeApiSession(result);
    closeAuth();
    updateUI();
  } catch (err) {
    error.textContent = err.message;
  }
}
