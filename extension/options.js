const DEFAULT_SERVER_URL = 'http://localhost:5123';

// Load saved settings
async function loadSettings() {
  const result = await chrome.storage.sync.get(['serverUrl']);
  document.getElementById('serverUrl').value = result.serverUrl || DEFAULT_SERVER_URL;
}

// Save settings
async function saveSettings() {
  const serverUrl = document.getElementById('serverUrl').value || DEFAULT_SERVER_URL;

  await chrome.storage.sync.set({ serverUrl });

  showStatus('saveStatus', '✓ Settings saved!', 'success');
}

// Reset to defaults
async function resetSettings() {
  await chrome.storage.sync.set({ serverUrl: DEFAULT_SERVER_URL });
  document.getElementById('serverUrl').value = DEFAULT_SERVER_URL;
  showStatus('saveStatus', '✓ Reset to defaults', 'success');
}

// Test connection to server
async function testConnection() {
  const serverUrl = document.getElementById('serverUrl').value || DEFAULT_SERVER_URL;

  showStatus('testStatus', 'Testing connection...', 'loading');

  try {
    const response = await fetch(`${serverUrl}/health`);
    if (response.ok) {
      const data = await response.json();
      let message = '✓ Server is online!\n';
      message += data.kindle_configured ? '✓ Kindle email configured' : '✗ Kindle email not configured';
      message += '\n';
      message += data.smtp_configured ? '✓ SMTP configured' : '✗ SMTP not configured';
      showStatus('testStatus', message, 'success');
    } else {
      showStatus('testStatus', '✗ Server returned an error', 'error');
    }
  } catch (error) {
    showStatus('testStatus', '✗ Could not connect to server. Make sure it is running.', 'error');
  }
}

// Show status message
function showStatus(elementId, message, type) {
  const status = document.getElementById(elementId);
  status.textContent = message;
  status.className = `status ${type}`;
  status.style.display = 'block';
  status.style.whiteSpace = 'pre-line';

  if (type === 'success') {
    setTimeout(() => {
      status.style.display = 'none';
    }, 3000);
  }
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();

  document.getElementById('save').addEventListener('click', saveSettings);
  document.getElementById('reset').addEventListener('click', resetSettings);
  document.getElementById('testConnection').addEventListener('click', testConnection);
});
