import os
import subprocess
import re
import requests
import ollama
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from pydantic import BaseModel
import zipfile
import shutil
import xmltodict

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FASTAPI_URL = "http://localhost:8001"
UPLOAD_DIRECTORY = "src"


class GenerateRequest(BaseModel):
    fastapi_url: str
    type: str
    src_folder: str = None


class RunRequest(BaseModel):
    type: str


# -----------------------------------------------------------------------------
#  PROMPTS
# -----------------------------------------------------------------------------
BDD_PROMPT = (
    "Generate BDD (Behavior-Driven Development) test cases for a FastAPI application. "
    "Write scenarios in Gherkin syntax and provide step definitions in Python using Behave."
)


@app.post("/generate-coverage")
async def generate_coverage_report():
    """
    Generate code coverage report, handling both successful and failed test scenarios
    """
    try:
        # Ensure necessary directories exist
        os.makedirs("coverage_reports", exist_ok=True)

        # Run coverage with detailed output
        coverage_commands = [
            # Erase previous coverage data
            "coverage erase",

            # Run tests with coverage (use --continue-on-collection-errors to handle test failures)
            "coverage run -m pytest generated_tests.py --continue-on-collection-errors",

            # Generate XML report (for detailed parsing)
            "coverage xml -o coverage_reports/coverage.xml",

            # Generate HTML report (for human-readable view)
            "coverage html -d coverage_reports/html",

            # Generate JSON report
            "coverage json -o coverage_reports/coverage.json"
        ]

        # Track test and coverage results
        test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "errors": []
        }

        # Execute commands with comprehensive error handling
        for cmd in coverage_commands:
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()

            # Parse pytest output for test results
            if "pytest" in cmd:
                # Count test results
                total_match = re.search(r'collected\s+(\d+)\s+item', stdout)
                passed_match = re.search(r'(\d+)\s+passed', stdout)
                failed_match = re.search(r'(\d+)\s+failed', stdout)

                test_results['total_tests'] = int(total_match.group(1)) if total_match else 0
                test_results['passed_tests'] = int(passed_match.group(1)) if passed_match else 0
                test_results['failed_tests'] = int(failed_match.group(1)) if failed_match else 0

                # Capture detailed error information
                if test_results['failed_tests'] > 0:
                    error_matches = re.findall(r'(FAILED.*?)\n\n', stdout, re.DOTALL)
                    test_results['errors'] = error_matches

            # Check for command execution errors
            if process.returncode != 0:
                return {
                    "error": f"Command failed: {cmd}",
                    "stderr": stderr,
                    "test_results": test_results
                }

        # Check if reports exist before parsing
        coverage_report = {"test_results": test_results}

        # Parse XML coverage report if it exists
        try:
            with open("coverage_reports/coverage.xml", "r") as f:
                coverage_xml = xmltodict.parse(f.read())

            # Extract coverage metrics
            coverage_report.update({
                "coverage_summary": {
                    "total_lines": int(coverage_xml['coverage']['@lines']),
                    "covered_lines": int(coverage_xml['coverage']['@covered']),
                    "coverage_percentage": round(
                        float(coverage_xml['coverage']['@line-rate']) * 100, 2
                    )
                }
            })
        except Exception as xml_error:
            coverage_report["coverage_error"] = str(xml_error)

        # Add report paths
        sys_path = "C:/Users/senth/Studies/WF-hackathon/DeepFreak/"
        coverage_report["report_paths"] = {
            "xml": sys_path + "coverage_reports/coverage.xml",
            "html": sys_path + "coverage_reports/html/index.html",
            "json": sys_path + "coverage_reports/coverage.json"
        }

        return coverage_report

    except Exception as e:
        return {
            "error": f"Failed to generate coverage report: {str(e)}",
            "details": str(e)
        }


