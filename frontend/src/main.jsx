// This is the main entry point for the React application.
// It finds the 'root' HTML element and renders our main App component inside it.
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './app.jsx'; // Corrected: Added .jsx extension
import './index.css'; // Imports the base styles

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

