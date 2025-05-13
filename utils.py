import os
import logging
from pytubefix import YouTube
from pytubefix.exceptions import PytubeFixError, RegexMatchError
import re
import time

logger = logging.getLogger(__name__)

def is_valid_youtube_url(url):
    """Check if the URL is a valid YouTube URL."""
    # More permissive regex that matches various YouTube URL formats
    youtube_regex = (
        r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|'
        r'youtube\.com/v/|youtube\.com/watch\?.*v=|youtube\.com/shorts/)'
        r'([a-zA-Z0-9_-]{11}).*'
    )
    match = re.match(youtube_regex, url)
    
    # If we didn't match, try to extract the video ID directly and validate its format
    if not match and 'youtube.com' in url and 'v=' in url:
        try:
            video_id = url.split('v=')[1].split('&')[0]
            if len(video_id) == 11:
                return True
        except IndexError:
            pass
            
    return bool(match)

def format_duration(seconds):
    """Format duration in seconds to HH:MM:SS."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def format_file_size(bytes_size):
    """Format file size from bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"

def get_video_info(url):
    """Get information about a YouTube video."""
    if not is_valid_youtube_url(url):
        return {'error': 'Invalid YouTube URL. Please enter a valid YouTube video URL.'}
    
    try:
        # Add user agent and other parameters to avoid blocking on cloud platforms
        from random import choice
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        
        # Create YouTube object with additional parameters to improve success rate and avoid blocking
        yt = YouTube(
            url, 
            use_oauth=False, 
            allow_oauth_cache=True,
            use_innertube=True,  # Use innertube API which is more reliable
            user_agent=choice(user_agents)  # Rotate user agents to avoid blocking
        )
        
        # Wait a moment to ensure metadata is loaded
        import time
        time.sleep(1)
        
        # Check if we got a title, if not, the video info wasn't properly fetched
        if not yt.title:
            logger.error("Failed to get video title")
            return {'error': 'Could not retrieve video information. Please try again or try a different video.'}
            
        # Get basic video info
        video_info = {
            'title': yt.title,
            'author': yt.author,
            'thumbnail_url': yt.thumbnail_url,
            'duration': format_duration(yt.length),
            'views': yt.views,
            'formats': []
        }
        
        # Get video formats
        video_streams = yt.streams.filter(progressive=True).order_by('resolution').desc()
        audio_streams = yt.streams.filter(only_audio=True).order_by('abr').desc()
        
        # Add video formats
        for stream in video_streams:
            try:
                video_info['formats'].append({
                    'itag': stream.itag,
                    'mime_type': stream.mime_type,
                    'resolution': stream.resolution,
                    'fps': stream.fps,
                    'file_size': format_file_size(stream.filesize),
                    'type': 'video',
                    'extension': stream.mime_type.split('/')[-1]
                })
            except Exception as e:
                logger.warning(f"Skipping video stream {stream.itag} due to error: {str(e)}")
        
        # Add audio formats
        for stream in audio_streams:
            try:
                video_info['formats'].append({
                    'itag': stream.itag,
                    'mime_type': stream.mime_type,
                    'abr': stream.abr,
                    'file_size': format_file_size(stream.filesize),
                    'type': 'audio',
                    'extension': stream.mime_type.split('/')[-1]
                })
            except Exception as e:
                logger.warning(f"Skipping audio stream {stream.itag} due to error: {str(e)}")
        
        # If no formats were found, return an error
        if not video_info['formats']:
            return {'error': 'No downloadable formats found for this video. It may be protected or region-restricted.'}
            
        return video_info
    
    except RegexMatchError:
        return {'error': 'Invalid YouTube URL. The provided URL does not match a YouTube video.'}
    except PytubeFixError as e:
        logger.error(f"PyTubeFix error: {str(e)}")
        return {'error': f'Error processing YouTube video: {str(e)}'}
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {'error': f'An unexpected error occurred: {str(e)}'}

def download_video(url, itag, download_dir, file_type):
    """Download a YouTube video with the specified itag."""
    try:
        # Add user agent and other parameters to avoid blocking on cloud platforms
        from random import choice
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
        
        # Create YouTube object with additional parameters to improve success rate and avoid blocking
        yt = YouTube(
            url, 
            use_oauth=False, 
            allow_oauth_cache=True,
            use_innertube=True,  # Use innertube API which is more reliable
            user_agent=choice(user_agents)  # Rotate user agents to avoid blocking
        )
        
        # Wait a moment to ensure metadata is loaded
        time.sleep(1)
        
        # Get the stream by itag
        stream = yt.streams.get_by_itag(int(itag))
        
        if not stream:
            logger.error(f"Stream with itag {itag} not found")
            return None
        
        # Create a safe filename
        timestamp = int(time.time())
        safe_title = re.sub(r'[^\w\-_\. ]', '_', yt.title)
        
        # Determine the correct file extension
        if file_type == 'audio' and 'audio' in stream.mime_type:
            # For audio, use mp3 extension
            filename = f"{safe_title}_{timestamp}.mp3"
        else:
            # For video, use the mime type's extension
            try:
                extension = stream.mime_type.split('/')[-1]
                filename = f"{safe_title}_{timestamp}.{extension}"
            except (AttributeError, IndexError):
                # Fallback if mime_type is missing or invalid
                filename = f"{safe_title}_{timestamp}.mp4"
        
        file_path = os.path.join(download_dir, filename)
        
        # Download the stream with retries
        max_retries = 3
        retry_count = 0
        download_success = False
        
        while retry_count < max_retries and not download_success:
            try:
                logger.info(f"Downloading {url} with itag {itag} (Attempt {retry_count + 1})")
                stream.download(output_path=download_dir, filename=filename)
                download_success = True
            except Exception as e:
                retry_count += 1
                logger.warning(f"Download attempt {retry_count} failed: {str(e)}")
                if retry_count >= max_retries:
                    raise
                time.sleep(2)  # Wait before retrying
        
        if download_success:
            logger.info(f"Downloaded to {file_path}")
            return file_path
        else:
            return None
    
    except PytubeFixError as e:
        logger.error(f"PyTubeFix error during download: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return None
