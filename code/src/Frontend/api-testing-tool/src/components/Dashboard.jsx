import React, { useState } from "react";
import axios from "axios";
import Results from "./Results";

const Dashboard = () => {
  const [testResults, setTestResults] = useState(null);

  const runTests = async () => {
    try {
      const response = await axios.post("http://localhost:8000/run-tests");
      setTestResults(response.data);
    } catch (error) {
      console.error("Error running tests:", error);
    }
  };

  return (
    <div>
      <h2>Dashboard</h2>
      <button onClick={runTests}>Run Tests</button>
      {testResults && <Results testResults={testResults} />}
    </div>
  );
};

export default Dashboard;