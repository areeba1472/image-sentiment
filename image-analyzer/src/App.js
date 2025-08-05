// App.js
import React, { useState } from 'react';
import './App.css';
import MetadataPage from './components/MetadataPage';
import Loader from './components/Loader';

function App() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [imageData, setImageData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showResultPage, setShowResultPage] = useState(false);

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
    }
  };

  const handleAnalyzeClick = async () => {
    if (selectedImage) {
      setLoading(true);
      const formData = new FormData();
      formData.append('files', selectedImage);

      try {
        const response = await fetch('http://127.0.0.1:8000/process-images', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) throw new Error('Server error');

        const json = await response.json();
        setImageData(json.results[0]);
        setShowResultPage(true);
      } catch (err) {
        alert('Failed to analyze image.');
      } finally {
        setLoading(false);
      }
    }
  };

  if (loading) return <Loader />;

  if (showResultPage && imageData) {
    return <MetadataPage imageData={imageData} />;
  }

  return (
    <div className="app-container">
      <h1>Image Analyzer</h1>
      <div className="upload-section">
        <label htmlFor="file-upload" className="custom-file-upload">📤 Upload Image</label>
        <input id="file-upload" type="file" accept="image/*" onChange={handleImageUpload} />
        {selectedImage && (
          <div className="image-preview">
            <img src={URL.createObjectURL(selectedImage)} alt="Preview" />
            <button className="analyze-button" onClick={handleAnalyzeClick}>🔍 Analyze Image</button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
