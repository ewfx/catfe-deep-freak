# 🚀 Context-Aware API Testing Tool - DeepFreak

## 📌 Table of Contents
- [Introduction](#introduction)
- [Demo](#demo)
- [Inspiration](#inspiration)
- [What It Does](#what-it-does)
- [How We Built It](#how-we-built-it)
- [Challenges We Faced](#challenges-we-faced)
- [How to Run](#how-to-run)
- [Tech Stack](#tech-stack)
- [Team](#team)

---

## 🎯 Introduction
The Context-Aware API Testing Tool is an intelligent testing system that automatically generates, executes, and refines API tests based on OpenAPI specifications. It solves the problem of maintaining comprehensive API test suites by dynamically creating tests that cover:
- Standard success cases
- Edge cases
- Categorical value testing
- Boundary conditions
- Compliance requirements

## 🎥 Demo
📹 Video Demo: [Demo](artifacts/demo/demo-video.mp4)

## 💡 Inspiration
Traditional API testing requires manual test case creation which is:
- Time-consuming
- Often incomplete
- Difficult to maintain
- Prone to human oversight

Our tool was inspired by the need for:
1. Automated test generation that understands API context
2. Intelligent test case evolution based on feedback
3. Comprehensive coverage without manual effort

## ⚙️ What It Does
- **Automatic Test Generation**: Creates pytest or BDD tests from OpenAPI specs
- **Context-Aware Testing**: Unlike traditional testing methods that operate in isolation, we intelligently extract context by first executing GET endpoints and dynamically incorporating their responses into our LLM-powered validation framework. For APIs without GET requests, we take another approach by probing them with precisely controlled inputs, systematically analyzing their responses to extract the underlying scoring logic.
- **Self-Healing Tests**: Automatically fixes failing tests with one reflection cycle
- **Comprehensive Coverage**: Generates tests for:
  - All HTTP methods
  - Various status codes
  - Request body validation
  - Edge cases
- **Multiple Testing Styles**: Supports both pytest and Behavior-Driven Development (BDD)

## 🛠️ How We Built It
Our system integrates multiple cutting-edge techniques to optimize test generation and execution:

1. OpenAPI Schema Analysis: Automatically extracts API endpoints, methods, request/response schemas, and parameter constraints from OpenAPI specifications. This ensures a structured and comprehensive understanding of the API’s capabilities.

2. LLM-Powered Test Generation: Utilizes an open-source Large Language Model (LLM) via Ollama to generate meaningful, context-aware test cases. By analyzing API behavior, expected outcomes, and edge cases, the LLM creates intelligent test scenarios beyond traditional rule-based methods.

3. Smart Mock Data Generation: Dynamically generates realistic and context-appropriate test data based on extracted API schemas. This enables comprehensive testing by simulating various user inputs, business logic conditions, and edge cases.

4. Self-Healing Mechanism: Implements a reflection cycle where failed or ineffective test cases are analyzed, refined, and regenerated. This iterative improvement ensures better accuracy and adaptability without requiring manual intervention.

5. Test Execution Engine: Runs generated test cases, evaluates API responses, and analyzes results against expected outputs. It identifies discrepancies, logs insights, and enhances API reliability through automated validation.

By combining these approaches, our system significantly improves API test coverage, reduces manual effort, and adapts dynamically to evolving API changes, ensuring robust and efficient testing.

## 🚧 Challenges We Faced
1. **Schema Complexity**: Handling nested OpenAPI schemas and references
2. **Test Relevance**: Ensuring generated tests are meaningful and not just syntactically valid
3. **Feedback Loop**: Implementing the self-healing mechanism without infinite loops
4. **Categorical Value Extraction**: Identifying and testing all possible enum values
5. **Performance**: Balancing test comprehensiveness with execution time

## 🏃 How to Run

### Prerequisites
- Python 3.8+
- Open-source LMM
- FastAPI (for the mock API if testing locally)

### Installation
1. Clone the repository  
   ```sh
   git clone https://github.com/your-repo/context-aware-api-tester.git
   cd code/source/Backend
   ```
2. Install dependencies  
   ```sh
   pip install -r requirements.txt
   ```
### Running the Services
1. Start the API Testing Tool Server (port 8000):
   ```sh
   uvicorn api_tester:app --host 127.0.0.1 --port 8000 --reload
   ```
2. Start the Mock API Server (port 8001):
   ```sh
   uvicorn ApiCalls:app --host 127.0.0.1 --port 8001 --reload
   ```  
### Testing Workflow
🌐 Web Interface (Recommended)
1. Access Swagger UI for both services:
 - Testing Tool: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
 - Mock API: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
2. Generate Tests:
 - Navigate to /generate endpoint
 - Use this request payload:
  ```sh
  {
    "fastapi_url": "http://127.0.0.1:8001/",
    "type": "pytest"
  }
  ```
 - Click "Execute" to generate test cases
3. Run Tests:
 - Navigate to /run endpoint
 - Use this request payload:
  ```sh
  {
  "type": "pytest"
  }
  ```
 - Click "Execute" to run all generated tests

🖥️ Command Line Alternative

  ```sh
    # Start services (in separate terminals)
    uvicorn api_tester:app --host 127.0.0.1 --port 8000 --reload  # Test tool
    uvicorn ApiCalls:app --host 127.0.0.1 --port 8001 --reload    # Mock API
    
    # Generate tests via curl
    curl -X POST "http://127.0.0.1:8000/generate" \
      -H "Content-Type: application/json" \
      -d '{"fastapi_url":"http://127.0.0.1:8001/","type":"pytest"}'
    
    # Run tests via curl
    curl -X POST "http://127.0.0.1:8000/run" \
      -H "Content-Type: application/json" \
      -d '{"type":"pytest"}'
  ```  

📊 Expected Responses
1. Generate Endpoint:
   ```sh
   {
   "file_content": "Generated pytest code...",
   "status": "success"
   }
   ```
2. Run Endpoint:
   ```sh
   {
   "total_tests": 15,
   "passed_tests": 15,
   "failed_tests": 0,
   "execution_time_seconds": 2.34
   }
   ```

## 🏗️ Tech Stack
- 🔹 Backend: FastAPI, Python
- 🔹 Testing: pytest, Behave
- 🔹 AI Integration: Open-source LLM
- 🔹 Data Handling: Pandas (for mock data)

## 👥 Team
- **Kalyan** - [GitHub](https://github.com/KalyanKumarPichuka) | [LinkedIn](https://www.linkedin.com/in/kalyanp369/) 
- **Sujai** - [GitHub](https://github.com/SujaiDev) | [LinkedIn](https://www.linkedin.com/in/sujai-dev-27a854192/)
- **Shalmali** - [GitHub](https://github.com/Shalmaliiii) | [LinkedIn](https://www.linkedin.com/in/shalmali-bhalerao-085750207/)
- **Someshwar** - [GitHub](https://github.com/SomeshwarJ) | [LinkedIn](https://www.linkedin.com/in/someshwar-j-93510121a/)
