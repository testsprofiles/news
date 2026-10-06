const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const loginTab = document.getElementById('loginTab');
const registerTab = document.getElementById('registerTab');
const loginSubmitBtn = document.getElementById('loginSubmitBtn');
const registerSubmitBtn = document.getElementById('registerSubmitBtn');
const loginError = document.getElementById('loginError');
const registerError = document.getElementById('registerError');
const loginPassword = document.getElementById('loginPassword');
const loginUsername = document.getElementById('loginUsername');
const registerPassword = document.getElementById('registerPassword');
const registerUsername = document.getElementById('registerUsername');
const toggleLoginPass = document.getElementById('toggleLoginPassword');
const toggleRegisterPass = document.getElementById('toggleRegisterPassword');
const successToast = document.getElementById('successToast');
const toastMessage = document.getElementById('toastMessage');

const showTab = (tab) => {
  if (tab === 'login') {
    loginTab.classList.add('tab-active', 'text-blue-600', 'font-semibold');
    loginTab.classList.remove('text-gray-500', 'hover:text-blue-600');
    registerTab.classList.remove('tab-active', 'text-blue-600', 'font-semibold');
    registerTab.classList.add('text-gray-500', 'hover:text-blue-600');
    loginForm.classList.remove('hidden');
    registerForm.classList.add('hidden');
  } else {
    registerTab.classList.add('tab-active', 'text-blue-600', 'font-semibold');
    registerTab.classList.remove('text-gray-500', 'hover:text-blue-600');
    loginTab.classList.remove('tab-active', 'text-blue-600', 'font-semibold');
    loginTab.classList.add('text-gray-500', 'hover:text-blue-600');
    registerForm.classList.remove('hidden');
    loginForm.classList.add('hidden');
  }
};

document.addEventListener('DOMContentLoaded', () => {
  showTab('login');

  loginTab.addEventListener('click', () => showTab('login'));
  registerTab.addEventListener('click', () => showTab('register'));
});

const setError = (el, msg, show = true) => {
  if (!msg) { el.classList.add('hidden'); el.textContent = ''; return; }
  el.classList.remove('hidden');
  el.textContent = msg;
};

toggleLoginPass.addEventListener('click', () => {
  const type = loginPassword.getAttribute('type') === 'password' ? 'text' : 'password';
  loginPassword.setAttribute('type', type);
  toggleLoginPass.innerHTML = type === 'password'
    ? `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>`
    : `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.586 3.586M13.586 13.586L3 3"/></svg>`;
});

toggleRegisterPass.addEventListener('click', () => {
  const type = registerPassword.getAttribute('type') === 'password' ? 'text' : 'password';
  registerPassword.setAttribute('type', type);
  toggleRegisterPass.innerHTML = type === 'password'
    ? `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>`
    : `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.586 3.586M13.586 13.586L3 3"/></svg>`;
});

loginForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = loginUsername.value.trim();
  const password = loginPassword.value;
  if (!username || !password) {
    setError(loginError, 'Username va parol kiritilishi shart!');
    return;
  }
  setError(loginError, '');
  loginSubmitBtn.disabled = true;

  try {
    const res = await api.login(username, password);
    if (res.token) {
      api.setToken(res.token);
      showToast('Muvaffaqiyatli kirildi. Portala yo`naltirilmoqda...', 'success');
      setTimeout(() => window.location.href = 'index.html', 800);
    } else {
      setError(loginError, res.message || 'Kirish xatosi');
    }
  } catch (err) {
    console.error('Login error:', err);
    setError(loginError, err.data && err.data.message ? err.data.message : (err.message || 'Xatolik yuz berdi'));
  } finally {
    loginSubmitBtn.disabled = false;
  }
});

registerForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const username = registerUsername.value.trim();
  const password = registerPassword.value;
  if (!username || !password) {
    setError(registerError, 'Username va parol kiritilishi shart!');
    return;
  }
  if (password.length < 4) {
    setError(registerError, 'Parol kamida 4 ta belgidan iborat bo\'lishi kerak!');
    return;
  }
  setError(registerError, '');
  registerSubmitBtn.disabled = true;

  try {
    const res = await api.register(username, password);
    if (res.id) {
      showToast('Ro\'yxatdan muvaffaqiyatli o\'tildi. Endi tushiring...', 'success');
      setTimeout(() => {
        showTab('login');
        registerUsername.value = '';
        registerPassword.value = '';
        loginUsername.value = username;
        loginPassword.focus();
        window.location.href = 'login.html';
      }, 600);
    } else {
      setError(registerError, res.message || 'Ro\'yxatdan o\'tishda xatolik!');
    }
  } catch (err) {
    console.error('Register error:', err);
    const msg = err.data && err.data.message ? err.data.message : (err.message || 'Xatolik yuz berdi');
    setError(registerError, msg);
  } finally {
    registerSubmitBtn.disabled = false;
  }
});

const showToast = (msg, type = 'success') => {
  toastMessage.textContent = msg;
  successToast.className = `fixed top-4 right-4 px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 text-sm ${type === 'success' ? 'bg-green-50 border border-green-200 text-green-700' : 'bg-red-50 border border-red-200 text-red-700'}`;
  successToast.classList.remove('hidden');
  setTimeout(() => successToast.classList.add('hidden'), 4000);
};