@app.post("/generate")
async def generate(
        fastapi_url: str = Form(...),
        type: str = Form(...),
        source_file: UploadFile = File(None)
):
    try:
        # Handle file upload if provided
        if source_file:
            # Ensure upload directory exists
            os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

            # Clear previous uploads
            for existing in os.listdir(UPLOAD_DIRECTORY):
                path = os.path.join(UPLOAD_DIRECTORY, existing)
                if os.path.isfile(path):
                    os.unlink(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)

            # Save uploaded file
            file_location = os.path.join(UPLOAD_DIRECTORY, source_file.filename)
            with open(file_location, "wb+") as file_object:
                file_object.write(await source_file.read())

            # If it's a zip file, extract it
            if source_file.filename.endswith('.zip'):
                with zipfile.ZipFile(file_location, 'r') as zip_ref:
                    zip_ref.extractall(UPLOAD_DIRECTORY)
                os.unlink(file_location)  # Remove zip after extraction

            # Update src_folder to the uploaded directory
            src_folder = UPLOAD_DIRECTORY

        # Validate fastapi_url
        fastapi_url = fastapi_url.rstrip('/')
        openapi_url = f"{fastapi_url}/openapi.json"

        # Verify OpenAPI spec
        try:
            response = requests.get(openapi_url)
            response.raise_for_status()
            openapi_data = response.json()
            if not openapi_data:
                return {"error": "Empty OpenAPI specification received"}
        except requests.RequestException as e:
            return {"error": f"Could not fetch OpenAPI schema: {str(e)}"}

        # Read source code contents if a folder is specified or uploaded
        source_contents = read_source_code_contents(src_folder)

        # Generate tests based on type
        if type == "pytest":
            result = generate_test_code_pytest(fastapi_url, source_contents)
        elif type == "bdd":
            result = generate_test_code_bdd(fastapi_url, source_contents)
        else:
            return {"error": "Invalid test type specified"}

        if "error" in result:
            return result
        if not result.get("file_content"):
            return {"error": "Test generation failed - no output produced"}

        return result

    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}


