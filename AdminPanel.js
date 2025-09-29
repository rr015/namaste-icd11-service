// src/components/AdminPanel.js
import React, { useState, useEffect } from 'react';
import { terminologyAPI } from '../services/api';
import './AdminPanel.css';

const AuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('');

  const loadAuditLogs = async () => {
    setLoading(true);
    try {
      const response = await terminologyAPI.getAuditLogs();
      setLogs(response.data.logs || []);
    } catch (error) {
      console.error('Failed to load audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLogs();
  }, []);

  const filteredLogs = logs.filter(log => 
    !filter || 
    log.action?.includes(filter) ||
    log.user_id?.includes(filter) ||
    log.resource_type?.includes(filter)
  );

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="audit-logs">
      <div className="audit-header">
        <h3>Audit Logs</h3>
        <div className="audit-controls">
          <input
            type="text"
            placeholder="Filter logs..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="filter-input"
          />
          <button onClick={loadAuditLogs} disabled={loading}>
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      <div className="logs-stats">
        <span>Total Logs: {logs.length}</span>
        <span>Filtered: {filteredLogs.length}</span>
      </div>

      <div className="logs-list">
        {filteredLogs.slice(0, 100).map((log, index) => (
          <div key={log.id || index} className="log-entry">
            <div className="log-header">
              <span className="timestamp">{formatTimestamp(log.timestamp)}</span>
              <span className={`action ${log.action}`}>{log.action}</span>
              <span className="user">{log.user_id}</span>
            </div>
            <div className="log-details">
              <span className="resource-type">{log.resource_type}</span>
              {log.resource_id && <span className="resource-id">ID: {log.resource_id}</span>}
              {log.query && <span className="query">Query: {log.query}</span>}
              {log.patient_id && <span className="patient-id">Patient: {log.patient_id}</span>}
            </div>
            {log.compliance && (
              <div className="compliance-tag">{log.compliance}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

const WHOStatusMonitor = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [detailedStatus, setDetailedStatus] = useState(null);

  const checkWHOStatus = async () => {
    setLoading(true);
    try {
      const response = await terminologyAPI.getWHOStatus();
      setStatus(response.data);
    } catch (error) {
      setStatus({ 
        connected: false, 
        error: error.message,
        configured: false
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

  const testWHOConnection = async () => {
    try {
      const response = await terminologyAPI.testWHOConnection();
      alert(`WHO Connection Test: ${response.data.status}\n${response.data.message}`);
    } catch (error) {
      alert(`WHO Connection Test Failed: ${error.response?.data?.detail || error.message}`);
    }
  };

  useEffect(() => {
    checkWHOStatus();
  }, []);

  return (
    <div className="who-status-monitor">
      <div className="status-header">
        <h3>WHO ICD-11 API Status Monitor</h3>
        <div className="status-controls">
          <button onClick={checkWHOStatus} disabled={loading}>
            {loading ? 'Checking...' : 'Refresh Status'}
          </button>
          <button onClick={checkDetailedStatus} className="secondary">
            Detailed Status
          </button>
          <button onClick={testWHOConnection} className="test-btn">
            Test Connection
          </button>
        </div>
      </div>

      {status && (
        <div className={`status-overview ${status.connected ? 'connected' : 'disconnected'}`}>
          <div className="status-indicator">
            <div className={`status-dot ${status.connected ? 'green' : 'red'}`}></div>
            <span className="status-text">
              {status.connected ? 'CONNECTED' : 'DISCONNECTED'}
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
          <h4>Detailed System Status</h4>
          <div className="systems-grid">
            {Object.entries(detailedStatus.systems || {}).map(([system, sysStatus]) => (
              <div key={system} className="system-status">
                <h5>{system.toUpperCase()}</h5>
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
          
          <div className="sync-info">
            <h5>Sync Information</h5>
            <pre>{JSON.stringify(detailedStatus.sync_info, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
};

const AdminPanel = () => {
  const [activeTab, setActiveTab] = useState('import');
  const [csvContent, setCsvContent] = useState('');
  const [importResult, setImportResult] = useState(null);
  const [syncResult, setSyncResult] = useState(null);
  const [versions, setVersions] = useState([]);

  const handleCSVImport = async () => {
    try {
      const result = await terminologyAPI.importCSV({
        csv_content: csvContent,
        description: "CSV import via admin panel"
      });
      setImportResult(result.data);
      setCsvContent(''); // Clear after import
    } catch (error) {
      setImportResult({ status: 'error', error: error.response?.data?.detail || error.message });
    }
  };

  const handleWHOSync = async () => {
    try {
      const result = await terminologyAPI.syncWHO({
        systems: ['icd11_tm2', 'icd11_bio'],
        force_refresh: true
      });
      setSyncResult(result.data);
    } catch (error) {
      setSyncResult({ status: 'error', error: error.response?.data?.detail || error.message });
    }
  };

  const loadVersions = async () => {
    try {
      const response = await terminologyAPI.getVersions();
      setVersions(response.data.versions || []);
    } catch (error) {
      console.error('Failed to load versions:', error);
    }
  };

  const activateVersion = async (version) => {
    try {
      await terminologyAPI.activateVersion(version);
      loadVersions(); // Reload versions to reflect changes
      alert(`Version ${version} activated successfully`);
    } catch (error) {
      alert(`Failed to activate version: ${error.response?.data?.detail || error.message}`);
    }
  };

  return (
    <div className="admin-panel">
      <h2>Administration Panel</h2>
      
      <div className="admin-tabs">
        <button 
          className={activeTab === 'import' ? 'active' : ''}
          onClick={() => setActiveTab('import')}
        >
          CSV Import
        </button>
        <button 
          className={activeTab === 'sync' ? 'active' : ''}
          onClick={() => setActiveTab('sync')}
        >
          WHO Sync
        </button>
        <button 
          className={activeTab === 'versions' ? 'active' : ''}
          onClick={() => { setActiveTab('versions'); loadVersions(); }}
        >
          Version Management
        </button>
        <button 
          className={activeTab === 'audit' ? 'active' : ''}
          onClick={() => setActiveTab('audit')}
        >
          Audit Logs
        </button>
        <button 
          className={activeTab === 'compliance' ? 'active' : ''}
          onClick={() => setActiveTab('compliance')}
        >
          Compliance
        </button>
        <button 
          className={activeTab === 'who-status' ? 'active' : ''}
          onClick={() => setActiveTab('who-status')}
        >
          WHO API Status
        </button>
      </div>

      {activeTab === 'import' && (
        <div className="tab-content">
          <h3>NAMASTE CSV Import</h3>
          <div className="import-instructions">
            <p>Format: Code,Display,Category,System</p>
            <p>Example: N001,Fever,Symptoms,namaste</p>
          </div>
          <textarea
            value={csvContent}
            onChange={(e) => setCsvContent(e.target.value)}
            placeholder="Paste CSV content here..."
            rows={10}
            className="csv-textarea"
          />
          <button onClick={handleCSVImport} disabled={!csvContent.trim()}>
            Import CSV
          </button>
          {importResult && (
            <div className={`result ${importResult.status}`}>
              <h4>Import Result</h4>
              <pre>{JSON.stringify(importResult, null, 2)}</pre>
            </div>
          )}
        </div>
      )}

      {activeTab === 'sync' && (
        <div className="tab-content">
          <h3>WHO ICD-API Synchronization</h3>
          
          <WHOStatusMonitor />

          <div className="sync-controls">
            <button onClick={handleWHOSync}>Sync with WHO API</button>
            <div className="sync-options">
              <label>
                <input type="checkbox" defaultChecked /> ICD-11 TM2
              </label>
              <label>
                <input type="checkbox" defaultChecked /> ICD-11 BIO
              </label>
              <label>
                <input type="checkbox" /> Force Refresh
              </label>
            </div>
          </div>
          
          {syncResult && (
            <div className={`result ${syncResult.status}`}>
              <h4>Sync Result</h4>
              <pre>{JSON.stringify(syncResult, null, 2)}</pre>
            </div>
          )}
        </div>
      )}

      {activeTab === 'versions' && (
        <div className="tab-content">
          <h3>Terminology Versions</h3>
          <button onClick={loadVersions}>Refresh Versions</button>
          
          <div className="versions-list">
            {versions.map((version, index) => (
              <div key={index} className="version-card">
                <div className="version-header">
                  <h4>Version {version.version}</h4>
                  {version.active && <span className="active-badge">Active</span>}
                </div>
                <p><strong>Effective:</strong> {new Date(version.effective_date).toLocaleDateString()}</p>
                <p><strong>Systems:</strong> {version.systems?.join(', ') || 'N/A'}</p>
                <p><strong>Description:</strong> {version.description || 'No description'}</p>
                {!version.active && (
                  <button 
                    onClick={() => activateVersion(version.version)}
                    className="activate-btn"
                  >
                    Activate Version
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="tab-content">
          <AuditLogs />
        </div>
      )}

      {activeTab === 'compliance' && (
        <div className="tab-content">
          <h3>Compliance Information</h3>
          <div className="compliance-info">
            <div className="standard">
              <h4>✅ FHIR R4 Compliance</h4>
              <p>All terminology resources follow FHIR R4 standards including CodeSystem and ConceptMap resources</p>
            </div>
            <div className="standard">
              <h4>✅ ISO 22600 Access Control</h4>
              <p>Implements comprehensive access control policies, audit trails, and privilege management</p>
            </div>
            <div className="standard">
              <h4>✅ India EHR Standards 2016</h4>
              <p>Compliant with Indian EHR standards including consent management and data privacy</p>
            </div>
            <div className="standard">
              <h4>✅ Semantic Interoperability</h4>
              <p>Supports SNOMED-CT and LOINC mappings for enhanced semantic interoperability</p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'who-status' && (
        <div className="tab-content">
          <WHOStatusMonitor />
        </div>
      )}
    </div>
  );
};

export default AdminPanel;