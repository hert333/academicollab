import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';

// FIXED: Capture unhandled asynchronous rejections to intercept silent application state crashes
window.addEventListener('unhandledrejection', (event) => {
  console.error('Critical unhandled asynchronous lifecycle rejection event:', event.reason);
  // Prevent default terminal logging loops if telemetry tracking hooks are attached later
});

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);