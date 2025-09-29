import React, { useState } from 'react';
import { terminologyAPI } from '../services/api';
import './CodeBrowser.css';

const CodeBrowser = () => {
  const [browseData, setBrowseData] = useState({
    system: 'namaste',
    code: ''
  });
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleBrowse = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await terminologyAPI.getCodeDetails(browseData.system, browseData.code);
      setDetails(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Code not found');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setBrowseData({
      ...browseData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="code-browser">
      <h2>Code Browser</h2>
      
      <form onSubmit={handleBrowse} className="browse-form">
        <div className="form-row">
          <div className="form-group">
            <label>System:</label>
            <select name="system" value={browseData.system} onChange={handleInputChange}>
              <option value="namaste">NAMASTE</option>
              <option value="icd11_tm2">ICD-11 TM2</option>
              <option value="icd11_bio">ICD-11 Biomedicine</option>
            </select>
          </div>

          <div className="form-group">
            <label>Code:</label>
            <input
              type="text"
              name="code"
              value={browseData.code}
              onChange={handleInputChange}
              placeholder="e.g., AY001, TM2_KA50"
              required
            />
          </div>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Loading...' : 'Get Details'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {details && (
        <div className="code-details">
          <h3>Code Details</h3>
          <div className="details-card">
            <h4>{details.display}</h4>
            <p><strong>Code:</strong> {details.code}</p>
            <p><strong>System:</strong> {browseData.system}</p>
            {details.definition && <p><strong>Definition:</strong> {details.definition}</p>}
            {details.dosha && <p><strong>Dosha:</strong> {details.dosha}</p>}
            {details.system && <p><strong>Body System:</strong> {details.system}</p>}
            {details.category && <p><strong>Category:</strong> {details.category}</p>}
            {details.synonyms && details.synonyms.length > 0 && (
              <p><strong>Synonyms:</strong> {details.synonyms.join(', ')}</p>
            )}
            {details.icd11_tm2_code && (
              <p><strong>ICD-11 TM2 Code:</strong> {details.icd11_tm2_code}</p>
            )}
            {details.icd11_bio_code && (
              <p><strong>ICD-11 Biomedicine Code:</strong> {details.icd11_bio_code}</p>
            )}
            {details.mapping_confidence && (
              <p><strong>Mapping Confidence:</strong> {(details.mapping_confidence * 100).toFixed(1)}%</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CodeBrowser;