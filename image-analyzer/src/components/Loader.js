import React from 'react';
import './Loader.css';

const Loader = () => (
  <div className="loader-container">
    <div className="loader-ring">
      <div></div>
      <div></div>
      <div></div>
      <div></div>
    </div>
    <p className="loader-text">Analyzing image... <span className="dots"></span></p>
  </div>
);

export default Loader;
