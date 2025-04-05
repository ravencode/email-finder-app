from flask import Flask, render_template, request, jsonify
from scrapers.email_scraper import EmailScraper
import threading
import time
import json
import os

app = Flask(__name__)
scraper = EmailScraper()

# In-memory storage for results
scan_results = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def scan():
    data = request.get_json()
    urls = data.get('urls', '').strip().split('\n')
    urls = [url.strip() for url in urls if url.strip()]
    
    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400
    
    # Create a unique scan ID based on timestamp
    scan_id = str(int(time.time()))
    
    # Initialize scan data
    scan_results[scan_id] = {
        'status': 'scanning',
        'progress': 0,
        'total': len(urls),
        'completed': 0,
        'results': {}
    }
    
    # Start the scan in a background thread
    threading.Thread(target=perform_scan, args=(scan_id, urls)).start()
    
    return jsonify({'scan_id': scan_id})

def perform_scan(scan_id, urls):
    for i, url in enumerate(urls):
        formatted_url = scraper.format_url(url)
        result = scraper.find_emails_from_site(formatted_url)
        
        # Update scan results
        scan_results[scan_id]['results'][url] = result
        scan_results[scan_id]['completed'] = i + 1
        scan_results[scan_id]['progress'] = int((i + 1) / len(urls) * 100)
    
    # Mark scan as completed
    scan_results[scan_id]['status'] = 'completed'
    
    # Keep scan results for 30 minutes only
    def cleanup_scan():
        time.sleep(1800)  # 30 minutes
        if scan_id in scan_results:
            del scan_results[scan_id]
    
    threading.Thread(target=cleanup_scan).start()

@app.route('/api/scan-status/<scan_id>')
def scan_status(scan_id):
    if scan_id not in scan_results:
        return jsonify({'error': 'Scan not found'}), 404
    
    return jsonify(scan_results[scan_id])

@app.route('/results/<scan_id>')
def results(scan_id):
    if scan_id not in scan_results:
        return render_template('index.html', error='Scan not found or expired')
    
    return render_template('results.html', scan_id=scan_id)

@app.route('/api/export/<scan_id>')
def export_results(scan_id):
    if scan_id not in scan_results:
        return jsonify({'error': 'Scan not found'}), 404
    
    export_type = request.args.get('type', 'json')
    results = scan_results[scan_id]['results']
    
    if export_type == 'json':
        return jsonify(results)
    elif export_type == 'txt':
        output = ""
        for url, data in results.items():
            emails_text = ", ".join(data['emails']) if data['emails'] else 'No email found'
            output += f"{url.ljust(40)}\t{emails_text}\n"
        
        return output, {'Content-Type': 'text/plain; charset=utf-8'}
    else:
        return jsonify({'error': 'Invalid export type'}), 400

if __name__ == '__main__':
    # Use this for local development
    # app.run(debug=True)
    
    # Use this for production
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)