document.addEventListener('DOMContentLoaded', () => {
    const downloadForm = document.getElementById('downloadForm');
    const videoUrlInput = document.getElementById('videoUrl');
    const fetchBtn = document.getElementById('fetchBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const errorMessage = document.getElementById('errorMessage');
    const videoInfo = document.getElementById('videoInfo');
    const downloadProgress = document.getElementById('downloadProgress');
    const successMessage = document.getElementById('successMessage');
    
    // Video information elements
    const videoThumbnail = document.getElementById('videoThumbnail');
    const videoTitle = document.getElementById('videoTitle');
    const videoAuthor = document.getElementById('videoAuthor');
    const videoDuration = document.getElementById('videoDuration');
    const videoViews = document.getElementById('videoViews');
    const videoFormats = document.getElementById('videoFormats');
    const audioFormats = document.getElementById('audioFormats');
    const noVideoFormats = document.getElementById('noVideoFormats');
    const noAudioFormats = document.getElementById('noAudioFormats');
    
    // Download elements
    const progressBar = document.querySelector('.progress-bar');
    const downloadStatus = document.getElementById('downloadStatus');
    const downloadLink = document.getElementById('downloadLink');
    
    // Store the current video URL
    let currentVideoUrl = '';
    
    // Format numbers with commas
    function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }
    
    // Handle form submission
    downloadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const videoUrl = videoUrlInput.value.trim();
        
        if (!videoUrl) {
            showError('Please enter a YouTube URL');
            return;
        }
        
        fetchVideoInfo(videoUrl);
    });
    
    // Fetch video information
    function fetchVideoInfo(videoUrl) {
        // Reset UI
        hideError();
        resetDownloadState();
        showLoading();
        hideVideoInfo();
        
        // Store current URL
        currentVideoUrl = videoUrl;
        
        // Send request to get video info
        const formData = new FormData();
        formData.append('video_url', videoUrl);
        
        fetch('/get_video_info', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            displayVideoInfo(data);
        })
        .catch(error => {
            hideLoading();
            showError('Failed to fetch video information: ' + error.message);
        });
    }
    
    // Display video information
    function displayVideoInfo(data) {
        // Set basic video info
        videoThumbnail.src = data.thumbnail_url;
        videoTitle.textContent = data.title;
        videoAuthor.textContent = 'By ' + data.author;
        videoDuration.textContent = data.duration;
        videoViews.textContent = formatNumber(data.views) + ' views';
        
        // Clear format tables
        videoFormats.innerHTML = '';
        audioFormats.innerHTML = '';
        
        // Filter and display formats
        const videoFormatsData = data.formats.filter(format => format.type === 'video');
        const audioFormatsData = data.formats.filter(format => format.type === 'audio');
        
        // Display video formats
        if (videoFormatsData.length > 0) {
            videoFormatsData.forEach(format => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${format.resolution} ${format.fps ? `(${format.fps}fps)` : ''}</td>
                    <td>${format.mime_type}</td>
                    <td>${format.file_size}</td>
                    <td>
                        <button class="btn btn-primary btn-sm download-btn" 
                                data-itag="${format.itag}" 
                                data-type="video">
                            <i class="fas fa-download me-1"></i> Download
                        </button>
                    </td>
                `;
                videoFormats.appendChild(row);
            });
            noVideoFormats.classList.add('d-none');
        } else {
            noVideoFormats.classList.remove('d-none');
        }
        
        // Display audio formats
        if (audioFormatsData.length > 0) {
            audioFormatsData.forEach(format => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${format.abr || 'Unknown'}</td>
                    <td>${format.mime_type}</td>
                    <td>${format.file_size}</td>
                    <td>
                        <button class="btn btn-success btn-sm download-btn" 
                                data-itag="${format.itag}" 
                                data-type="audio">
                            <i class="fas fa-download me-1"></i> Download
                        </button>
                    </td>
                `;
                audioFormats.appendChild(row);
            });
            noAudioFormats.classList.add('d-none');
        } else {
            noAudioFormats.classList.remove('d-none');
        }
        
        // Add event listeners to download buttons
        document.querySelectorAll('.download-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const itag = e.target.closest('.download-btn').dataset.itag;
                const fileType = e.target.closest('.download-btn').dataset.type;
                downloadVideo(currentVideoUrl, itag, fileType);
            });
        });
        
        // Show video info section
        showVideoInfo();
    }
    
    // Download video
    function downloadVideo(videoUrl, itag, fileType) {
        // Reset and show download progress
        resetDownloadState();
        showDownloadProgress();
        
        // Simulate progress (since we can't get real progress from the server)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress > 95) {
                progress = 95; // We'll set it to 100% when download completes
                clearInterval(progressInterval);
            }
            updateProgress(progress);
        }, 300);
        
        // Send download request
        const formData = new FormData();
        formData.append('video_url', videoUrl);
        formData.append('itag', itag);
        formData.append('file_type', fileType);
        
        fetch('/download', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            clearInterval(progressInterval);
            
            if (data.error) {
                updateProgress(0);
                showError(data.error);
                hideDownloadProgress();
                return;
            }
            
            // Complete progress
            updateProgress(100);
            downloadStatus.textContent = 'Download complete!';
            
            // Show success message with download link
            downloadLink.href = data.download_url;
            hideDownloadProgress();
            showSuccessMessage();
            
            // Clean up temp files after download
            setTimeout(() => {
                fetch('/clear_temp')
                    .catch(error => console.error('Error clearing temp files:', error));
            }, 3000);
        })
        .catch(error => {
            clearInterval(progressInterval);
            updateProgress(0);
            hideDownloadProgress();
            showError('Download failed: ' + error.message);
        });
    }
    
    // Update progress bar
    function updateProgress(percent) {
        const roundedPercent = Math.round(percent);
        progressBar.style.width = roundedPercent + '%';
        progressBar.setAttribute('aria-valuenow', roundedPercent);
        progressBar.textContent = roundedPercent + '%';
        
        if (roundedPercent < 100) {
            downloadStatus.textContent = 'Downloading... ' + roundedPercent + '%';
        }
    }
    
    // UI Helper Functions
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('d-none');
    }
    
    function hideError() {
        errorMessage.classList.add('d-none');
        errorMessage.textContent = '';
    }
    
    function showLoading() {
        loadingSpinner.classList.remove('d-none');
        fetchBtn.disabled = true;
    }
    
    function hideLoading() {
        loadingSpinner.classList.add('d-none');
        fetchBtn.disabled = false;
    }
    
    function showVideoInfo() {
        videoInfo.classList.remove('d-none');
    }
    
    function hideVideoInfo() {
        videoInfo.classList.add('d-none');
    }
    
    function showDownloadProgress() {
        downloadProgress.classList.remove('d-none');
    }
    
    function hideDownloadProgress() {
        downloadProgress.classList.add('d-none');
    }
    
    function showSuccessMessage() {
        successMessage.classList.remove('d-none');
    }
    
    function hideSuccessMessage() {
        successMessage.classList.add('d-none');
    }
    
    function resetDownloadState() {
        hideDownloadProgress();
        hideSuccessMessage();
        updateProgress(0);
        downloadStatus.textContent = 'Preparing download...';
    }
    
    // Auto-focus the URL input field
    videoUrlInput.focus();
});
