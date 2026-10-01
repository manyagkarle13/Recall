/**
 * Recall Content Script.
 * Extracts page URL, title, selected text, and body innerText.
 */

// Function to extract text content
function getPageContent() {
  const selection = window.getSelection() ? window.getSelection().toString().trim() : '';
  const title = document.title || window.location.hostname;
  const url = window.location.href;

  // Clean and limit full body text to prevent payload overflow
  let fullText = document.body ? document.body.innerText : '';
  fullText = fullText.replace(/\s+/g, ' ').trim();
  if (fullText.length > 50000) {
    fullText = fullText.substring(0, 50000);
  }

  return {
    title,
    url,
    selectedText: selection,
    fullText,
    content: selection.length > 0 ? selection : fullText,
    isSelection: selection.length > 0,
  };
}

// Listen for messages from popup or background service worker
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'GET_PAGE_CONTENT') {
    const data = getPageContent();
    sendResponse(data);
  }
  return true;
});
