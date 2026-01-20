#!/usr/bin/env python3
"""
Kindle Sender - Self-hosted article to Kindle service
Receives article URLs, extracts content, converts to EPUB, and sends to Kindle.
"""

import os
import smtplib
import tempfile
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from newspaper import Article
from ebooklib import epub
from bs4 import BeautifulSoup
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["*"])  # Allow browser extension to connect

# Configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
KINDLE_EMAIL = os.getenv('KINDLE_EMAIL')
SERVER_PORT = int(os.getenv('SERVER_PORT', 5123))
FROM_EMAIL = os.getenv('FROM_EMAIL')

# Store for queued articles (in production, use a database)
article_queue = []


def extract_article(url: str) -> dict:
    """Extract article content from URL using newspaper3k."""
    try:
        article = Article(url)
        article.download()
        article.parse()

        return {
            'title': article.title or 'Untitled Article',
            'authors': article.authors,
            'publish_date': str(article.publish_date) if article.publish_date else None,
            'text': article.text,
            'html': article.html,
            'top_image': article.top_image,
            'url': url,
            'success': True
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'url': url
        }


def create_epub(article_data: dict) -> str:
    """Create an EPUB file from article data."""
    book = epub.EpubBook()

    # Set metadata
    title = article_data.get('title', 'Untitled')
    book.set_identifier(f"kindle-sender-{datetime.now().timestamp()}")
    book.set_title(title)
    book.set_language('en')

    authors = article_data.get('authors', [])
    if authors:
        for author in authors:
            book.add_author(author)
    else:
        book.add_author('Unknown')

    # Create chapter content
    content = article_data.get('text', '')
    html_content = f"""
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: Georgia, serif; line-height: 1.6; padding: 20px; }}
            h1 {{ margin-bottom: 10px; }}
            .meta {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
            .content {{ text-align: justify; }}
            p {{ margin-bottom: 1em; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div class="meta">
            <p>Source: <a href="{article_data.get('url', '')}">{article_data.get('url', '')}</a></p>
            {f"<p>Authors: {', '.join(authors)}</p>" if authors else ""}
            {f"<p>Published: {article_data.get('publish_date')}</p>" if article_data.get('publish_date') else ""}
        </div>
        <div class="content">
            {''.join(f'<p>{para}</p>' for para in content.split('\n\n') if para.strip())}
        </div>
    </body>
    </html>
    """

    # Create chapter
    chapter = epub.EpubHtml(title=title, file_name='content.xhtml', lang='en')
    chapter.content = html_content
    book.add_item(chapter)

    # Add navigation
    book.toc = [epub.Link('content.xhtml', title, 'content')]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define spine
    book.spine = ['nav', chapter]

    # Save to temp file
    temp_dir = tempfile.mkdtemp()
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    epub_path = os.path.join(temp_dir, f"{safe_title[:50]}.epub")
    epub.write_epub(epub_path, book)

    return epub_path


def send_to_kindle(epub_path: str, title: str) -> dict:
    """Send EPUB file to Kindle via email."""
    if not all([SMTP_USERNAME, SMTP_PASSWORD, KINDLE_EMAIL]):
        return {
            'success': False,
            'error': 'Email configuration incomplete. Please set SMTP_USERNAME, SMTP_PASSWORD, and KINDLE_EMAIL in .env'
        }

    try:
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL or SMTP_USERNAME
        msg['To'] = KINDLE_EMAIL
        msg['Subject'] = f'Kindle: {title}'

        # Add body
        body = f"Article: {title}\nSent via Kindle Sender"
        msg.attach(MIMEText(body, 'plain'))

        # Attach EPUB file
        with open(epub_path, 'rb') as attachment:
            part = MIMEBase('application', 'epub+zip')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{os.path.basename(epub_path)}"'
            )
            msg.attach(part)

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        return {'success': True, 'message': f'Sent "{title}" to Kindle'}

    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        # Clean up temp file
        if os.path.exists(epub_path):
            os.remove(epub_path)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'kindle_configured': bool(KINDLE_EMAIL),
        'smtp_configured': bool(SMTP_USERNAME and SMTP_PASSWORD)
    })


@app.route('/send', methods=['POST'])
def send_article():
    """Extract article and send to Kindle immediately."""
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400

    # Extract article
    article_data = extract_article(url)
    if not article_data.get('success'):
        return jsonify(article_data), 400

    # Create EPUB
    try:
        epub_path = create_epub(article_data)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to create EPUB: {str(e)}'}), 500

    # Send to Kindle
    result = send_to_kindle(epub_path, article_data['title'])

    if result['success']:
        return jsonify({
            'success': True,
            'message': result['message'],
            'title': article_data['title']
        })
    else:
        return jsonify(result), 500


@app.route('/queue', methods=['POST'])
def queue_article():
    """Add article to queue for batch sending later."""
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400

    # Extract article metadata
    article_data = extract_article(url)
    if not article_data.get('success'):
        return jsonify(article_data), 400

    article_queue.append({
        'url': url,
        'title': article_data['title'],
        'added_at': datetime.now().isoformat()
    })

    return jsonify({
        'success': True,
        'message': f'Added "{article_data["title"]}" to queue',
        'queue_length': len(article_queue)
    })


@app.route('/queue', methods=['GET'])
def get_queue():
    """Get current queue of articles."""
    return jsonify({
        'success': True,
        'queue': article_queue,
        'count': len(article_queue)
    })


@app.route('/queue/send', methods=['POST'])
def send_queue():
    """Send all queued articles to Kindle."""
    if not article_queue:
        return jsonify({'success': False, 'error': 'Queue is empty'}), 400

    results = []
    for item in article_queue[:]:  # Copy list to iterate safely
        article_data = extract_article(item['url'])
        if article_data.get('success'):
            epub_path = create_epub(article_data)
            result = send_to_kindle(epub_path, article_data['title'])
            results.append({
                'title': article_data['title'],
                'success': result['success'],
                'error': result.get('error')
            })
            if result['success']:
                article_queue.remove(item)
        else:
            results.append({
                'url': item['url'],
                'success': False,
                'error': article_data.get('error')
            })

    return jsonify({
        'success': True,
        'results': results,
        'remaining_in_queue': len(article_queue)
    })


@app.route('/queue/clear', methods=['DELETE'])
def clear_queue():
    """Clear the article queue."""
    article_queue.clear()
    return jsonify({'success': True, 'message': 'Queue cleared'})


@app.route('/preview', methods=['POST'])
def preview_article():
    """Preview extracted article without sending."""
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400

    article_data = extract_article(url)
    return jsonify(article_data)


if __name__ == '__main__':
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║           Kindle Sender - Self-Hosted Server              ║
╠═══════════════════════════════════════════════════════════╣
║  Server running at: http://localhost:{SERVER_PORT}                 ║
║  Kindle email: {KINDLE_EMAIL or 'NOT CONFIGURED'}
║  SMTP configured: {'Yes' if SMTP_USERNAME and SMTP_PASSWORD else 'No'}
╚═══════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=True)
