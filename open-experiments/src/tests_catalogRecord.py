import os
import json
import random
import pytest
import subprocess
import requests

# --- Configuración ---
TOKEN = "eyJhbGciOiJIUzI1NiJ9..."  # mismo token
API_URL = "http://localhost:8080"
ENTITY_TYPE = "catalogRecord"
ASPECT_NAME = "datasetProperties"   # escogemos un aspect común como datasetProperties
CATALOG_ID = 2000 + random.randint(0, 8999)
URN = f"urn:li:catalogRecord:(urn:li:dataPlatform:geoserver,{CATALOG_ID},PROD)"
ASPECT_FILE = "catalogRecordInfo.json"
DATAHUB_CLI = "../../metadata-ingestion/venv/bin/datahub"

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
        "name": f"catalog-{CATALOG_ID}",
        "description": "Descripción de prueba para catalogRecord"
    }
    with open(ASPECT_FILE, "w") as f:
        json.dump(aspect_data, f)

    run_datahub("put", "--urn", URN, "--aspect", ASPECT_NAME, "-d", ASPECT_FILE)

@pytest.fixture(scope="module")
def modified_aspect():
    aspect_data = {
        "name": f"catalog-{CATALOG_ID}-updated",
        "description": "Descripción modificada"
    }
    with open(ASPECT_FILE, "w") as f:
        json.dump(aspect_data, f)

    run_datahub("put", "--urn", URN, "--aspect", ASPECT_NAME, "-d", ASPECT_FILE)

@pytest.fixture(scope="module")
def get_aspect_output():
    return run_datahub("get", "--urn", URN, "--aspect", ASPECT_NAME)

# --- Tests ---
def test_entity_registered():
    payload = {
        "input": "*",
        "entity": ENTITY_TYPE,
        "start": 0,
        "count": 10
    }
    r = requests.post(f"{API_URL}/entities?action=search", headers=headers(), json=payload)
    assert "value" in r.json()

def test_insert_aspect(aspect_created):
    output = run_datahub("get", "--urn", URN, "--aspect", ASPECT_NAME)
    assert f"catalog-{CATALOG_ID}" in output

def test_check_urn_exists():
    output = run_datahub("exists", "--urn", URN)
    assert "true" in output.lower()

def test_get_aspect(aspect_created):
    output = run_datahub("get", "--urn", URN, "--aspect", ASPECT_NAME)
    assert "name" in output

def test_graphql_entitytype():
    graphql_query = {"query": '{ __type(name: "EntityType") { enumValues { name } } }'}
    r = requests.post(f"{API_URL}/api/graphql", headers=headers(), json=graphql_query)
    enum_values = r.json().get("data", {}).get("__type", {}).get("enumValues", [])
    assert any(ev.get("name") == "CATALOG_RECORD" for ev in enum_values)

def test_graphql_search_catalogrecord():
    query = {
        "query": """
        query {
          search(input: {
            type: CATALOG_RECORD,
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
    response_json = r.json()
    print("\n[DEBUG] GraphQL search_catalogrecord response:", json.dumps(response_json, indent=2))
    results = response_json.get("data", {}).get("search", {}).get("searchResults")
    assert results is not None

def test_validate_aspect_structure(get_aspect_output):
    aspect_json = json.loads(get_aspect_output)
    info = aspect_json.get("datasetProperties", {})
    assert info.get("name") == f"catalog-{CATALOG_ID}"

def test_modify_aspect(modified_aspect):
    output = run_datahub("get", "--urn", URN, "--aspect", ASPECT_NAME)
    assert f"catalog-{CATALOG_ID}-updated" in output

def test_verify_aspect_update():
    output = run_datahub("get", "--urn", URN, "--aspect", ASPECT_NAME)
    assert f"catalog-{CATALOG_ID}-updated" in output

def test_search_by_name():
    query = {
        "query": f'''
        query {{
          search(input: {{
            type: CATALOG_RECORD,
            query: "catalog-{CATALOG_ID}-updated",
            start: 0,
            count: 10
          }}) {{
            searchResults {{
              entity {{ urn }}
            }}
          }}
        }}
        '''
    }
    r = requests.post(f"{API_URL}/api/graphql", headers=headers(), json=query)
    response_json = r.json()
    print("\n[DEBUG] GraphQL search_by_name response:", json.dumps(response_json, indent=2))
    results = response_json.get("data", {}).get("search", {}).get("searchResults", [])
    assert any(res.get("entity", {}).get("urn") == URN for res in results)

def test_query_catalogrecord_by_urn():
    query = {
        "query": f'''
        query {{
          catalogRecord(urn: "{URN}") {{
            urn
            type
            properties {{
              name
              description
            }}
          }}
        }}
        '''
    }
    r = requests.post(f"{API_URL}/api/graphql", headers=headers(), json=query)
    data = r.json().get("data", {}).get("catalogRecord", {})
    assert data.get("urn") == URN
