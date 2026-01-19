// Configuration
const DEFAULT_SERVER_URL = 'http://localhost:5123';

// Get server URL from storage or use default
async function getServerUrl() {
  const result = await chrome.storage.sync.get(['serverUrl']);
  return result.serverUrl || DEFAULT_SERVER_URL;
}

// Get current tab info
async function getCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

// Update UI with page info
async function updatePageInfo() {
  const tab = await getCurrentTab();
  document.getElementById('pageTitle').textContent = tab.title || 'Unknown Page';
  document.getElementById('pageUrl').textContent = tab.url || '';
}

// Check server status
async function checkServerStatus() {
  const serverUrl = await getServerUrl();
  const statusDot = document.getElementById('serverStatus');
  const statusText = document.getElementById('serverStatusText');

  try {
    const response = await fetch(`${serverUrl}/health`, { method: 'GET' });
    if (response.ok) {
      const data = await response.json();
      statusDot.classList.add('online');
      statusDot.classList.remove('offline');
      statusText.textContent = 'Server Online';

      // Enable buttons
      document.getElementById('sendNow').disabled = false;
      document.getElementById('addToQueue').disabled = false;
    } else {
      throw new Error('Server error');
    }
  } catch (error) {
    statusDot.classList.add('offline');
    statusDot.classList.remove('online');
    statusText.textContent = 'Server Offline';

    // Disable buttons
    document.getElementById('sendNow').disabled = true;
    document.getElementById('addToQueue').disabled = true;
  }
}

// Show status message
function showStatus(message, type) {
  const status = document.getElementById('status');
  status.textContent = message;
  status.className = `status ${type}`;
}

// Update queue info
async function updateQueueInfo() {
  const serverUrl = await getServerUrl();
  try {
    const response = await fetch(`${serverUrl}/queue`);
    if (response.ok) {
      const data = await response.json();
      const queueInfo = document.getElementById('queueInfo');
      const queueCount = document.getElementById('queueCount');

      if (data.count > 0) {
        queueInfo.style.display = 'block';
        queueCount.textContent = data.count;
      } else {
        queueInfo.style.display = 'none';
      }
    }
  } catch (error) {
    console.error('Failed to fetch queue:', error);
  }
}

// Send article to Kindle immediately
async function sendToKindle() {
  const serverUrl = await getServerUrl();
  const tab = await getCurrentTab();

  showStatus('Extracting article and sending to Kindle...', 'loading');
  document.getElementById('sendNow').disabled = true;

  try {
    const response = await fetch(`${serverUrl}/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: tab.url })
    });

    const data = await response.json();

    if (data.success) {
      showStatus(`✓ "${data.title}" sent to Kindle!`, 'success');
    } else {
      showStatus(`✗ Error: ${data.error}`, 'error');
    }
  } catch (error) {
    showStatus(`✗ Failed to connect to server`, 'error');
  } finally {
    document.getElementById('sendNow').disabled = false;
  }
}

// Add article to queue
async function addToQueue() {
  const serverUrl = await getServerUrl();
  const tab = await getCurrentTab();

  showStatus('Adding to queue...', 'loading');
  document.getElementById('addToQueue').disabled = true;

  try {
    const response = await fetch(`${serverUrl}/queue`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: tab.url })
    });

    const data = await response.json();

    if (data.success) {
      showStatus(`✓ Added to queue (${data.queue_length} articles)`, 'success');
      updateQueueInfo();
    } else {
      showStatus(`✗ Error: ${data.error}`, 'error');
    }
  } catch (error) {
    showStatus(`✗ Failed to connect to server`, 'error');
  } finally {
    document.getElementById('addToQueue').disabled = false;
  }
}

// Send all queued articles
async function sendQueue() {
  const serverUrl = await getServerUrl();

  showStatus('Sending queued articles...', 'loading');
  document.getElementById('sendQueue').disabled = true;

  try {
    const response = await fetch(`${serverUrl}/queue/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();

    if (data.success) {
      const successCount = data.results.filter(r => r.success).length;
      showStatus(`✓ Sent ${successCount} articles to Kindle`, 'success');
      updateQueueInfo();
    } else {
      showStatus(`✗ Error: ${data.error}`, 'error');
    }
  } catch (error) {
    showStatus(`✗ Failed to connect to server`, 'error');
  } finally {
    document.getElementById('sendQueue').disabled = false;
  }
}

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  await updatePageInfo();
  await checkServerStatus();
  await updateQueueInfo();

  // Attach event listeners
  document.getElementById('sendNow').addEventListener('click', sendToKindle);
  document.getElementById('addToQueue').addEventListener('click', addToQueue);
  document.getElementById('sendQueue').addEventListener('click', sendQueue);
});
