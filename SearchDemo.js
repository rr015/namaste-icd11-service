import React, { useState } from 'react';
import { terminologyAPI } from '../services/api';
import './SearchDemo.css';

const SearchDemo = () => {
  const [searchData, setSearchData] = useState({
    query: '',
    system: '',
    patient_age: '',
    patient_gender: '',
    existing_conditions: '',
    symptoms: '',
    limit: 10
  });
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const requestData = {
        ...searchData,
        patient_age: searchData.patient_age ? parseInt(searchData.patient_age) : null,
        existing_conditions: searchData.existing_conditions ? searchData.existing_conditions.split(',') : null,
        symptoms: searchData.symptoms ? searchData.symptoms.split(',') : null,
        system: searchData.system || null
      };

      const response = await terminologyAPI.search(requestData);
      setResults(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setSearchData({
      ...searchData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="search-demo">
      <h2>Advanced Terminology Search</h2>
      
      <form onSubmit={handleSearch} className="search-form">
        <div className="form-group">
          <label>Search Query:</label>
          <input
            type="text"
            name="query"
            value={searchData.query}
            onChange={handleInputChange}
            placeholder="Enter term (e.g., fever, jwara, diabetes)"
            required
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>System:</label>
            <select name="system" value={searchData.system} onChange={handleInputChange}>
              <option value="">All Systems</option>
              <option value="namaste">NAMASTE</option>
              <option value="icd11_tm2">ICD-11 TM2</option>
              <option value="icd11_bio">ICD-11 Biomedicine</option>
            </select>
          </div>

          <div className="form-group">
            <label>Patient Age:</label>
            <input
              type="number"
              name="patient_age"
              value={searchData.patient_age}
              onChange={handleInputChange}
              placeholder="Age"
            />
          </div>

          <div className="form-group">
            <label>Patient Gender:</label>
            <select name="patient_gender" value={searchData.patient_gender} onChange={handleInputChange}>
              <option value="">Any</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label>Existing Conditions (comma-separated):</label>
          <input
            type="text"
            name="existing_conditions"
            value={searchData.existing_conditions}
            onChange={handleInputChange}
            placeholder="diabetes, hypertension"
          />
        </div>

        <div className="form-group">
          <label>Symptoms (comma-separated):</label>
          <input
            type="text"
            name="symptoms"
            value={searchData.symptoms}
            onChange={handleInputChange}
            placeholder="fever, cough, headache"
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {results.length > 0 && (
        <div className="results">
          <h3>Search Results ({results.length})</h3>
          <div className="results-grid">
            {results.map((result, index) => (
              <div key={index} className="result-card">
                <h4>{result.display}</h4>
                <p><strong>Code:</strong> {result.code} ({result.system})</p>
                <p><strong>Score:</strong> {result.score.toFixed(2)}</p>
                {result.definition && <p>{result.definition}</p>}
                {result.mapped_codes && Object.keys(result.mapped_codes).length > 0 && (
                  <div>
                    <strong>Mappings:</strong>
                    <ul>
                      {Object.entries(result.mapped_codes).map(([system, code]) => (
                        <li key={system}>{system}: {code}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchDemo;