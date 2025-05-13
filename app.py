import os
import logging
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from utils import get_video_info, download_video
import tempfile
import shutil
import uuid
from werkzeug.middleware.proxy_fix import ProxyFix

# Create temporary directory to store downloads
temp_dir = os.environ.get('TEMP_DIR', 'temp')
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir, exist_ok=True)

# Set up app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "youtube-downloader-secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure logger
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')

@app.route('/get_video_info', methods=['POST'])
def fetch_video_info():
    """Get information about a YouTube video."""
    video_url = request.form.get('video_url', '')
    
    if not video_url:
        return jsonify({'error': 'Please enter a YouTube URL'}), 400
    
    try:
        video_info = get_video_info(video_url)
        if 'error' in video_info:
            return jsonify(video_info), 400
        return jsonify(video_info)
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/download', methods=['POST'])
def download():
    """Download a YouTube video."""
    video_url = request.form.get('video_url', '')
    itag = request.form.get('itag', '')
    file_type = request.form.get('file_type', '')
    
    if not video_url or not itag:
        return jsonify({'error': 'Missing video URL or format selection'}), 400
    
    try:
        # Generate a unique session ID for this download
        session_id = str(uuid.uuid4())
        session['download_id'] = session_id
        
        # Create a temporary directory for this download
        download_dir = os.path.join(os.environ.get('TEMP_DIR', 'temp'), session_id)
        if not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)
        
        # Download the video
        download_path = download_video(video_url, itag, download_dir, file_type)
        
        if not download_path:
            return jsonify({'error': 'Failed to download video'}), 500
        
        # Store the download path in the session
        session['download_path'] = download_path
        
        return jsonify({
            'success': True,
            'message': 'Download completed',
            'download_url': url_for('serve_download')
        })
    
    except Exception as e:
        logger.error(f"Error during download: {str(e)}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

@app.route('/serve_download')
def serve_download():
    """Serve the downloaded file to the user."""
    download_path = session.get('download_path', None)
    
    if not download_path or not os.path.exists(download_path):
        flash('Download expired or not found. Please try again.', 'error')
        return redirect(url_for('index'))
    
    try:
        filename = os.path.basename(download_path)
        return send_file(
            download_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        logger.error(f"Error serving download: {str(e)}")
        flash(f'Error retrieving your download: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/clear_temp')
def clear_temp():
    """Clear temporary files (for maintenance)."""
    try:
        # Only clear the temp directory for the current session
        session_id = session.get('download_id')
        if session_id:
            download_dir = os.path.join(os.environ.get('TEMP_DIR', 'temp'), session_id)
            if os.path.exists(download_dir):
                shutil.rmtree(download_dir)
            session.pop('download_id', None)
            session.pop('download_path', None)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error clearing temp files: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Clean up function to be called periodically or on exit
@app.teardown_appcontext
def cleanup_temp_files(exception=None):
    """Clean up temporary files when the application context ends."""
    try:
        temp_base_dir = os.environ.get('TEMP_DIR', 'temp')
        # Only delete directories older than 1 hour
        # In a production app, you would implement a more sophisticated cleanup
        # This is disabled for now to prevent issues with file downloads
        pass
    except Exception as e:
        logger.error(f"Error in cleanup: {str(e)}")
