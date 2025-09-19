import os
import json
import random
import pytest
import requests

# --- Configuración ---
TOKEN = os.getenv("DATAHUB_TOKEN", "eyJhbGciOiJIUzI1NiJ9...")  # cambia si usas otro
API_URL = "http://localhost:8080"

# --- Helpers ---
def headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

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
                "value": json.dumps(aspect_data),  # ✅ serializar dict a JSON string
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
                "value": json.dumps(aspect_data),  # ✅ también serializado
                "contentType": "application/json"
            }
        }
    }
    resp = requests.post(f"{API_URL}/aspects?action=ingestProposal", headers=headers(), json=payload)
    print("\n[DEBUG] ingest_platform_resource response:", resp.status_code, resp.text)
    assert resp.status_code == 200

def test_create_relationship(catalog_record_urn, platform_resource_urn):
    aspect_data = {
        "relationships": [
            {
                "entity": platform_resource_urn,
                "type": "RelatedTo"
            }
        ]
    }
    payload = {
        "proposal": {
            "entityType": "catalogRecord",
            "entityUrn": catalog_record_urn,
            "changeType": "UPSERT",
            "aspectName": "relationships",
            "aspect": {
                "value": json.dumps(aspect_data),
                "contentType": "application/json"
            }
        }
    }
    resp = requests.post(f"{API_URL}/aspects?action=ingestProposal", headers=headers(), json=payload)
    print("\n[DEBUG] create_relationship response:", resp.status_code, resp.text)
    print("[DEBUG] response body:", resp.text)
    assert resp.status_code == 200



def test_check_relationship(catalog_record_urn, platform_resource_urn):
    params = {
        "direction": "OUTGOING",
        "urn": catalog_record_urn,
        "types": "RelatedTo"
    }
    resp = requests.get(f"{API_URL}/relationships", headers=headers(), params=params)
    print("\n[DEBUG] check_relationship response:", resp.status_code, resp.text)
    assert resp.status_code == 200
    data = resp.json()
    related_urns = [rel["entity"]["urn"] for rel in data.get("relationships", [])]
    assert platform_resource_urn in related_urns



