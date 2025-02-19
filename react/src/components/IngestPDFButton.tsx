import React, { useRef, useState, useEffect } from 'react';
import { getCookie } from '../utils/csrf';

interface IngestPDFButtonProps {
  collectionId: string | number;
}

const IngestPDFButton: React.FC<IngestPDFButtonProps> = ({ collectionId }) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Component lifecycle and props validation
  useEffect(() => {
    console.log('IngestPDFButton: Component mounted with collectionId:', collectionId);
    console.log('IngestPDFButton: Initial fileInputRef:', fileInputRef.current);
    
    return () => {
      console.log('IngestPDFButton: Component unmounting');
    };
  }, [collectionId]);

  const handleButtonClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    console.log('IngestPDFButton: Button clicked', {
      event: e,
      buttonElement: e.currentTarget,
      fileInput: fileInputRef.current,
      collectionId
    });

    if (fileInputRef.current) {
      console.log('IngestPDFButton: Attempting to trigger file input click');
      fileInputRef.current.click();
    } else {
      console.error('IngestPDFButton: fileInputRef is null');
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    console.log('IngestPDFButton: File input changed', {
      files: e.target.files,
      fileInput: e.target
    });

    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setError(null);
      setSuccess(false);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('collection_id', collectionId.toString());

      const csrfToken = getCookie('csrftoken');
      console.log('IngestPDFButton: CSRF token:', csrfToken);
      if (!csrfToken) {
        setError('Missing CSRF token');
        return;
      }

      setUploading(true);
      try {
        console.log('IngestPDFButton: Initiating file upload', {
          fileName: file.name,
          fileSize: file.size,
          collectionId
        });

        const response = await fetch('/ingest_pdf/', {
          method: 'POST',
          credentials: 'include',
          body: formData,
          headers: {
            'Accept': 'application/json',
            'X-CSRFToken': csrfToken
          }
        });
        if (!response.ok) {
          const errorText = await response.text();
          let errorMessage;
          try {
            const errorData = JSON.parse(errorText);
            errorMessage = errorData.error || 'Failed to upload PDF';
          } catch {
            errorMessage = `Server error: ${response.status} ${response.statusText}`;
          }
          setError(errorMessage);
        } else {
          const contentType = response.headers.get('Content-Type') || '';
          if (contentType.includes('application/json')) {
            const data = await response.json();
            console.log('PDF uploaded successfully:', data);
          } else {
            console.log('PDF uploaded successfully, but no JSON payload received');
          }
          setSuccess(true);
        }
      } catch (err) {
        console.error('IngestPDFButton: Upload error:', err);
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setUploading(false);
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      }
    }
  };

  return (
    <div>
      <button
        onClick={handleButtonClick}
        disabled={uploading}
        style={{
          padding: '0.5rem',
          backgroundColor: '#3b82f6',
          color: 'white',
          borderRadius: '0.375rem',
          border: 'none',
          cursor: 'pointer',
          width: '100%'
        }}
      >
        {uploading ? 'Uploading...' : 'Ingest PDF'}
      </button>
      <input
        type="file"
        accept=".pdf,application/pdf"
        ref={fileInputRef}
        hidden
        onChange={handleFileChange}
      />
      {error && <div className="mt-2 text-red-500 text-sm">{error}</div>}
      {success && <div className="mt-2 text-green-500 text-sm">Successfully uploaded PDF!</div>}
    </div>
  );
};

export default IngestPDFButton; 