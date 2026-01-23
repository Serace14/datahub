import os
import json
import random
import pytest
import subprocess
import requests
import base64
import time

# --- Configuración ---
TOKEN = os.getenv("DATAHUB_TOKEN", "eyJhbGciOiJIUzI1NiJ9.eyJhY3RvclR5cGUiOiJVU0VSIiwiYWN0b3JJZCI6ImRhdGFodWIiLCJ0eXBlIjoiUEVSU09OQUwiLCJ2ZXJzaW9uIjoiMiIsImp0aSI6IjRiNTYxNWQyLWQ1ZmYtNGVkYy1iZjQ2LTM2ZjVhZjRiODE4NSIsInN1YiI6ImRhdGFodWIiLCJleHAiOjE3NjM4ODkxMjMsImlzcyI6ImRhdGFodWItbWV0YWRhdGEtc2VydmljZSJ9.DhiGqCmdmowSS5TRLRkoYDuPNtp_cLsKZR7JlLtMDHI")
API_URL = "http://localhost:8080"
ENTITY_TYPE = "platformResource"
ASPECT_NAME = "platformResourceInfo"
RESOURCE_ID = f"resource-{random.randint(1000, 9999)}"
URN = f"urn:li:platformResource:looker-resource-{RESOURCE_ID}"
ASPECT_FILE = "platformresourceinfo.json"
DATAHUB_CLI = "../metadata-ingestion/venv/bin/datahub"

# --- Helpers ---
def run_datahub(*args):
    result = subprocess.run([DATAHUB_CLI, *args], capture_output=True, text=True)
    return result.stdout + result.stderr

def headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

# --- Fixtures ---
@pytest.fixture(scope="module")
def aspect_created():
    aspect_data = {
        "resourceType": "table",
        "primaryKey": "id123",
        "secondaryKeys": ["sk1", "sk2"],
        "value": {
            "blob": base64.b64encode(b'{"foo":"bar"}').decode("utf-8"),
            "contentType": "JSON",
            "schemaType": "NONE"
        }
    }
    with open(ASPECT_FILE, "w") as f:
        json.dump(aspect_data, f)

    run_datahub("put", "--urn", URN, "--aspect", ASPECT_NAME, "-d", ASPECT_FILE)

@pytest.fixture(scope="module")
def modified_aspect():
    aspect_data = {
        "resourceType": "view",
        "primaryKey": "id456",
        "secondaryKeys": ["sk3"],
        "value": {
            "blob": base64.b64encode(b'{"hello":"world"}').decode("utf-8"),
            "contentType": "XML",
            "schemaType": "NONE"
        }
    }
    with open(ASPECT_FILE, "w") as f:
        json.dump(aspect_data, f)

    run_datahub("put", "--urn", URN, "--aspect", ASPECT_NAME, "-d", ASPECT_FILE)

@pytest.fixture(scope="module")
def get_aspect_output():
    return run_datahub("get", "--urn", URN, "--aspect", ASPECT_NAME)

# --- Tests ---
def test_entity_registered():
    payload = {"input": "*", "entity": ENTITY_TYPE, "start": 0, "count": 10}
    r = requests.post(f"{API_URL}/entities?action=search", headers=headers(), json=payload)
    assert "value" in r.json()

def test_insert_aspect(aspect_created):
    output = run_datahub("get", "--urn", URN, "--aspect", ASPECT_NAME)
    assert "table" in output

def test_check_urn_exists():
    output = run_datahub("exists", "--urn", URN)
    assert "true" in output.lower()

def test_get_aspect(aspect_created):
    output = run_datahub("get", "--urn", URN, "--aspect", ASPECT_NAME)
    assert "primaryKey" in output

def test_graphql_entitytype():
    graphql_query = {"query": '{ __type(name: "EntityType") { enumValues { name } } }'}
    r = requests.post(f"{API_URL}/api/graphql", headers=headers(), json=graphql_query)
    enum_values = r.json().get("data", {}).get("__type", {}).get("enumValues", [])
    assert any(ev.get("name") == "PLATFORM_RESOURCE" for ev in enum_values)

def test_graphql_search_platformresource():
    query = {
        "query": """
        query {
          search(input: {
            type: PLATFORM_RESOURCE,
            query: "*",
            start: 0,
            count: 10
          }) {
            searchResults {
              entity {
                urn
                type
              }
            }
          }
        }
        """
    }
    r = requests.post(f"{API_URL}/api/graphql", headers=headers(), json=query)
    results = r.json().get("data", {}).get("search", {}).get("searchResults")
    assert results is not None

def test_validate_aspect_structure(get_aspect_output):
    aspect_json = json.loads(get_aspect_output)
    info = aspect_json.get("platformResourceInfo", {})
    assert info.get("resourceType") == "table"

def test_modify_aspect(modified_aspect):
    output = run_datahub("get", "--urn", URN, "--aspect", ASPECT_NAME)
    assert "view" in output

def test_verify_aspect_update():
    output = run_datahub("get", "--urn", URN, "--aspect", ASPECT_NAME)
    assert "id456" in output

def test_query_platformresource_by_urn():
    query = {
        "query": f'''
        query {{
          platformResource(urn: "{URN}") {{
            urn
            type
            id
            info {{
              resourceType
              primaryKey
            }}
          }}
        }}
        '''
    }
    r = requests.post(f"{API_URL}/api/graphql", headers=headers(), json=query)
    data = r.json().get("data", {}).get("platformResource", {})
    assert data.get("urn") == URN
    assert data.get("info", {}).get("resourceType") in ["table", "view"]