@app.post("/run")
async def run(request: RunRequest):
    try:
        if request.type == "pytest":
            return run_tests()
        elif request.type == "bdd":
            return run_bdd_tests()
        else:
            raise HTTPException(status_code=400, detail="Invalid test type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def read_source_code_contents(src_folder=None):
    """
    Read contents of source code files
    """
    if not src_folder:
        src_folder = UPLOAD_DIRECTORY

    source_contents = {}
    for root, dirs, files in os.walk(src_folder):
        for file in files:
            if file.endswith(('.py')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        source_contents[file_path] = f.read()
                except Exception as e:
                    print(f"Could not read {file_path}: {e}")

    return source_contents


# -----------------------------------------------------------------------------
#  Template for final test file
# -----------------------------------------------------------------------------
TEST_TEMPLATE = """
import os
import requests
import pytest

BASE_URL = os.getenv('TEST_API_URL', {FASTAPI_URL})

{test_functions}
"""

# -----------------------------------------------------------------------------
#  PROMPTS
# -----------------------------------------------------------------------------
PLAN_PROMPT = (
    "Generate a test plan for a fictional REST API with categories like "
    "authorization, boundary, and error handling. Include a few scenarios each."
)

# -----------------------------------------------------------------------------
#  Template for final BDD test structure
# -----------------------------------------------------------------------------
FEATURE_TEMPLATE = """
Feature: API Testing

{scenarios}
"""

STEP_DEFINITION_TEMPLATE = """
from behave import given, when, then
import requests
import os

BASE_URL = os.getenv('TEST_API_URL', {FASTAPI_URL})

{step_definitions}
"""


def generate_test_code_bdd(fastapi_url, source_contents):
    print("\n----- Generating BDD Test Cases from FastAPI Schema -----\n")
    dynamic_prompt = generate_dynamic_prompt_bdd(fastapi_url)

    if dynamic_prompt.startswith("ERROR:"):
        print(dynamic_prompt)
        return

    raw_response = call_ollama(dynamic_prompt)
    if raw_response.startswith("ERROR:"):
        print(raw_response)
        return

    feature_content, step_definitions = extract_bdd_from_response(raw_response)

    # Write the feature file
    feature_file = "features/api_tests.feature"
    os.makedirs(os.path.dirname(feature_file), exist_ok=True)
    with open(feature_file, "w", encoding="utf-8") as f:
        f.write(feature_content)

    # Write the step definition file
    step_def_file = "features/steps/step_definitions.py"
    os.makedirs(os.path.dirname(step_def_file), exist_ok=True)
    with open(step_def_file, "w", encoding="utf-8") as f:
        f.write(step_definitions)

    print(f"Successfully generated BDD tests in '{feature_file}' and '{step_def_file}'")


def generate_dynamic_prompt_bdd(fastapi_url):
    api_tests = extract_fastapi_routes(fastapi_url)
    if isinstance(api_tests, str) and api_tests.startswith("ERROR"):
        return api_tests

    scenarios = ""
    step_definitions = ""

    for scenario in api_tests:
        method = scenario['method']
        endpoint = scenario['endpoint']
        body_required = scenario['bodyRequired']
        body_example = scenario['bodyExample']
        expected_status = scenario['expected_status']
        descriptions = scenario['descriptions']

        scenario_name = f"Scenario: Test {method} {endpoint}"
        steps = f"""
        Given the API is running
        When I send a {method} request to "{endpoint}"
        """

        if body_required:
            steps += f"And I include the request body {body_example}\n"

        steps += f"Then the response status code should be one of {expected_status}\n"

        scenarios += f"{scenario_name}\n{steps}\n"

    additional_context = fetch_get_endpoints(api_tests, fastapi_url)

    GENERATION_PROMPT = f"""
    Generate a feature file and step definitions in Python using Behave for the following API test scenarios:

    {scenarios}

    The feature file should be structured as follows:
    ```gherkin
    {FEATURE_TEMPLATE}
    ```
    Instead of filling "sample_field_name" in the field value, understand the context from {additional_context} and generate and fill meaning ful mock data to test.
    The step definitions should follow this structure:
    ```python
    {STEP_DEFINITION_TEMPLATE}
    ```
    """
    return GENERATION_PROMPT


def extract_bdd_from_response(llm_response: str):
    pattern_feature = r"```gherkin\s*(.*?)\s*```"
    pattern_steps = r"```python\s*(.*?)\s*```"

    feature_match = re.search(pattern_feature, llm_response, re.DOTALL)
    step_match = re.search(pattern_steps, llm_response, re.DOTALL)

    feature_content = feature_match.group(1).strip() if feature_match else ""
    step_definitions = step_match.group(1).strip() if step_match else ""

    return feature_content, step_definitions


# -----------------------------------------------------------------------------
#  Run BDD Tests
# -----------------------------------------------------------------------------
def run_bdd_tests():
    print("\n----- Running BDD Tests with Behave -----\n")
    try: 
        output = subprocess.check_output(["behave", "features"], shell=True, text=True)
        return parse_json(output)
    except subprocess.CalledProcessError as e:
        return parse_json(e.output)


def fetch_openapi_schema(fastapi_url):
    try:
        response = requests.get(fastapi_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return f"ERROR: Could not fetch OpenAPI schema: {e}"


def resolve_ref(ref, openapi_data):
    ref_path = ref.replace("#/components/schemas/", "")
    return openapi_data.get("components", {}).get("schemas", {}).get(ref_path, {})

def extract_categories(description):
    """Extracts category options from the description string if formatted as a list."""
    match = re.search(r"\[([^\]]+)\]", description)
    if match:
        return [item.strip() for item in match.group(1).split(",")]
    return None


def generate_example_from_schema(schema, openapi_data):
    if not schema:
        return None, None , None 

    if "$ref" in schema:
        schema = resolve_ref(schema["$ref"], openapi_data)

    example = {}
    descriptions = {}
    categories = {}

    properties = schema.get("properties", {})

    for key, value in properties.items():
        if "$ref" in value:
            resolved_schema = resolve_ref(value["$ref"], openapi_data)
            example[key], descriptions[key], categories[key]  = generate_example_from_schema(resolved_schema, openapi_data)
        else:
            # Extract description if available
            if "description" in value:
                descriptions[key] = value.get("description", "")
                extracted_categories = extract_categories(value.get("description", ""))
                if extracted_categories:
                    categories[key] = extracted_categories

            # Generate example value based on type
            if "example" in value:
                example[key] = value["example"]
            elif "type" in value:
                if value["type"] == "string":
                    example[key] = f"sample_{key}"
                elif value["type"] == "integer":
                    example[key] = 123
                elif value["type"] == "boolean":
                    example[key] = True
                elif value["type"] == "array":
                    item_example, item_description, item_categories = generate_example_from_schema(value["items"], openapi_data)
                    example[key] = [item_example]
                    descriptions[key] = item_description
                    categories[key] = item_categories
                elif value["type"] == "number":
                    example[key] = 5000
                elif value["type"] == "object":
                    example[key], descriptions[key], categories[key] = generate_example_from_schema(value, openapi_data)
            else:
                example[key] = None
    return example, descriptions, categories
    

def extract_fastapi_routes(fastapi_url):
    try:
        openapi_url = f"{fastapi_url}/openapi.json"
        response = requests.get(openapi_url)
        response.raise_for_status()
        openapi_data = response.json()

        if not isinstance(openapi_data, dict):
            raise ValueError("Invalid OpenAPI specification format")

        test_scenarios = []
        paths = openapi_data.get("paths", {})

        if not paths:
            raise ValueError("No paths found in OpenAPI specification")

        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue

            for method, details in methods.items():
                if method.lower() not in ['get', 'post', 'put', 'delete', 'patch']:
                    continue

                request_body_required = "requestBody" in details
                body_example = None
                description = None
                categories = None

                if request_body_required:
                    content = details.get("requestBody", {}).get("content", {})
                    if "application/json" in content:
                        schema = content["application/json"].get("schema", {})
                        body_example, description, categories = generate_example_from_schema(schema, openapi_data)

                test_case = {
                    "method": method.upper(),
                    "endpoint": path,
                    "bodyRequired": request_body_required,
                    "bodyExample": body_example,
                    "expected_status": list(details.get("responses", {}).keys()),
                    "descriptions": description if description else None,
                    "categories" : categories if categories else None
                }
                print(test_case)
                test_scenarios.append(test_case)

        if not test_scenarios:
            raise ValueError("No valid API endpoints found to test")

        return test_scenarios

    except Exception as e:
        print(f"Error extracting routes: {str(e)}")
        raise ValueError(f"Failed to extract API routes: {str(e)}")


# For more context
def fetch_get_endpoints(api_tests, base_url):
    responses = {}

    for scenario in api_tests:
        method = scenario['method']
        endpoint = scenario['endpoint']
        if method == 'GET' and not scenario.get('bodyRequired', False):
            url = f"{base_url}{endpoint}"
            try:
                response = requests.get(url)
                responses[endpoint] = {
                    'status_code': response.status_code,
                    'json': response.json() if response.headers.get(
                        'Content-Type') == 'application/json' else response.text
                }
            except requests.RequestException as e:
                responses[endpoint] = {'error': str(e)}

    return responses


def generate_dynamic_prompt(fastapi_url, source_contents=None):
    api_tests = extract_fastapi_routes(fastapi_url)
    if isinstance(api_tests, str) and api_tests.startswith("ERROR"):
        return api_tests

    test_cases = ""
    for scenario in api_tests:
        method = scenario['method']
        endpoint = scenario['endpoint']
        body_required = scenario['bodyRequired']
        body_example = scenario['bodyExample']
        expected_status = scenario['expected_status']
        descriptions = scenario['descriptions']
        categories = scenario['categories']

        test_name = f"test_{method.lower()}_{endpoint.strip('/').replace('/', '_').replace('{', '').replace('}', '')}"
        print(test_name)
        test_cases += f"- {test_name}: {method} {endpoint} => Expected {expected_status}\n"

        if body_required:
            test_cases += f"  Request Body: {body_example}\n"
            test_cases += f" Description: {descriptions}\n"
            test_cases += f" Categories : {categories}\n"

    additional_context = fetch_get_endpoints(api_tests, fastapi_url)

    source_code_context = ""

    if source_contents:
        source_code_context = "\n\n### Source Code Context:\n"
        for file_path, content in source_contents.items():
            source_code_context += f"# File: {file_path}\n{content[:500]}...\n\n"

    print(source_code_context)

    GENERATION_PROMPT = f"""
            You are a highly skilled AI specializing in writing robust API test cases using pytest. Your task is to generate a complete and executable Python test file based on the following requirements:
            Below is a skeleton of our test file using pytest. Fill in the 'test_functions'
            placeholder with tests for the following real API behavior:

            {test_cases}
            {source_code_context}

        Requirements:
        1. Only return valid Python code, wrapped in triple backticks (no extra commentary).
        2. Keep 'BASE_URL' with {fastapi_url}.
        3. Provide all tests in place of {{test_functions}}.
        4. Each test asserts the correct status code (and JSON if needed).
        5. The final output should be a complete Python file that can run under pytest.
        6. In the {test_cases} there is a request body. Instead of filling "sample_field_name" in the field value, understand the context from {additional_context} and generate and fill meaning ful mock data to test.
        7. The mock data generated should be completely unique and different from data which already exists in the DB. 
        9. Strictly Do not modify any existing data. The CRUD operations should be performed on data which does not already exist in DB.
        10. If an API schema includes **categorical values**  field of {test_cases}, generate:
            - Generate a **separate test case for each possible categorical value**.  
            - Create tests covering **combinations of multiple categorical values**, where applicable.  
            - Validate behavior against **invalid or out-of-scope categorical values**.  
        11. Extract categorical values from descriptions (e.g., "City" may include **Bangalore, Pune, Kolkata, etc.**)  
            - **Each value must be tested individually.**
            - **Also, test for invalid categorical values** (e.g., random strings, out-of-scope values).  

        12. To maximize test coverage, further expand the test scenarios by integrating quantitative values (e.g., numerical data) alongside categorical values. Expand **numerical test cases** for fields like "Distance" by covering:
            - **Minimum allowed value**
            - **Maximum allowed value**
            - **Negative values**
            - **Zero**
            - **Extremely large values**  

        13. Generate at least **5+ test cases** for APIs with categorical data to ensure proper validation.
        14. Enclose all property name in double quotes for the json payload to post. 
        15. Do not assume any negative scenarios and assert them to failed response code. Such as amount being negative. 
        Skeleton:
        ```python
        {TEST_TEMPLATE}"""


    return GENERATION_PROMPT


# -----------------------------------------------------------------------------
#  call_ollama: Sends a prompt to an LLM via OpenRouter
# -----------------------------------------------------------------------------
def call_ollama(prompt: str) -> str:
    try:
        response = ollama.chat(
            model='gemma:2b',  # You can change this to your preferred model
            messages=[
                {
                    'role': 'system',
                    'content': (
                        "You are an AI that generates or updates an API test plan or code "
                        "based on user instructions. Reply with well-structured text or code. "
                        "Do NOT include extra commentary outside code blocks."
                    )
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            options={
                'temperature': 0.0
            }
        )
        return response['message']['content'].strip()
    except Exception as e:
        return f"ERROR: Ollama request failed: {e}"


# -----------------------------------------------------------------------------
#  extract_code_from_response
# -----------------------------------------------------------------------------
def extract_code_from_response(llm_response: str) -> str:
    pattern = r"```(?:python)?\s*(.*?)\s*```"
    match = re.search(pattern, llm_response, re.DOTALL)
    if match:
        return match.group(1).strip()
    return llm_response.strip()


# -----------------------------------------------------------------------------
#  plan
# -----------------------------------------------------------------------------
def generate_plan():
    print("\n----- Fetching a Test Plan from the LLM -----\n")
    plan = call_ollama(PLAN_PROMPT)
    print(plan)
    print("\n----- End of Test Plan -----\n")


# -----------------------------------------------------------------------------
#  generate pytest
# -----------------------------------------------------------------------------
def generate_test_code_pytest(fastapi_url, source_contents):
    try:
        dynamic_prompt = generate_dynamic_prompt(fastapi_url, source_contents)

        if dynamic_prompt.startswith("ERROR:"):
            return {"error": dynamic_prompt}

        raw_response = call_ollama(dynamic_prompt)
        if raw_response.startswith("ERROR:"):
            return {"error": raw_response}

        python_code = extract_code_from_response(raw_response)
        if not python_code:
            return {"error": "No test code generated by LLM"}

        output_file = "generated_tests.py"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(python_code)
            return {"file_content": python_code}

        except OSError as e:
            return {"error": f"Could not write to {output_file}: {e}"}

    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}


# -----------------------------------------------------------------------------
#  run
# -----------------------------------------------------------------------------
def parse_json(output):
    test_session = {"total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0, 
        "execution_time_seconds": 0.0
    }
    summary_match = re.search(r'(\d+)\s+failed,?\s+(\d+)\s+passed', output)
    if summary_match:
        test_session['failed_tests'] = int(summary_match.group(1))
        test_session['passed_tests'] = int(summary_match.group(2))
        test_session['total_tests'] = test_session['failed_tests'] + test_session['passed_tests']
    else:
        passed_only_match = re.search(r'(\d+)\s+passed', output)
        if passed_only_match:
            test_session['passed_tests'] = int(passed_only_match.group(1))
            test_session['total_tests'] = test_session['passed_tests']

    time_match = re.search(r'(\d+\.\d+)s', output)
    if time_match:
        test_session['execution_time_seconds'] = float(time_match.group(1))

    if (test_session['failed_tests']):
        test_session["failed_test_names"] = re.findall(r'generated_tests.py::(\S+)\sFAILED', output)

    return test_session


def run_tests():
    print("\n----- Running the generated tests with pytest -----\n")
    try:
        output = subprocess.check_output(['pytest', 'generated_tests.py', '-v'], text=True)
        print(output)
        return parse_json(output)

    except subprocess.CalledProcessError as e:
        print(e.output)
        return parse_json(e.output)


# -----------------------------------------------------------------------------
#  feedback
# -----------------------------------------------------------------------------
def handle_feedback(user_feedback: str):
    print("\n----- Processing feedback with LLM -----\n")

    prompt_text = f"""
        We have the above logic for '/api/endpoint', '/api/nonexistent', and '/api/error'.
        User feedback: '{user_feedback}'

        Please update or expand the test code using the same approach. 
        The skeleton is:
        ```python
        {TEST_TEMPLATE}
        ```
        Insert your changes in {{test_functions}}, produce valid Python code in triple backticks.
    """

    response = call_ollama(prompt_text)
    print(response)
    print("\n----- End of Feedback Response -----\n")
