import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "./Results.css";

const Results = () => {
  const [isDarkTheme] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { testResults, generatedCode, apiDetails } = location.state || {};

  if (!testResults) {
    return (
      <div className={`results-container ${isDarkTheme ? 'dark-theme' : ''}`}>
        <div className="results-header">
          <h1>Test Results</h1>
          <button className="back-button" onClick={() => navigate(-1)}>
            ← Back
          </button>
        </div>
        <div className="no-results">
          <p>No test results available.</p>
        </div>
      </div>
    );
  }

  const handleDownload = () => {
    if (!generatedCode) return;

    const element = document.createElement("a");
    const fileName =
      apiDetails?.type === "bdd" ? "api_tests.feature" : "generated_tests.py";
    const file = new Blob([generatedCode], { type: "text/plain" });

    element.href = URL.createObjectURL(file);
    element.download = fileName;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const formatCodeForDisplay = (code) => {
    if (!code) return "No content available";
    if (typeof code === "string") return code;
    if (typeof code === "object") return JSON.stringify(code, null, 2);
    return String(code);
  };

  const CodeDisplay = ({ code }) => {
    const formattedCode = formatCodeForDisplay(code);
    return (
      <pre className={`code-block ${isDarkTheme ? 'dark' : 'light'}`}>
        <code>{formattedCode}</code>
      </pre>
    );
  };

  // Get metrics from test results
  const executionMetrics = testResults.executionMetrics || {};
  const testCases = testResults.testCases || [];
  const totalTests = executionMetrics.total_tests || testCases.length;
  const passedCount = executionMetrics.passed_tests || 
                     testCases.filter(tc => tc.status === 'PASSED').length;
  const failedCount = executionMetrics.failed_tests || 
                     testCases.filter(tc => tc.status === 'FAILED').length;
  const execTime = executionMetrics.execution_time_seconds || 0;

  return (
    <div className={`results-container ${isDarkTheme ? 'dark-theme' : ''}`}>
      <div className="results-header">
        <h1>Test Results</h1>
        <button className="back-button" onClick={() => navigate(-1)}>
          ← Back
        </button>
      </div>

      <div className="results-grid">
        {/* API Details Section */}
        <div className="api-details-card">
          <h2>API Information</h2>
          {apiDetails ? (
            <div className="api-info">
              <p>
                <strong>URL:</strong> {apiDetails.url}
              </p>
              <p>
                <strong>Test Type:</strong> {apiDetails.type}
              </p>
              <p>
                <strong>Registered:</strong>{" "}
                {new Date(apiDetails.registration_time).toLocaleString()}
              </p>
              <p>
                <strong>Last Test Status:</strong>
                <span
                  className={`status-badge ${
                    passedCount === totalTests ? "passed" : "failed"
                  }`}
                >
                  {passedCount === totalTests ? "PASSED" : "FAILED"}
                </span>
              </p>
            </div>
          ) : (
            <p>No API details available</p>
          )}
        </div>

        {/* Test Summary Section */}
        <div className="summary-card">
          <h2>Test Summary</h2>
          <div className="summary-stats">
            <div className="stat-card total">
              <h3>Total Tests</h3>
              <p>{totalTests}</p>
            </div>
            <div className="stat-card passed">
              <h3>Passed</h3>
              <p>{passedCount}</p>
            </div>
            <div className="stat-card failed">
              <h3>Failed</h3>
              <p>{failedCount}</p>
            </div>
            <div className="stat-card time">
              <h3>Time</h3>
              <p>{execTime.toFixed(2)}s</p>
            </div>
          </div>
          <div className="success-rate">
            <h3>Success Rate</h3>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${totalTests ? (passedCount / totalTests) * 100 : 0}%` }}
              ></div>
            </div>
            <p>{totalTests ? Math.round((passedCount / totalTests) * 100) : 0}%</p>
          </div>
        </div>

        {/* Generated Code Section */}
        <div className="output-card">
          <div className="code-header">
            <h2>Generated Test Code</h2>
            <button onClick={handleDownload} className="download-button">
              Download
            </button>
          </div>
          <div className="code-editor">
            <CodeDisplay code={generatedCode} />
          </div>
        </div>

        {/* Test Output Section */}
        <div className="output-card">
          <h2>Test Output</h2>
          <div className="code-editor">
            <CodeDisplay code={testResults.output} />
          </div>
        </div>

        {/* Test Details Section */}
        <div className="details-card">
          <h2>Test Details</h2>
          <div className="test-cases">
            {testCases.length > 0 ? (
              <table>
                <thead>
                  <tr>
                    <th>Test Case</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {testCases.map((test, index) => (
                    <tr key={index}>
                      <td>{test.test_case}</td>
                      <td>
                        <span
                          className={`status-badge ${
                            test.status === "PASSED" ? "passed" : "failed"
                          }`}
                        >
                          {test.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p>No test cases found in output</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Results;