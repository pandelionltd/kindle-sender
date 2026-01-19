# Kindle Sender - Self-Hosted Article to Kindle Solution

A self-hosted alternative to Instapaper that lets you send web articles to your Kindle with one click.

## Features

- **Browser Extension**: One-click to send any article to your Kindle
- **Reading Queue**: Save articles for later batch sending
- **Article Extraction**: Automatically extracts clean article content
- **EPUB Format**: Converts to Kindle-optimized EPUB format
- **Self-Hosted**: Full control over your data

## Quick Start

### 1. Set Up Your Kindle Email

1. Go to [Amazon's Manage Your Content and Devices](https://www.amazon.com/hz/mycd/digital-console/contentlist/pdocs)
2. Go to **Preferences** → **Personal Document Settings**
3. Note your Kindle email (e.g., `yourname_abc123@kindle.com`)
4. Under **Approved Personal Document E-mail List**, add the email you'll send from

### 2. Configure the Server

```bash
cd server

# Copy the example environment file
cp .env.example .env

# Edit .env with your settings:
# - SMTP credentials (for Gmail, use an App Password)
# - Your Kindle email address
```

**Gmail Setup (recommended):**
1. Enable 2-Factor Authentication on your Google account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a new app password for "Mail"
4. Use this password in your `.env` file

### 3. Install & Run the Server

```bash
cd server

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

The server will start at `http://localhost:5123`

### 4. Install the Browser Extension

**Chrome:**
1. Open `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `extension` folder

**Firefox:**
1. Open `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Select any file in the `extension` folder

### 5. Use It!

1. Navigate to any article you want to read
2. Click the Kindle Sender extension icon
3. Click "Send to Kindle Now" or "Add to Reading Queue"

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check server status |
| `/send` | POST | Send article to Kindle immediately |
| `/queue` | GET | Get queued articles |
| `/queue` | POST | Add article to queue |
| `/queue/send` | POST | Send all queued articles |
| `/queue/clear` | DELETE | Clear the queue |
| `/preview` | POST | Preview extracted article |

## Configuration Options

### Environment Variables (`.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_SERVER` | SMTP server address | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USERNAME` | Your email address | - |
| `SMTP_PASSWORD` | Email password/app password | - |
| `KINDLE_EMAIL` | Your Kindle email | - |
| `SERVER_PORT` | Server port | `5123` |

## Running as a Service (Linux)

Create `/etc/systemd/system/kindle-sender.service`:

```ini
[Unit]
Description=Kindle Sender Server
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/kindle-sender/server
ExecStart=/path/to/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable kindle-sender
sudo systemctl start kindle-sender
```

## Troubleshooting

**"Server Offline" in extension**
- Make sure the server is running (`python app.py`)
- Check the server URL in extension settings matches

**"Email configuration incomplete"**
- Verify all SMTP settings in `.env`
- For Gmail, make sure you're using an App Password

**Articles not arriving on Kindle**
- Check your Kindle's approved email list includes your sender email
- Documents may take a few minutes to sync
- Make sure your Kindle is connected to WiFi

## Privacy & Data

- All processing happens locally on your computer
- No data is sent to any third-party service
- Articles are temporarily stored only during processing
- Your reading queue is stored in memory (clears on server restart)

## License

MIT License - Use freely for personal or commercial purposes.
