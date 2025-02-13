import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const IngestTranscript: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
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

    try {
      const response = await fetch('/api/ingest_vtt/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.error || 'Failed to upload transcript');
      }

      const data = await response.json();
      setSuccess(true);
      
      // Reset form
      setFile(null);
      if (e.target instanceof HTMLFormElement) {
        e.target.reset();
      }

      // If we have a document ID, navigate to it after a short delay
      if (data.document_id) {
        setTimeout(() => {
          navigate(`/document/${data.document_id}`);
        }, 1500);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4 text-white">Upload Transcript</h1>
      <form onSubmit={handleSubmit} className="max-w-md">
        <div className="mb-4">
          <label className="block text-white mb-2">Select Transcript File</label>
          <input
            type="file"
            accept=".vtt,.srt,.txt"
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
            Supported formats: VTT, SRT, TXT
          </p>
        </div>
        
        {error && (
          <div className="mb-4 text-red-500 text-sm">{error}</div>
        )}

        {success && (
          <div className="mb-4 text-green-500 text-sm">
            Successfully uploaded transcript! Redirecting to document view...
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
          {uploading ? 'Uploading...' : 'Upload Transcript'}
        </button>
      </form>
    </div>
  );
};

export default IngestTranscript; 