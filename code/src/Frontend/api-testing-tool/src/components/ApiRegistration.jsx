import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import testingImage from "../assets/api-testing.png";
import "./ApiRegistration.css";

const ApiRegistration = () => {
  const [fastApiLink, setFastApiLink] = useState("");
  const [apiSpec, setApiSpec] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [testType, setTestType] = useState("pytest");
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [generatedCode, setGeneratedCode] = useState("");
  const navigate = useNavigate();

  const fetchOpenApiSpec = async () => {
    setIsLoading(true);
    try {
      let url = fastApiLink.endsWith("/") ? fastApiLink : `${fastApiLink}/`;
      url = url.endsWith("openapi.json") ? url : `${url}openapi.json`;
      
      const response = await axios.get(url, {
        headers: {
          'Accept': 'application/json'
        }
      });
      
      setApiSpec(JSON.stringify(response.data, null, 2));
      setMessage({ text: "OpenAPI specification fetched successfully.", type: "success" });
    } catch (error) {
      console.error("Error fetching OpenAPI spec:", error);
      setMessage({
        text: error.response?.data?.detail || 
             "Failed to fetch OpenAPI specification. Please check the link and ensure the backend is running.",
        type: "error"
      });
      setApiSpec("");
    } finally {
      setIsLoading(false);
    }
  };

  const parseTestOutput = (output) => {
    if (!output) return [];
    const lines = typeof output === "string" ? output.split("\n") : [];
    const testCases = [];
    
    lines.forEach(line => {
      if (line.includes('def test_')) {
        const testName = line.split('def ')[1].split('(')[0];
        testCases.push({ test_case: testName, status: 'PENDING' });
      }
    });
    
    return testCases;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!apiSpec) {
      setMessage({ text: "No OpenAPI specification to register.", type: "error" });
      return;
    }
  
    try {
      setIsRegistering(true);
      setRegistrationSuccess(false);
      setMessage({ text: "Generating test cases...", type: "info" });
  
      // Generate tests
      const generateResponse = await axios.post(
        "http://localhost:8000/generate",
        {
          fastapi_url: fastApiLink.replace(/\/$/, ""),
          type: testType
        }
      );
      console.log("Generate response:", generateResponse.data);
  
      // Store generated code
      const generatedData = generateResponse.data;
      console.log("Generated data:", generatedData);
  
      if (!generatedData || !generatedData.file_content) {
        console.log("Generated data:", generatedData.error);
        throw new Error(generatedData?.error || "No test code generated");
      }
  
      setGeneratedCode(generatedData.file_content);
      setMessage({ text: "Test cases generated, now executing...", type: "info" });
  
      // Run tests - add error handling
      const runResponse = await axios.post(
        "http://localhost:8000/run",
        { type: testType }
      ).catch(error => {
        // Handle network errors
        const errorData = error.response?.data || { error: error.message };
        throw new Error(errorData.error || errorData.detail || "Test execution failed");
      });
  
      // Validate response structure
      if (!runResponse.data || typeof runResponse.data.passed_tests === 'undefined') {
        throw new Error("Invalid test results format");
      }
  
      // Combine results
      const completeResults = {
        output: generatedData.file_content,
        executionMetrics: runResponse.data,
        testCases: parseTestOutput(generatedData.file_content)
      };
  
      setTestResults(completeResults);
      setMessage({
        text: `Testing completed! ${runResponse.data.passed_tests} tests passed`,
        type: "success"
      });
      setRegistrationSuccess(true);
  
    } catch (error) {
      console.error("Full error:", error);
      setMessage({
        text: error.message,
        type: "error"
      });
      setRegistrationSuccess(false);
    } finally {
      setIsRegistering(false);
    }
  };

  const handleViewResults = () => {
    navigate("/results", { 
      state: { 
        testResults,
        generatedCode,
        apiDetails: {
          url: fastApiLink,
          type: testType,
          registration_time: new Date().toISOString()
        }
      } 
    });
  };

  return (
    <div className="api-registration-container">
      <header className="api-registration-header">
        <h1>API Testing Tool</h1>
        <p>Simplify API Testing with Automated Test Case Generation</p>
      </header>

      <div className="api-registration-main-content">
        <div className="api-registration-image-section">
          <img
            src={testingImage}
            alt="API Testing"
            className="api-registration-image"
          />
        </div>

        <div className="api-registration-form-section">
          <div className="api-registration-form-container">
            <h2>Register Your API</h2>
            <p className="api-registration-subtitle">
              Input your FastAPI URL to fetch and register the OpenAPI specification.
            </p>

            <form onSubmit={handleSubmit} className="api-registration-form">
              <div className="api-registration-input-group">
                <label htmlFor="fastApiLink">FastAPI Link:</label>
                <input
                  type="url"
                  id="fastApiLink"
                  placeholder="http://localhost:8000"
                  value={fastApiLink}
                  onChange={(e) => setFastApiLink(e.target.value)}
                  required
                  pattern="https?://.+"
                />
              </div>

              <div className="api-registration-input-group">
                <label htmlFor="testType">Test Type:</label>
                <select
                  id="testType"
                  value={testType}
                  onChange={(e) => setTestType(e.target.value)}
                  className="api-registration-select"
                  required
                >
                  <option value="pytest">Pytest</option>
                  <option value="bdd">BDD</option>
                </select>
              </div>

              <div className="api-registration-button-group">
                <button
                  type="button"
                  onClick={fetchOpenApiSpec}
                  disabled={!fastApiLink || isLoading}
                  className="api-registration-primary-button"
                >
                  {isLoading ? "Fetching..." : "Fetch OpenAPI Spec"}
                </button>
                <button
                  type="submit"
                  disabled={!apiSpec || isRegistering}
                  className="api-registration-primary-button"
                >
                  {isRegistering ? (
                    <span className="registering-dots">
                      Registering<span className="dot">.</span><span className="dot">.</span><span className="dot">.</span>
                    </span>
                  ) : "Register API"}
                </button>
              </div>
            </form>

            {apiSpec && (
              <div className="api-registration-spec-container">
                <details className="api-registration-spec">
                  <summary>View OpenAPI Specification</summary>
                  <pre>{apiSpec}</pre>
                </details>
              </div>
            )}

            {message && (
              <p className={`api-registration-message ${message.type}`}>
                {message.text}
              </p>
            )}

            <div className="api-registration-action-buttons">
              <button
                className="api-registration-view-button"
                onClick={() => navigate("/registered-apis")}
              >
                View Registered APIs
              </button>
              
              {registrationSuccess && (
                <button
                  className="api-registration-results-button"
                  onClick={handleViewResults}
                >
                  View Test Results
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ApiRegistration;