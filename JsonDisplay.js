// src/components/JsonDisplay.js
import React from 'react';
import './JsonDisplay.css';

const JsonDisplay = ({ data, title }) => {
  if (!data) return null;

  const formatValue = (value) => {
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  return (
    <div className="json-display">
      {title && <h4>{title}</h4>}
      <pre className="json-content">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
};

export default JsonDisplay;