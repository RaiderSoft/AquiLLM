import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const IngestPDF: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      console.log('Selected file:', {
        name: selectedFile.name,
        size: selectedFile.size,
        type: selectedFile.type
      });
      setFile(selectedFile);
      setError(null);
      setSuccess(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(false);

    const formData = new FormData();
    formData.append('file', file);

    // Log the request details
    console.log('Sending request to:', '/ingest_pdf/');
    console.log('File being sent:', {
      name: file.name,
      size: file.size,
      type: file.type
    });

    try {
      console.log('Starting PDF upload...');
      const response = await fetch('/ingest_pdf/', {
        method: 'POST',
        body: formData,
        headers: {
          'Accept': 'application/json',
        },
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', {
          status: response.status,
          statusText: response.statusText,
          body: errorText
        });
        
        let errorMessage;
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.error || 'Failed to upload PDF';
        } catch {
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log('Success response:', data);
      setSuccess(true);
      
      // Reset form
      setFile(null);
      if (e.target instanceof HTMLFormElement) {
        e.target.reset();
      }

      // If we have a document ID, navigate to it after a short delay
      if (data.document_id) {
        console.log('Navigating to document:', data.document_id);
        setTimeout(() => {
          navigate(`/document/${data.document_id}`);
        }, 1500);
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4 text-white">Upload PDF</h1>
      <form onSubmit={handleSubmit} className="max-w-md">
        <div className="mb-4">
          <label className="block text-white mb-2">Select PDF File</label>
          <input
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-400
              file:mr-4 file:py-2 file:px-4
              file:rounded-lg file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-600 file:text-white
              hover:file:bg-blue-700
              file:cursor-pointer cursor-pointer"
          />
          <p className="mt-1 text-gray-400 text-sm">
            Maximum file size: 50MB
          </p>
        </div>
        
        {error && (
          <div className="mb-4 text-red-500 text-sm">{error}</div>
        )}

        {success && (
          <div className="mb-4 text-green-500 text-sm">
            Successfully uploaded PDF! Redirecting to document view...
          </div>
        )}

        <button
          type="submit"
          disabled={uploading || !file}
          className={`w-full py-2 px-4 rounded-lg font-semibold ${
            uploading || !file
              ? 'bg-gray-600 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          } text-white transition-colors`}
        >
          {uploading ? 'Uploading...' : 'Upload PDF'}
        </button>
      </form>
    </div>
  );
};

export default IngestPDF; 