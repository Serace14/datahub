import os
import json
import requests

TOKEN = os.getenv("DATAHUB_TOKEN", "eyJhbGciOiJIUzI1NiJ9...")
API_URL = "http://localhost:8080"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def register_related_resources_aspect():
    """Registra el aspecto custom 'relatedResources' para catalogRecord"""
    aspect_definition = {
        "name": "relatedResources",
        "entity": "catalogRecord",
        "jsonSchema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "relatedResources",
            "type": "object",
            "properties": {
                "resources": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["resources"]
        }
    }

    payload = {
        "proposal": {
            "entityType": "aspect",
            "entityUrn": f"urn:li:aspect:(catalogRecord,relatedResources,1.0)",
            "changeType": "UPSERT",
            "aspectName": "aspectProperties",
            "aspect": {
                "value": json.dumps(aspect_definition),
                "contentType": "application/json"
            }
        }
    }

    resp = requests.post(f"{API_URL}/aspects?action=ingestProposal", headers=HEADERS, json=payload)
    print("[DEBUG] register_related_resources_aspect response:", resp.status_code, resp.text)
    return resp

if __name__ == "__main__":
    register_related_resources_aspect()
