import os
import json
import random
import pytest
import subprocess
import requests

# --- Configuración ---
TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhY3RvclR5cGUiOiJVU0VSIiwiYWN0b3JJZCI6ImRhdGFodWIiLCJ0eXBlIjoiUEVSU09OQUwiLCJ2ZXJzaW9uIjoiMiIsImp0aSI6IjRiNTYxNWQyLWQ1ZmYtNGVkYy1iZjQ2LTM2ZjVhZjRiODE4NSIsInN1YiI6ImRhdGFodWIiLCJleHAiOjE3NjM4ODkxMjMsImlzcyI6ImRhdGFodWItbWV0YWRhdGEtc2VydmljZSJ9.DhiGqCmdmowSS5TRLRkoYDuPNtp_cLsKZR7JlLtMDHI"
API_URL = "http://localhost:8080"
ENTITY_TYPE = "dashboard2"
ASPECT_NAME = "dashboard2Info"
DASHBOARD_ID = 1000 + random.randint(0, 8999)
URN = f"urn:li:dashboard2:(looker,looker.com/dashboards/{DASHBOARD_ID})"
ASPECT_FILE = "../../dashboard2info.json"
DATAHUB_CLI = "/home/sergio/datahub/metadata-ingestion/venv/bin/datahub"

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
        "title": "Mi Dashboard2",
        "description": "Descripcion de prueba para dashboard2"
    }
    with open(ASPECT_FILE, "w") as f:
        json.dump(aspect_data, f)

    run_datahub("put", "--urn", URN, "--aspect", ASPECT_NAME, "-d", ASPECT_FILE)

@pytest.fixture(scope="module")
def modified_aspect():
    aspect_data = {
        "title": "Dashboard2 actualizado",
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
    assert "Mi Dashboard2" in output

def test_check_urn_exists():
    output = run_datahub("exists", "--urn", URN)
    assert "true" in output.lower()

def test_get_aspect(aspect_created):
    output = run_datahub("get", "--urn", URN, "--aspect", ASPECT_NAME)
    assert "title" in output

def test_graphql_entitytype():
    graphql_query = {"query": '{ __type(name: "EntityType") { enumValues { name } } }'}
    r = requests.post(f"{API_URL}/api/graphql", headers=headers(), json=graphql_query)
    enum_values = r.json().get("data", {}).get("__type", {}).get("enumValues", [])
    assert any(ev.get("name") == "DASHBOARD2" for ev in enum_values)

def test_graphql_search_dashboard2():
    query = {
        "query": """
        query {
          search(input: {
            type: DASHBOARD2,
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

def test_graphql_search_dashboard():
    query = {
        "query": """
        query {
          search(input: {
            type: DASHBOARD,
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
    info = aspect_json.get("dashboard2Info", {})
    assert info.get("title") == "Mi Dashboard2"

def test_check_urn_still_exists():
    output = run_datahub("exists", "--urn", URN)
    assert "true" in output.lower()

def test_modify_aspect(modified_aspect):
    output = run_datahub("get", "--urn", URN, "--aspect", ASPECT_NAME)
    assert "Dashboard2 actualizado" in output

def test_verify_aspect_update():
    output = run_datahub("get", "--urn", URN, "--aspect", ASPECT_NAME)
    assert "Dashboard2 actualizado" in output

def test_search_by_title():
    query = {
        "query": f'''
        query {{
          search(input: {{
            type: DASHBOARD2,
            query: "Dashboard2 actualizado",
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
    results = r.json().get("data", {}).get("search", {}).get("searchResults", [])
    assert any(res.get("entity", {}).get("urn") == URN for res in results)

def test_query_dashboard2_by_urn():
    query = {
        "query": f'''
        query {{
          dashboard2(urn: "{URN}") {{
            urn
            type
            info {{
              name
              description
            }}
          }}
        }}
        '''
    }
    r = requests.post(f"{API_URL}/api/graphql", headers=headers(), json=query)
    data = r.json().get("data", {}).get("dashboard2", {})
    assert data.get("urn") == URN

def test_search_old_title():
    query = {
        "query": f'''
        query {{
          search(input: {{
            type: DASHBOARD2,
            query: "Mi Dashboard2",
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
    results = r.json().get("data", {}).get("search", {}).get("searchResults", [])
    assert any(res.get("entity", {}).get("urn") == URN for res in results)

def test_query_dashboard2_by_id():
    query = {
        "query": f'''
        query {{
          dashboard2(urn: "{URN}") {{
            urn
            type
            dashboardId
          }}
        }}
        '''
    }
    r = requests.post(f"{API_URL}/api/graphql", headers=headers(), json=query)
    data = r.json().get("data", {}).get("dashboard2", {})
    assert data.get("dashboardId") == f"looker.com/dashboards/{DASHBOARD_ID}"
