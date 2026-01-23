import os
import json
import random
import pytest
import requests

TOKEN = os.getenv("DATAHUB_TOKEN", "eyJhbGciOiJIUzI1NiJ9...")
API_URL = "http://localhost:8080"

def headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

def graphql_query(query: str):
    payload = {"query": query}
    resp = requests.post(f"{API_URL}/graphql", headers=headers(), json=payload)
    return resp

# --- Fixtures ---
@pytest.fixture(scope="module")
def catalog_record_urn():
    catalog_id = 2000 + random.randint(0, 8999)
    return f"urn:li:catalogRecord:(urn:li:dataPlatform:geoserver,{catalog_id},PROD)"

@pytest.fixture(scope="module")
def platform_resource_urn():
    resource_id = random.randint(1000, 9999)
    return f"urn:li:platformResource:looker-resource-{resource_id}"

# --- Tests ---
def test_ingest_catalog_record(catalog_record_urn):
    aspect_data = {
        "name": "My Catalog Record",
        "description": "Catalog creado desde pytest"
    }
    payload = {
        "proposal": {
            "entityType": "catalogRecord",
            "entityUrn": catalog_record_urn,
            "changeType": "UPSERT",
            "aspectName": "datasetProperties",
            "aspect": {
                "value": json.dumps(aspect_data),
                "contentType": "application/json"
            }
        }
    }
    resp = requests.post(f"{API_URL}/aspects?action=ingestProposal", headers=headers(), json=payload)
    print("\n[DEBUG] ingest_catalog_record response:", resp.status_code, resp.text)
    assert resp.status_code == 200

def test_ingest_platform_resource(platform_resource_urn):
    aspect_data = {
        "resourceType": "table",
        "primaryKey": "id123",
        "secondaryKeys": ["sk1", "sk2"]
    }
    payload = {
        "proposal": {
            "entityType": "platformResource",
            "entityUrn": platform_resource_urn,
            "changeType": "UPSERT",
            "aspectName": "platformResourceInfo",
            "aspect": {
                "value": json.dumps(aspect_data),
                "contentType": "application/json"
            }
        }
    }
    resp = requests.post(f"{API_URL}/aspects?action=ingestProposal", headers=headers(), json=payload)
    print("\n[DEBUG] ingest_platform_resource response:", resp.status_code, resp.text)
    assert resp.status_code == 200

def test_create_relationship(catalog_record_urn, platform_resource_urn):
    # Creamos relación nativa DependsOn (catalog depende del resource)
    query = f"""
    mutation {{
      createRelationship(input: {{
        type: DependsOn,
        source: "{catalog_record_urn}",
        destination: "{platform_resource_urn}"
      }})
    }}
    """
    resp = graphql_query(query)
    print("\n[DEBUG] create_relationship response:", resp.status_code, resp.text)
    assert resp.status_code == 200
    data = resp.json()
    assert "errors" not in data, data.get("errors")
    assert data.get("data", {}).get("createRelationship") is True

def test_check_relationship(catalog_record_urn, platform_resource_urn):
    # Consultamos relaciones salientes de tipo DependsOn
    query = f"""
    query {{
      entity(urn: "{catalog_record_urn}") {{
        relationships(input: {{
          types: [DependsOn],
          direction: OUTGOING
        }}) {{
          relationships {{
            entity {{ urn }}
            type
          }}
        }}
      }}
    }}
    """
    resp = graphql_query(query)
    assert resp.status_code == 200
    data = resp.json()
    relationships = data["data"]["entity"]["relationships"]["relationships"]
    related_urns = [rel["entity"]["urn"] for rel in relationships]
    print("\n[DEBUG] check_relationship related_urns:", related_urns)
    assert platform_resource_urn in related_urns
