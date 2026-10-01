/**
 * Recall Background Service Worker (Manifest V3).
 * Supports:
 * - Text & Webpage capture via context menu
 * - Screenshot capture via chrome.tabs.captureVisibleTab() + backend OCR
 */

const BASE_API = 'http://127.0.0.1:8000';

// Register context menu items on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'recall-remember-text',
    title: 'Remember this (text / selection)',
    contexts: ['page', 'selection'],
  });

  chrome.contextMenus.create({
    id: 'recall-remember-screenshot',
    title: 'Remember this (screenshot)',
    contexts: ['page', 'image'],
  });
});

// Context Menu Click Handler
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (!tab || !tab.id) return;

  if (info.menuItemId === 'recall-remember-text') {
    await handleTextCapture(info, tab);
  } else if (info.menuItemId === 'recall-remember-screenshot') {
    await handleScreenshotCapture(tab);
  }
});

async function handleTextCapture(info, tab) {
  try {
    const response = await chrome.tabs.sendMessage(tab.id, { action: 'GET_PAGE_CONTENT' }).catch(() => null);
    let content = info.selectionText ? info.selectionText.trim() : (response?.content || '');
    let title = info.selectionText ? `${tab.title} (Selection)` : (response?.title || tab.title);

    await postMemory(`${BASE_API}/api/memories/`, {
      title,
      raw_content: content || `Saved page from ${tab.url}`,
      source_type: 'webpage',
      source_url: tab.url,
    });

    flashBadge(tab.id, '✓', '#10b981');
  } catch (err) {
    console.error('Text capture failed:', err);
    flashBadge(tab.id, '!', '#ef4444');
  }
}

async function handleScreenshotCapture(tab) {
  try {
    // 1. Capture visible tab as PNG base64
    const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: 'png' });

    // 2. Post to /api/memories/screenshot/
    await postMemory(`${BASE_API}/api/memories/screenshot/`, {
      image_base64: dataUrl,
      title: `${tab.title || 'Web'} Screenshot`,
      source_url: tab.url,
    });

    flashBadge(tab.id, '✓', '#8b5cf6');
  } catch (err) {
    console.error('Screenshot capture failed:', err);
    flashBadge(tab.id, '!', '#ef4444');
  }
}

async function postMemory(url, payload) {
  const stored = await chrome.storage.local.get('recallToken');
  if (!stored.recallToken) {
    throw new Error('Log in to Recall from the extension before saving.');
  }

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Token ${stored.recallToken}`,
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Server returned ${res.status}: ${text}`);
  }

  const resData = await res.json();
  await chrome.storage.local.set({
    lastSaved: {
      title: payload.title,
      time: new Date().toLocaleTimeString(),
      type: payload.source_type || 'screenshot',
    },
  });
  return resData;
}

function flashBadge(tabId, text, color) {
  chrome.action.setBadgeText({ tabId, text });
  chrome.action.setBadgeBackgroundColor({ tabId, color });
  setTimeout(() => {
    chrome.action.setBadgeText({ tabId, text: '' });
  }, 3000);
}

// Listener for popup actions
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'LOGIN') {
    fetch(`${BASE_API}/api/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: request.username, password: request.password }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.non_field_errors?.[0] || 'Invalid username or password.');
        await chrome.storage.local.set({ recallToken: data.token, recallUser: data.user });
        sendResponse({ success: true, user: data.user });
      })
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true;
  } else if (request.action === 'SAVE_MEMORY') {
    postMemory(`${BASE_API}/api/memories/`, request.payload)
      .then((data) => sendResponse({ success: true, data }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true;
  } else if (request.action === 'CAPTURE_SCREENSHOT') {
    chrome.tabs.query({ active: true, currentWindow: true }).then(([activeTab]) => {
      if (!activeTab) {
        sendResponse({ success: false, error: 'No active tab' });
        return;
      }
      chrome.tabs.captureVisibleTab(activeTab.windowId, { format: 'png' }).then((dataUrl) => {
        postMemory(`${BASE_API}/api/memories/screenshot/`, {
          image_base64: dataUrl,
          title: `${activeTab.title || 'Web'} Screenshot`,
          source_url: activeTab.url,
        })
          .then((data) => sendResponse({ success: true, data }))
          .catch((err) => sendResponse({ success: false, error: err.message }));
      }).catch((err) => sendResponse({ success: false, error: err.message }));
    });
    return true;
  }
});
