import React, { useState, useEffect } from 'react';
import './App.css';

// Read backend URL from environment variable, fallback to localhost for direct running
const backendUrl = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000"; // Changed

function App() {
  const [productUrl, setProductUrl] = useState('');
  const [currentVideoId, setCurrentVideoId] = useState(null);
  const [currentVideoFilename, setCurrentVideoFilename] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [videoList, setVideoList] = useState([]);

  useEffect(() => {
    fetchVideoList();
    const interval = setInterval(fetchVideoList, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchVideoList = async () => {
    try {
      const response = await fetch(`${backendUrl}/videos/`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setVideoList(data);
    } catch (err) {
      console.error('Error fetching video list:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setCurrentVideoId(null);
    setCurrentVideoFilename(null);
    setStatusMessage('Starting video generation...');

    try {
      const response = await fetch(`${backendUrl}/generate-ad-video/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: productUrl }),
      });

      const data = await response.json();

      if (response.ok) {
        setCurrentVideoId(data.id);
        setCurrentVideoFilename(data.video_filename);
        setStatusMessage('Video generation initiated. Please wait a moment for the video to be ready. It will appear in the list below.');
        setProductUrl('');
        fetchVideoList();
      } else {
        if (response.status === 422 && data.detail && Array.isArray(data.detail)) {
          const validationErrors = data.detail.map(err => `${err.loc.join('.')} - ${err.msg}`).join('; ');
          setError(`Validation Error: ${validationErrors}`);
        } else {
          setError(data.detail || 'An unknown error occurred on the server.');
        }
        setStatusMessage('Video generation failed.');
      }
    } catch (err) {
      console.error('Network error during video generation request:', err);
      setError('Could not connect to the backend server. Please ensure it is running.');
      setStatusMessage('Network error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = (filename) => {
    if (filename) {
      window.open(`${backendUrl}/get-video/${filename}`, '_blank');
    } else {
      setError("No video file to download.");
    }
  };

  const handlePreview = (filename) => {
    if (filename) {
      setCurrentVideoFilename(filename);
      setError(null);
      setStatusMessage('Video selected for preview.');
    } else {
      setError("No video file selected for preview.");
    }
  };

  const handleDelete = async (videoId, videoTitle) => {
    if (window.confirm(`Are you sure you want to delete the video for "${videoTitle}"? This action cannot be undone.`)) {
      try {
        const response = await fetch(`${backendUrl}/videos/${videoId}`, {
          method: 'DELETE',
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        setStatusMessage(`Video "${videoTitle}" deleted successfully.`);
        setError(null);
        fetchVideoList();
        if (currentVideoId === videoId) {
          setCurrentVideoId(null);
          setCurrentVideoFilename(null);
        }
      } catch (err) {
        console.error('Error deleting video:', err);
        setError(`Failed to delete video: ${err.message}`);
      }
    }
  };

  return (
    <div className="app-container">
      <h1 className="app-title">AI Video Ad Generator</h1>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="url-input" className="label">
            Product Page URL:
          </label>
          <input
            type="url"
            id="url-input"
            className="input-field"
            placeholder="e.g., https://www.amazon.in/..."
            value={productUrl}
            onChange={(e) => setProductUrl(e.target.value)}
            required
          />
        </div>
        <button
          type="submit"
          className="submit-button"
          disabled={isLoading}
        >
          {isLoading ? (
            <div className="spinner"></div>
          ) : null}
          {isLoading ? 'Generating Video...' : 'Generate Video Ad'}
        </button>
      </form>

      {statusMessage && <p className="status-message">{statusMessage}</p>}

      {error && (
        <div className="error-message" role="alert">
          <strong>Error:</strong>
          <span>
            {typeof error === 'string'
              ? error
              : (error.msg || (error.detail && error.detail.length > 0 ? error.detail[0].msg : 'An unknown error occurred. Check console for details.'))
            }
          </span>
        </div>
      )}

      {currentVideoFilename && (
        <div className="video-section">
          <h2 className="section-title">Current Video Preview</h2>
          <video
            controls
            src={`${backendUrl}/get-video/${currentVideoFilename}`}
            className="video-player"
            key={currentVideoFilename}
          >
            Your browser does not support the video tag.
          </video>
          <div className="action-buttons">
            <button
              onClick={() => handleDownload(currentVideoFilename)}
              className="download-button"
            >
              Download Current Video
            </button>
          </div>
        </div>
      )}

      <div className="video-list-section">
        <h2 className="section-title">Generated Videos</h2>
        {videoList.length === 0 ? (
          <p>No videos generated yet. Submit a URL above!</p>
        ) : (
          <ul className="video-list">
            {videoList.map((video) => (
              <li key={video.id} className="video-list-item">
                <div className="video-info">
                  <h3>{video.product_title}</h3>
                  <p>Status: <span className={`status-${video.status}`}>{video.status}</span></p>
                  <p>Generated: {new Date(video.created_at).toLocaleString()}</p>
                </div>
                <div className="video-actions">
                  {video.status === 'completed' && video.video_filename ? (
                    <>
                      <button onClick={() => handlePreview(video.video_filename)} className="preview-button">
                        Preview
                      </button>
                      <button onClick={() => handleDownload(video.video_filename)} className="download-button">
                        Download
                      </button>
                      <button
                        onClick={() => handleDelete(video.id, video.product_title)}
                        className="delete-button"
                      >
                        Delete
                      </button>
                    </>
                  ) : video.status === 'failed' ? (
                    <>
                      <span className="no-actions-message">Generation Failed</span>
                      <button
                        onClick={() => handleDelete(video.id, video.product_title)}
                        className="delete-button"
                      >
                        Delete
                      </button>
                    </>
                  ) : (
                    <span className="no-actions-message">Processing...</span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default App;