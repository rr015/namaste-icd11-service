import React, { useState } from 'react';
import { terminologyAPI } from '../services/api';
import './TranslateDemo.css';

const TranslateDemo = () => {
  const [translateData, setTranslateData] = useState({
    code: '',
    source_system: 'namaste',
    target_system: 'icd11_tm2'
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleTranslate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await terminologyAPI.translate(translateData);
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Translation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setTranslateData({
      ...translateData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="translate-demo">
      <h2>Code Translation</h2>
      
      <form onSubmit={handleTranslate} className="translate-form">
        <div className="form-row">
          <div className="form-group">
            <label>Source Code:</label>
            <input
              type="text"
              name="code"
              value={translateData.code}
              onChange={handleInputChange}
              placeholder="e.g., AY001, TM2_KA50"
              required
            />
          </div>

          <div className="form-group">
            <label>Source System:</label>
            <select name="source_system" value={translateData.source_system} onChange={handleInputChange}>
              <option value="namaste">NAMASTE</option>
              <option value="icd11_tm2">ICD-11 TM2</option>
              <option value="icd11_bio">ICD-11 Biomedicine</option>
            </select>
          </div>

          <div className="form-group">
            <label>Target System:</label>
            <select name="target_system" value={translateData.target_system} onChange={handleInputChange}>
              <option value="icd11_tm2">ICD-11 TM2</option>
              <option value="icd11_bio">ICD-11 Biomedicine</option>
              <option value="namaste">NAMASTE</option>
            </select>
          </div>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Translating...' : 'Translate'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="translation-result">
          <h3>Translation Result</h3>
          <div className="result-card">
            <div className="source">
              <h4>Source</h4>
              <p><strong>Code:</strong> {result.source_code}</p>
              <p><strong>Display:</strong> {result.source_display}</p>
            </div>
            
            <div className="arrow">→</div>
            
            <div className="target">
              <h4>Target</h4>
              <p><strong>Code:</strong> {result.target_code}</p>
              <p><strong>Display:</strong> {result.target_display}</p>
              <p><strong>Confidence:</strong> {(result.confidence * 100).toFixed(1)}%</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TranslateDemo;