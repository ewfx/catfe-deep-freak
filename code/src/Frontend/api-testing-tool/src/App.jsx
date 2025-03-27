import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import ApiRegistration from "./components/ApiRegistration";
import Dashboard from "./components/Dashboard";
import RegisteredApis from "./components/RegisteredApis";
import Results from "./components/Results";

const App = () => {
  return (
    <div className="app-container">
      <Router>
        <Routes>
          <Route path="/" element={<ApiRegistration />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/registered-apis" element={<RegisteredApis />} />
          <Route path="/results" element={<Results />} />
        </Routes>
      </Router>
    </div>
  );
};

export default App;