# Recall Chrome Extension (Manifest V3)

Quick-capture extension for the Recall personal AI memory system.

## Features
- **Toolbar Icon & Popup**: One-click capture of the active webpage title, URL, and text.
- **Right-Click Context Menu**: Highlight any text on any website, right click -> **"Remember this with Recall"**.
- **Backend Communication**: Directly dispatches to Django `/api/memories/` with `source_type=webpage`.

## Installation in Chrome / Brave / Edge

1. Open Chrome and navigate to:
   `chrome://extensions/`
2. Enable **Developer mode** (toggle in the top-right corner).
3. Click **Load unpacked** in the top-left.
4. Select this directory:
   `C:\Users\manya\Desktop\recall\extension`
5. The **Recall** extension icon will appear in your browser toolbar!
