// src/components/CompliancePanel.js
import React, { useState, useEffect } from 'react';
import { terminologyAPI } from '../services/api';
import './CompliancePanel.css';

const CompliancePanel = () => {
  const [complianceData, setComplianceData] = useState(null);
  const [snomedMappings, setSnomedMappings] = useState({});
  const [loading, setLoading] = useState(false);

  const loadComplianceInfo = async () => {
    setLoading(true);
    try {
      const response = await terminologyAPI.getCompliancePolicies();
      setComplianceData(response.data);
    } catch (error) {
      console.error('Failed to load compliance data:', error);
    } finally {
      setLoading(false);
    }
  };

  const testSNOMEDMapping = async (code) => {
    try {
      const response = await terminologyAPI.getSNOMEDLOINCMappings(code);
      setSnomedMappings(prev => ({
        ...prev,
        [code]: response.data
      }));
    } catch (error) {
      console.error('Failed to load SNOMED mappings:', error);
    }
  };

  useEffect(() => {
    loadComplianceInfo();
  }, []);

  return (
    <div className="compliance-panel">
      <h2>Compliance & Standards</h2>
      
      <div className="compliance-grid">
        <div className="compliance-card">
          <h3>✅ FHIR R4 Compliance</h3>
          <p>All terminology resources follow FHIR R4 standards for interoperability</p>
          <ul>
            <li>CodeSystem resources</li>
            <li>ConceptMap resources</li>
            <li>ProblemList entries</li>
            <li>Bundle transactions</li>
          </ul>
        </div>

        <div className="compliance-card">
          <h3>🔒 ISO 22600 Access Control</h3>
          <p>Implements healthcare access control policies</p>
          {complianceData && (
            <div className="policies">
              <h4>Access Policies:</h4>
              {complianceData.policies.map((policy, index) => (
                <div key={index} className="policy">
                  <strong>{policy.name}</strong>: {policy.description}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="compliance-card">
          <h3>🇮🇳 India EHR Standards 2016</h3>
          <p>Compliant with Indian EHR standards including:</p>
          <ul>
            <li>ABHA integration support</li>
            <li>Consent management</li>
            <li>Audit trails</li>
            <li>Terminology standards</li>
          </ul>
        </div>

        <div className="compliance-card">
          <h3>🔗 SNOMED-CT & LOINC Semantics</h3>
          <p>Semantic interoperability with international standards</p>
          
          <div className="mapping-test">
            <h4>Test Mappings:</h4>
            <button onClick={() => testSNOMEDMapping('AY001')}>Test AY001 (Jwara)</button>
            <button onClick={() => testSNOMEDMapping('AY004')}>Test AY004 (Madhumeha)</button>
            
            {snomedMappings['AY001'] && (
              <div className="mapping-result">
                <h5>AY001 Mappings:</h5>
                <pre>{JSON.stringify(snomedMappings['AY001'], null, 2)}</pre>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="compliance-status">
        <h3>Overall Compliance Status</h3>
        <div className="status-grid">
          <div className="status-item compliant">
            <span>FHIR R4</span>
            <span>✅ Compliant</span>
          </div>
          <div className="status-item compliant">
            <span>ISO 22600</span>
            <span>✅ Implemented</span>
          </div>
          <div className="status-item compliant">
            <span>EHR Standards 2016</span>
            <span>✅ Compliant</span>
          </div>
          <div className="status-item compliant">
            <span>SNOMED-CT/LOINC</span>
            <span>✅ Integrated</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompliancePanel;