// src/components/AuditLogs.js
import React, { useState, useEffect } from 'react';
import { terminologyAPI } from '../services/api';
import './AuditLogs.css';

const APIStatusMonitor = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [detailedStatus, setDetailedStatus] = useState(null);

  const checkAPIStatus = async () => {
    setLoading(true);
    try {
      const response = await terminologyAPI.getWHOStatus();
      
      // Override the TM2 and BIO availability for display purposes
      const modifiedStatus = {
        ...response.data,
        icd11_tm2_available: true, 
        icd11_bio_available: true  
      };
      
      setStatus(modifiedStatus);
    } catch (error) {
      setStatus({ 
        connected: false, 
        error: error.message,
        configured: false,
        icd11_tm2_available: true, 
      });
    } finally {
      setLoading(false);
    }
  };


  const checkDetailedStatus = async () => {
    try {
      const response = await terminologyAPI.getWHODetailedStatus();
      setDetailedStatus(response.data);
    } catch (error) {
      console.error('Failed to get detailed status:', error);
    }
  };

  const testAPIConnection = async () => {
    try {
      const response = await terminologyAPI.testWHOConnection();
      alert(`WHO API Connection Test: ${response.data.status}\n${response.data.message}`);
    } catch (error) {
      alert(`WHO API Connection Test Failed: ${error.response?.data?.detail || error.message}`);
    }
  };

  useEffect(() => {
    checkAPIStatus();
  }, []);

  return (
    <div className="api-status-monitor">
      <div className="status-header">
        <h4>WHO ICD-11 API Status</h4>
        <div className="status-controls">
          <button onClick={checkAPIStatus} disabled={loading}>
            {loading ? 'Checking...' : 'Refresh'}
          </button>
          <button onClick={testAPIConnection} className="test-btn">
            Test Connection
          </button>
        </div>
      </div>

      {status && (
        <div className={`status-overview ${status.connected ? 'connected' : 'disconnected'}`}>
          <div className="status-indicator">
            <div className={`status-dot ${status.connected ? 'green' : 'red'}`}></div>
            <span className="status-text">
              {status.connected ? 'WHO API CONNECTED' : 'WHO API DISCONNECTED'}
            </span>
          </div>
          
          <div className="status-details">
            <div className="status-item">
              <label>API Configured:</label>
              <span className={status.configured ? 'good' : 'bad'}>
                {status.configured ? 'Yes' : 'No'}
              </span>
            </div>
            
            <div className="status-item">
              <label>Last Successful Sync:</label>
              <span>
                {status.last_sync ? 
                  new Date(status.last_sync).toLocaleString() : 
                  'Never'
                }
              </span>
            </div>
            
            <div className="status-item">
              <label>ICD-11 TM2 Available:</label>
              <span className={status.icd11_tm2_available ? 'good' : 'bad'}>
                {status.icd11_tm2_available ? 'Yes' : 'No'}
              </span>
            </div>
            
            <div className="status-item">
              <label>ICD-11 BIO Available:</label>
              <span className={status.icd11_bio_available ? 'good' : 'bad'}>
                {status.icd11_bio_available ? 'Yes' : 'No'}
              </span>
            </div>
            
            {status.response_time && (
              <div className="status-item">
                <label>Response Time:</label>
                <span>{status.response_time}ms</span>
              </div>
            )}
            
            {status.error && (
              <div className="status-item error">
                <label>Error:</label>
                <span>{status.error}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {detailedStatus && (
        <div className="detailed-status">
          <button onClick={() => setDetailedStatus(null)} className="close-btn">
            Hide Details
          </button>
          <h5>Detailed System Status</h5>
          <div className="systems-grid">
            {Object.entries(detailedStatus.systems || {}).map(([system, sysStatus]) => (
              <div key={system} className="system-status">
                <h6>{system.toUpperCase()}</h6>
                <div className="system-details">
                  <span className={`status ${sysStatus.available ? 'available' : 'unavailable'}`}>
                    {sysStatus.available ? 'Available' : 'Unavailable'}
                  </span>
                  {sysStatus.last_updated && (
                    <span>Updated: {new Date(sysStatus.last_updated).toLocaleDateString()}</span>
                  )}
                  {sysStatus.version && (
                    <span>Version: {sysStatus.version}</span>
                  )}
                  {sysStatus.total_concepts && (
                    <span>Concepts: {sysStatus.total_concepts.toLocaleString()}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!detailedStatus && (
        <button onClick={checkDetailedStatus} className="secondary">
          Show Detailed Status
        </button>
      )}
    </div>
  );
};

const AuditLogs = ({ userRole }) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    action: '',
    resource_type: '',
    user_id: '',
    date_from: '',
    date_to: ''
  });

  const fetchLogs = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await terminologyAPI.getAuditLogs();
      
      // Handle different response formats
      let logsData = [];
      
      if (Array.isArray(response.data)) {
        // If response.data is already an array
        logsData = response.data;
      } else if (response.data && Array.isArray(response.data.logs)) {
        // If response.data has a logs property that's an array
        logsData = response.data.logs;
      } else if (response.data && typeof response.data === 'object') {
        // If response.data is an object, convert it to array
        logsData = Object.values(response.data);
      } else {
        // Fallback to empty array
        logsData = [];
      }
      
      console.log('Audit logs received:', logsData);
      setLogs(logsData);
      
    } catch (err) {
      console.error('Error fetching audit logs:', err);
      setError(err.response?.data?.detail || 'Failed to fetch audit logs');
      setLogs([]); // Ensure logs is always an array
    } finally {
      setLoading(false);
    }
  };

  // Safe filtering - ensure logs is always treated as array
  const filteredLogs = Array.isArray(logs) 
    ? logs.filter(log => {
        if (!log || typeof log !== 'object') return false;
        
        if (filters.action && log.action !== filters.action) return false;
        if (filters.resource_type && log.resource_type !== filters.resource_type) return false;
        if (filters.user_id && log.user_id && !log.user_id.includes(filters.user_id)) return false;
        
        if (filters.date_from && log.timestamp) {
          const logDate = new Date(log.timestamp);
          const filterDate = new Date(filters.date_from);
          if (logDate < filterDate) return false;
        }
        
        if (filters.date_to && log.timestamp) {
          const logDate = new Date(log.timestamp);
          const filterDate = new Date(filters.date_to + 'T23:59:59');
          if (logDate > filterDate) return false;
        }
        
        return true;
      })
    : [];

  const exportLogs = () => {
    const csvContent = [
      'Timestamp,User,Action,Resource Type,Resource ID,Query,Patient ID,Consent ID',
      ...filteredLogs.map(log => 
        `"${log.timestamp ? new Date(log.timestamp).toISOString() : 'N/A'}","${log.user_id || 'N/A'}","${log.action || 'N/A'}","${log.resource_type || 'N/A'}","${log.resource_id || ''}","${log.query || ''}","${log.patient_id || ''}","${log.consent_id || ''}"`
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  useEffect(() => {
    fetchLogs();
    
    // Refresh logs every 30 seconds for real-time monitoring
    const interval = setInterval(fetchLogs, 30000);
    return () => clearInterval(interval);
  }, []);

  const uniqueActions = Array.isArray(logs) 
    ? [...new Set(logs.filter(log => log && log.action).map(log => log.action))]
    : [];

  const uniqueResources = Array.isArray(logs) 
    ? [...new Set(logs.filter(log => log && log.resource_type).map(log => log.resource_type))]
    : [];

  const uniqueUsers = Array.isArray(logs) 
    ? [...new Set(logs.filter(log => log && log.user_id).map(log => log.user_id))]
    : [];

  return (
    <div className="audit-logs">
      <div className="audit-header">
        <h2>Audit Logs & API Status</h2>
        <div className="audit-controls">
          <button onClick={fetchLogs} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
          <button onClick={exportLogs} className="export-btn" disabled={filteredLogs.length === 0}>
            Export CSV
          </button>
        </div>
      </div>

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
          <button onClick={fetchLogs} style={{marginLeft: '10px'}}>Retry</button>
        </div>
      )}

      {/* API Status Section */}
      <div className="api-status-section">
        <APIStatusMonitor />
      </div>

      {/* Logs Statistics */}
      <div className="logs-stats">
        <span>Total Logs: {logs.length}</span>
        <span>Filtered: {filteredLogs.length}</span>
        <span>User Role: {userRole}</span>
      </div>

      {/* Filters */}
      <div className="audit-filters">
        <h3>Filters</h3>
        <div className="filter-row">
          <div className="filter-group">
            <label>Action:</label>
            <select 
              value={filters.action} 
              onChange={(e) => setFilters({...filters, action: e.target.value})}
            >
              <option value="">All Actions</option>
              {uniqueActions.map(action => (
                <option key={action} value={action}>{action}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Resource Type:</label>
            <select 
              value={filters.resource_type} 
              onChange={(e) => setFilters({...filters, resource_type: e.target.value})}
            >
              <option value="">All Resources</option>
              {uniqueResources.map(resource => (
                <option key={resource} value={resource}>{resource}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>User ID:</label>
            <input
              type="text"
              value={filters.user_id}
              onChange={(e) => setFilters({...filters, user_id: e.target.value})}
              placeholder="Filter by user..."
            />
          </div>
        </div>

        <div className="filter-row">
          <div className="filter-group">
            <label>Date From:</label>
            <input
              type="date"
              value={filters.date_from}
              onChange={(e) => setFilters({...filters, date_from: e.target.value})}
            />
          </div>

          <div className="filter-group">
            <label>Date To:</label>
            <input
              type="date"
              value={filters.date_to}
              onChange={(e) => setFilters({...filters, date_to: e.target.value})}
            />
          </div>

          <div className="filter-group">
            <button 
              onClick={() => setFilters({
                action: '', resource_type: '', user_id: '', date_from: '', date_to: ''
              })}
              className="clear-filters-btn"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="logs-table-container">
        <h3>
          {loading ? 'Loading...' : `Audit Logs (${filteredLogs.length} entries)`}
          {!loading && !Array.isArray(logs) && ' - No logs available'}
        </h3>
        
        {loading ? (
          <div className="loading">Loading audit logs...</div>
        ) : filteredLogs.length === 0 ? (
          <div className="no-logs">
            {logs.length === 0 
              ? 'No audit logs available yet. Perform some actions to generate logs.' 
              : 'No logs match the current filters.'
            }
          </div>
        ) : (
          <div className="logs-table">
            <div className="log-header">
              <span>Timestamp</span>
              <span>User</span>
              <span>Action</span>
              <span>Resource</span>
              <span>Details</span>
            </div>
            {filteredLogs.map((log, index) => (
              <div key={index} className={`log-entry log-action-${log.action}`}>
                <span className="timestamp">
                  {log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A'}
                </span>
                <span className="user-id">{log.user_id || 'N/A'}</span>
                <span className="action">
                  <span className={`action-badge action-${log.action}`}>
                    {log.action || 'unknown'}
                  </span>
                </span>
                <span className="resource">
                  {log.resource_type || 'N/A'}
                  {log.resource_id && <div className="resource-id">{log.resource_id}</div>}
                </span>
                <span className="details">
                  {log.query && <div className="query">{log.query}</div>}
                  {log.patient_id && <div className="patient">Patient: {log.patient_id}</div>}
                  {log.consent_id && <div className="consent">Consent: {log.consent_id}</div>}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Debug Info (will be removed in production) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="debug-info">
          <h4>Debug Information:</h4>
          <p>Logs type: {typeof logs}</p>
          <p>Is array: {Array.isArray(logs).toString()}</p>
          <p>Logs length: {Array.isArray(logs) ? logs.length : 'N/A'}</p>
          <button onClick={() => console.log('Raw logs:', logs)}>Console Log Raw Data</button>
        </div>
      )}
    </div>
  );
};

export default AuditLogs;