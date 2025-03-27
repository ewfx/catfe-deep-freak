import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./RegisteredApis.css";

const RegisteredApis = () => {
  const [apis, setApis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchRegisteredApis = async () => {
      try {
        const response = await axios.get("http://localhost:8000/registered-apis");
        setApis(response.data);
      } catch (err) {
        setError("Failed to fetch registered APIs");
        console.error("Error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchRegisteredApis();
  }, []);

  const handleViewResults = (api) => {
    navigate("/results", { 
      state: { 
        apiDetails: api,
        testResults: { output: "Loading...", passed: api.last_test_result }
      } 
    });
  };

  if (loading) {
    return <div className="registered-apis-loading">Loading APIs...</div>;
  }

  if (error) {
    return <div className="registered-apis-error">{error}</div>;
  }

  return (
    <div className="registered-apis-container">
      <header className="registered-apis-header">
        <h1>Registered APIs</h1>
        <p>List of all registered APIs and their test types.</p>
      </header>

      <section className="registered-apis-content">
        {apis.length === 0 ? (
          <p className="registered-apis-empty">No APIs registered yet.</p>
        ) : (
          <table className="registered-apis-table">
            <thead>
              <tr>
                <th>S.No.</th>
                <th>API URL</th>
                <th>Test Type</th>
                <th>Registered</th>
                <th>Last Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {apis.map((api, index) => (
                <tr key={index}>
                  <td>{index + 1}</td>
                  <td className="api-url">{api.url}</td>
                  <td>{api.type}</td>
                  <td>{new Date(api.registration_time).toLocaleString()}</td>
                  <td>
                    <span className={`status-badge ${api.last_test_result ? 'passed' : 'failed'}`}>
                      {api.last_test_result ? 'PASSED' : 'FAILED'}
                    </span>
                  </td>
                  <td>
                    <button 
                      className="view-results-button"
                      onClick={() => handleViewResults(api)}
                    >
                      View Results
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
};

export default RegisteredApis;