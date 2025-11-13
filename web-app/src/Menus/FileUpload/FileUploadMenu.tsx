import React, { useState } from 'react';
import './FileUploadMenu.css';

interface FileInfo {
  name: string;
  size: number;
  path?: string;
}

interface FileUploadMenuProps {
  isVisible: boolean;
  onClose: () => void;
}

const FileUploadMenu: React.FC<FileUploadMenuProps> = ({ isVisible, onClose }) => {
  const [stlFile, setStlFile] = useState<File | null>(null);
  const [streamlinesFile, setStreamlinesFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<{
    stl_files: FileInfo[];
    streamline_files: FileInfo[];
  }>({ stl_files: [], streamline_files: [] });

  const API_BASE = 'http://localhost:8080';

  if (!isVisible) return null;

  const handleStlFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.name.endsWith('.stl')) {
      setStlFile(file);
      setUploadStatus('');
    } else {
      setUploadStatus('Please select a valid STL file');
    }
  };

  const handleStreamlinesFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.name.endsWith('.json')) {
      setStreamlinesFile(file);
      setUploadStatus('');
    } else {
      setUploadStatus('Please select a valid JSON file');
    }
  };

  const uploadStl = async () => {
    if (!stlFile) {
      setUploadStatus('Please select an STL file first');
      return;
    }

    setIsUploading(true);
    setUploadStatus('Uploading STL file...');

    try {
      const formData = new FormData();
      formData.append('file', stlFile);

      const response = await fetch(`${API_BASE}/upload/stl`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setUploadStatus(`✓ STL uploaded: ${result.filename}`);
        setStlFile(null);
        fetchUploadedFiles();
      } else {
        setUploadStatus(`✗ Upload failed: ${result.detail || 'Unknown error'}`);
      }
    } catch (error) {
      setUploadStatus(`✗ Upload error: ${error}`);
    } finally {
      setIsUploading(false);
    }
  };

  const uploadStreamlines = async () => {
    if (!streamlinesFile) {
      setUploadStatus('Please select a streamlines JSON file first');
      return;
    }

    setIsUploading(true);
    setUploadStatus('Uploading streamlines...');

    try {
      const formData = new FormData();
      formData.append('file', streamlinesFile);

      const response = await fetch(`${API_BASE}/upload/streamlines`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setUploadStatus(`✓ Streamlines uploaded: ${result.filename} (${result.num_streamlines} streamlines)`);
        setStreamlinesFile(null);
        fetchUploadedFiles();
      } else {
        setUploadStatus(`✗ Upload failed: ${result.detail || 'Unknown error'}`);
      }
    } catch (error) {
      setUploadStatus(`✗ Upload error: ${error}`);
    } finally {
      setIsUploading(false);
    }
  };

  const fetchUploadedFiles = async () => {
    try {
      const response = await fetch(`${API_BASE}/files`);
      const result = await response.json();
      setUploadedFiles(result);
    } catch (error) {
      console.error('Failed to fetch uploaded files:', error);
    }
  };

  const deleteStl = async (filename: string) => {
    try {
      const response = await fetch(`${API_BASE}/files/stl/${filename}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setUploadStatus(`✓ Deleted ${filename}`);
        fetchUploadedFiles();
      }
    } catch (error) {
      setUploadStatus(`✗ Delete failed: ${error}`);
    }
  };

  const deleteStreamlines = async (filename: string) => {
    try {
      const response = await fetch(`${API_BASE}/files/streamlines/${filename}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setUploadStatus(`✓ Deleted ${filename}`);
        fetchUploadedFiles();
      }
    } catch (error) {
      setUploadStatus(`✗ Delete failed: ${error}`);
    }
  };

  // Fetch files on mount
  React.useEffect(() => {
    if (isVisible) {
      fetchUploadedFiles();
    }
  }, [isVisible]);

  return (
    <div className="file-upload-menu">
      <div className="file-upload-header">
        <h2>Upload Files</h2>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>

      <div className="file-upload-content">
        {/* STL Upload Section */}
        <div className="upload-section">
          <h3>STL File</h3>
          <div className="upload-row">
            <input
              type="file"
              accept=".stl"
              onChange={handleStlFileChange}
              disabled={isUploading}
            />
            <button
              onClick={uploadStl}
              disabled={!stlFile || isUploading}
              className="upload-btn"
            >
              Upload STL
            </button>
          </div>
          {stlFile && <p className="file-info">Selected: {stlFile.name}</p>}
        </div>

        {/* Streamlines Upload Section */}
        <div className="upload-section">
          <h3>Streamlines JSON</h3>
          <div className="upload-row">
            <input
              type="file"
              accept=".json"
              onChange={handleStreamlinesFileChange}
              disabled={isUploading}
            />
            <button
              onClick={uploadStreamlines}
              disabled={!streamlinesFile || isUploading}
              className="upload-btn"
            >
              Upload Streamlines
            </button>
          </div>
          {streamlinesFile && <p className="file-info">Selected: {streamlinesFile.name}</p>}
        </div>

        {/* Status */}
        {uploadStatus && (
          <div className={`upload-status ${uploadStatus.startsWith('✓') ? 'success' : 'error'}`}>
            {uploadStatus}
          </div>
        )}

        {/* Uploaded Files List */}
        <div className="uploaded-files">
          <h3>Uploaded STL Files ({uploadedFiles.stl_files.length})</h3>
          <div className="file-list">
            {uploadedFiles.stl_files.map((file) => (
              <div key={file.name} className="file-item">
                <span>{file.name}</span>
                <span className="file-size">
                  {(file.size / 1024).toFixed(1)} KB
                </span>
                <button
                  className="delete-btn"
                  onClick={() => deleteStl(file.name)}
                >
                  Delete
                </button>
              </div>
            ))}
            {uploadedFiles.stl_files.length === 0 && (
              <p className="no-files">No STL files uploaded yet</p>
            )}
          </div>

          <h3>Uploaded Streamlines ({uploadedFiles.streamline_files.length})</h3>
          <div className="file-list">
            {uploadedFiles.streamline_files.map((file: any) => (
              <div key={file.name} className="file-item">
                <span>{file.name}</span>
                <span className="file-size">
                  {file.num_streamlines} streamlines
                </span>
                <button
                  className="delete-btn"
                  onClick={() => deleteStreamlines(file.name)}
                >
                  Delete
                </button>
              </div>
            ))}
            {uploadedFiles.streamline_files.length === 0 && (
              <p className="no-files">No streamline files uploaded yet</p>
            )}
          </div>
        </div>

        {/* Help Section */}
        <div className="help-section">
          <h4>Format Help</h4>
          <p>
            <strong>STL Files:</strong> Standard STL format (ASCII or binary)
          </p>
          <p>
            <strong>Streamlines JSON:</strong> See{' '}
            <code>upload-service/STREAMLINE_FORMAT.md</code> for format details
          </p>
        </div>
      </div>
    </div>
  );
};

export default FileUploadMenu;
