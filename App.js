// src/App.js
import React, { useState } from 'react';
import Header from './components/Header';
import SearchDemo from './components/SearchDemo';
import TranslateDemo from './components/TranslateDemo';
import CodeBrowser from './components/CodeBrowser';
import AuditLogs from './components/AuditLogs';
import CompliancePanel from './components/CompliancePanel';
import { authAPI, setAuthToken } from './services/api';
import './styles/App.css';

function App() {
  const [activeTab, setActiveTab] = useState('search');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loginData, setLoginData] = useState({ username: 'doctor1', password: 'doctorpass' });
  const [loginError, setLoginError] = useState('');
  const [userRole, setUserRole] = useState('user');
  const [userInfo, setUserInfo] = useState(null);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');

    try {
      const response = await authAPI.login(loginData.username, loginData.password);
      setAuthToken(response.data.access_token);
      setIsAuthenticated(true);
      
      // Set user role and info based on username
      let role = 'user';
      let userData = {
        username: loginData.username,
        displayName: 'Medical Professional'
      };

      if (loginData.username.includes('admin') || loginData.username === 'doctor1') {
        role = 'admin';
        userData.displayName = 'System Administrator';
        userData.permissions = ['read', 'write', 'admin'];
      } else if (loginData.username.includes('researcher')) {
        role = 'researcher';
        userData.displayName = 'Research User';
        userData.permissions = ['read', 'export'];
      } else {
        userData.permissions = ['read'];
      }

      setUserRole(role);
      setUserInfo(userData);

      // Log login success
      console.log(`User ${loginData.username} logged in with role: ${role}`);
    } catch (error) {
      setLoginError('Login failed. Please check credentials.');
      console.error('Login error:', error);
    }
  };

  const handleLogout = () => {
    console.log(`User ${userInfo?.username} logging out`);
    setAuthToken(null);
    setIsAuthenticated(false);
    setUserRole('user');
    setUserInfo(null);
  };

  if (!isAuthenticated) {
    return (
      <div className="app">
        <Header />
        <div className="login-container">
          <div className="login-form">
            <h2>Login to NAMASTE-ICD11 Terminology Service</h2>
            <div className="compliance-badge">
              <span>FHIR R4 Compliant • ISO 22600 Security</span>
            </div>
            
            <form onSubmit={handleLogin}>
              <div className="form-group">
                <label>Username:</label>
                <input
                  type="text"
                  value={loginData.username}
                  onChange={(e) => setLoginData({ ...loginData, username: e.target.value })}
                  placeholder="Enter username"
                  required
                />
              </div>
              <div className="form-group">
                <label>Password:</label>
                <input
                  type="password"
                  value={loginData.password}
                  onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                  placeholder="Enter password"
                  required
                />
              </div>
              {loginError && <div className="error">{loginError}</div>}
              <button type="submit" className="login-btn">Login</button>
            </form>

            <div className="demo-credentials">
              <h4>Demo Credentials:</h4>
              <div className="credential-group">
                <strong>Medical Professional:</strong>
                <p>Username: doctor1 | Password: doctorpass</p>
                <small>Full system access including API status monitoring</small>
              </div>
              <div className="credential-group">
                <strong>Research User:</strong>
                <p>Username: researcher1 | Password: researcherpass</p>
                <small>Read and export access with API status</small>
              </div>
            </div>

            <div className="system-info">
              <h4>System Features:</h4>
              <ul>
                <li>✓ NAMASTE-ICD11 Terminology Mapping</li>
                <li>✓ FHIR R4 CodeSystem & ConceptMap</li>
                <li>✓ ISO 22600 Security Compliance</li>
                <li>✓ WHO ICD-API Integration</li>
                <li>✓ Real-time API Status Monitoring</li>
                <li>✓ Consent Management</li>
                <li>✓ Audit Logging (All Users)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <Header userInfo={userInfo} />
      
      <nav className="tabs">
        {/* Core tabs - available to all users */}
        <button 
          className={activeTab === 'search' ? 'active' : ''} 
          onClick={() => setActiveTab('search')}
          title="Search terminology across all systems"
        >
          🔍 Search
        </button>
        <button 
          className={activeTab === 'translate' ? 'active' : ''} 
          onClick={() => setActiveTab('translate')}
          title="Translate codes between systems"
        >
          🔄 Translate
        </button>
        <button 
          className={activeTab === 'browse' ? 'active' : ''} 
          onClick={() => setActiveTab('browse')}
          title="Browse code systems"
        >
          📚 Code Browser
        </button>
        
        {/* Audit Logs with API Status - available to ALL authenticated users */}
        <button 
          className={activeTab === 'audit' ? 'active' : ''} 
          onClick={() => setActiveTab('audit')}
          title="View audit logs and API status"
        >
          📊 Audit & API Status
        </button>
        
        <button 
          className={activeTab === 'compliance' ? 'active' : ''} 
          onClick={() => setActiveTab('compliance')}
          title="Compliance and security information"
        >
          🛡️ Compliance
        </button>
        
        {/* Researcher-specific tab */}
        {userRole === 'researcher' && (
          <button 
            className={activeTab === 'export' ? 'active' : ''} 
            onClick={() => setActiveTab('export')}
            title="Data export functions"
          >
            📤 Export Data
          </button>
        )}

        <button 
  className="logout-btn" 
  onClick={handleLogout}
  title={`Logout ${userInfo?.username}`}
>
  🚪 Logout (Doctor)
</button>
      </nav>

      <main className="main-content">
        {activeTab === 'search' && <SearchDemo userRole={userRole} />}
        {activeTab === 'translate' && <TranslateDemo userRole={userRole} />}
        {activeTab === 'browse' && <CodeBrowser userRole={userRole} />}
        {activeTab === 'audit' && <AuditLogs userRole={userRole} />}
        {activeTab === 'compliance' && <CompliancePanel userRole={userRole} />}
        
        {activeTab === 'export' && userRole === 'researcher' && (
          <div className="export-panel">
            <h2>Data Export</h2>
            <p>Researcher data export functionality coming soon...</p>
          </div>
        )}
      </main>

      {/* Footer with system info */}
      <footer className="app-footer">
        <div className="footer-content">
          <span>NAMASTE-ICD11 Terminology Service v1.0.0</span>
          <span>FHIR R4 • ISO 22600 • WHO ICD-11 Compliant</span>
          <span>User: {userInfo?.username} | Role: {userRole}</span>
        </div>
      </footer>
    </div>
  );
}

export default App;