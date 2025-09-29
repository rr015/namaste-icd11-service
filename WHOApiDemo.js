// src/components/WHOApiDemo.js
import React, { useState } from 'react';
import { terminologyAPI } from '../services/api';
import './WHOApiDemo.css';

const WHOApiDemo = () => {
  const [searchQuery, setSearchQuery] = useState('fever');
  const [searchSystem, setSearchSystem] = useState('icd11_tm2');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState(null);

  const testWHOApi = async () => {
    setLoading(true);
    try {
      const status = await terminologyAPI.getWHOStatus();
      setApiStatus(status.data);
    } catch (error) {
      setApiStatus({ connected: false, error: error.message });
    } finally {
      setLoading(false);
    }
  };

  const searchWHOApi = async () => {
    setLoading(true);
    try {
      const response = await terminologyAPI.searchWHODirect({
        query: searchQuery,
        system: searchSystem
      });
      setSearchResults(response.data.results);
    } catch (error) {
      console.error('WHO API search failed:', error);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="who-api-demo">
      <h2>WHO ICD-API Integration Demo</h2>
      
      <div className="api-status">
        <h3>API Connection Status</h3>
        <button onClick={testWHOApi} disabled={loading}>
          {loading ? 'Testing...' : 'Test WHO API Connection'}
        </button>
        
        {apiStatus && (
          <div className={`status ${apiStatus.connected ? 'connected' : 'disconnected'}`}>
            <h4>Status: {apiStatus.connected ? '✅ Connected' : '❌ Disconnected'}</h4>
            {apiStatus.message && <p>{apiStatus.message}</p>}
            {apiStatus.error && <p className="error">Error: {apiStatus.error}</p>}
          </div>
        )}
      </div>

      <div className="real-time-search">
        <h3>Real-time WHO API Search</h3>
        <div className="search-controls">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Enter search term..."
          />
          <select value={searchSystem} onChange={(e) => setSearchSystem(e.target.value)}>
            <option value="icd11_tm2">ICD-11 TM2</option>
            <option value="icd11_bio">ICD-11 Biomedicine</option>
          </select>
          <button onClick={searchWHOApi} disabled={loading}>
            {loading ? 'Searching WHO API...' : 'Search Real-time'}
          </button>
        </div>

        {searchResults.length > 0 && (
          <div className="search-results">
            <h4>WHO API Results ({searchResults.length})</h4>
            {searchResults.map((result, index) => (
              <div key={index} className="who-result">
                <h5>{result.display}</h5>
                <p><strong>Code:</strong> {result.code}</p>
                <p><strong>ID:</strong> {result.id}</p>
                {result.definition && <p><strong>Definition:</strong> {result.definition}</p>}
                <p><strong>Source:</strong> WHO ICD-API</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="api-info">
        <h3>About WHO ICD-API</h3>
        <div className="info-grid">
          <div className="info-item">
            <h4>🌐 Real-time Data</h4>
            <p>Direct access to WHO's official ICD-11 terminology</p>
          </div>
          <div className="info-item">
            <h4>🏥 TM2 Module</h4>
            <p>Chapter 26 - Traditional Medicine conditions</p>
          </div>
          <div className="info-item">
            <h4>⚡ Live Search</h4>
            <p>Search the latest ICD-11 codes in real-time</p>
          </div>
          <div className="info-item">
            <h4>🔗 Automatic Mapping</h4>
            <p>AI-powered mapping between NAMASTE and ICD-11</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WHOApiDemo;