/**
 * Recall Popup Script.
 * Supports:
 * 1. Remember Page Text (DOM / selection)
 * 2. Remember Screenshot (captureVisibleTab + pytesseract OCR on backend)
 */

document.addEventListener('DOMContentLoaded', async () => {
  const pageTitleEl = document.getElementById('page-title');
  const pageUrlEl = document.getElementById('page-url');
  const selectionBanner = document.getElementById('selection-banner');
  const saveBtn = document.getElementById('save-btn');
  const btnText = document.getElementById('btn-text');
  const spinner = document.getElementById('spinner');

  const screenshotBtn = document.getElementById('screenshot-btn');
  const screenshotBtnText = document.getElementById('screenshot-btn-text');
  const screenshotSpinner = document.getElementById('screenshot-spinner');

  const statusCard = document.getElementById('status-card');
  const statusTitle = document.getElementById('status-title');
  const statusDetails = document.getElementById('status-details');
  const errorCard = document.getElementById('error-card');
  const errorText = document.getElementById('error-text');
  const authPanel = document.getElementById('auth-panel');
  const actions = document.getElementById('actions');
  const loginBtn = document.getElementById('login-btn');
  const loginUsername = document.getElementById('login-username');
  const loginPassword = document.getElementById('login-password');
  const loginError = document.getElementById('login-error');

  let activeTab = null;
  let pageData = null;

  const stored = await chrome.storage.local.get(['recallToken', 'recallUser']);
  if (stored.recallToken) {
    authPanel.classList.add('hidden');
    actions.classList.remove('hidden');
  }

  loginBtn.addEventListener('click', () => {
    loginBtn.disabled = true;
    loginError.classList.add('hidden');
    chrome.runtime.sendMessage({
      action: 'LOGIN',
      username: loginUsername.value.trim(),
      password: loginPassword.value,
    }, (response) => {
      loginBtn.disabled = false;
      if (response?.success) {
        authPanel.classList.add('hidden');
        actions.classList.remove('hidden');
      } else {
        loginError.textContent = response?.error || 'Login failed.';
        loginError.classList.remove('hidden');
      }
    });
  });

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  activeTab = tab;

  if (activeTab) {
    pageTitleEl.textContent = activeTab.title || 'Untitled Page';
    pageUrlEl.textContent = activeTab.url || '';

    try {
      pageData = await chrome.tabs.sendMessage(activeTab.id, { action: 'GET_PAGE_CONTENT' });
      if (pageData && pageData.isSelection) {
        selectionBanner.classList.remove('hidden');
        btnText.textContent = '✂ Remember Selected Text';
      }
    } catch (e) {
      console.log('Content script not accessible:', e);
    }
  }

  // 1. Text Save Handler
  saveBtn.addEventListener('click', async () => {
    saveBtn.disabled = true;
    screenshotBtn.disabled = true;
    spinner.classList.remove('hidden');
    btnText.textContent = 'Saving...';
    statusCard.classList.add('hidden');
    errorCard.classList.add('hidden');

    let title = activeTab?.title || 'Web Memory';
    let url = activeTab?.url || '';
    let content = pageData?.content || `Saved webpage link: ${url}`;

    if (pageData?.isSelection) {
      title = `${title} (Excerpt)`;
    }

    const payload = {
      title,
      raw_content: content,
      source_type: 'webpage',
      source_url: url,
    };

    chrome.runtime.sendMessage({ action: 'SAVE_MEMORY', payload }, (response) => {
      spinner.classList.add('hidden');
      saveBtn.disabled = false;
      screenshotBtn.disabled = false;

      if (response && response.success) {
        btnText.textContent = 'Saved!';
        statusCard.classList.remove('hidden');
        statusTitle.textContent = 'Page Text Saved!';
        statusDetails.textContent = 'Vectorized into Recall database';
        setTimeout(() => window.close(), 2000);
      } else {
        btnText.textContent = 'Try Again';
        errorCard.classList.remove('hidden');
        errorText.textContent = response?.error || 'Backend connection failed';
      }
    });
  });

  // 2. Screenshot Capture & OCR Handler
  screenshotBtn.addEventListener('click', async () => {
    saveBtn.disabled = true;
    screenshotBtn.disabled = true;
    screenshotSpinner.classList.remove('hidden');
    screenshotBtnText.textContent = 'Capturing & OCR...';
    statusCard.classList.add('hidden');
    errorCard.classList.add('hidden');

    chrome.runtime.sendMessage({ action: 'CAPTURE_SCREENSHOT' }, (response) => {
      screenshotSpinner.classList.add('hidden');
      saveBtn.disabled = false;
      screenshotBtn.disabled = false;

      if (response && response.success) {
        screenshotBtnText.textContent = 'Captured!';
        statusCard.classList.remove('hidden');
        statusTitle.textContent = 'Screenshot & OCR Saved!';
        statusDetails.textContent = 'Embedded into 384-d vector space';
        setTimeout(() => window.close(), 2200);
      } else {
        screenshotBtnText.textContent = 'Try Again';
        errorCard.classList.remove('hidden');
        errorText.textContent = response?.error || 'Screenshot OCR failed';
      }
    });
  });
});
