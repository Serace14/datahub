import os
import pytest
import requests

# Configuración: ajusta estos valores según tu entorno
DATAHUB_GRAPHQL_URL = os.getenv("DATAHUB_GRAPHQL_URL", "http://localhost:8080/api/graphql")
DATAHUB_TOKEN = os.getenv("DATAHUB_TOKEN", "<tu_token_aqui>")

HEADERS = {
    "Authorization": f"Bearer {DATAHUB_TOKEN}",
    "Content-Type": "application/json"
}

def run_graphql_query(query, variables=None):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    response = requests.post(DATAHUB_GRAPHQL_URL, json=payload, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def test_search_datasets():
    query = """
    query {
      search(input: { type: DATASET, query: "*", start: 0, count: 5 }) {
        searchResults {
          entity {
            ... on Dataset {
              name
              urn
            }
          }
        }
      }
    }
    """
    data = run_graphql_query(query)
    assert "data" in data
    results = data["data"]["search"]["searchResults"]
    assert isinstance(results, list)
    assert len(results) > 0
    assert "urn" in results[0]["entity"]

def test_dataset_description():
    dataset_urn = "urn:li:dataset:(urn:li:dataPlatform:hive,fct_users_deleted,PROD)"
    query = """
    query($urn: String!) {
      dataset(urn: $urn) {
        properties {
          description
        }
      }
    }
    """
    data = run_graphql_query(query, {"urn": dataset_urn})
    assert "data" in data
    assert data["data"]["dataset"] is not None
    assert "properties" in data["data"]["dataset"]

def test_dataset_schema_fields():
    dataset_urn = "urn:li:dataset:(urn:li:dataPlatform:hive,fct_users_created,PROD)"
    query = """
    query($urn: String!) {
      dataset(urn: $urn) {
        schemaMetadata {
          fields {
            fieldPath
            type
            nativeDataType
            description
          }
        }
      }
    }
    """
    data = run_graphql_query(query, {"urn": dataset_urn})
    print("GraphQL response:", data)
    assert "data" in data
    assert data["data"]["dataset"] is not None
    fields = data["data"]["dataset"]["schemaMetadata"]["fields"]
    assert isinstance(fields, list)
    assert len(fields) > 0
    assert "fieldPath" in fields[0]


def test_search_datasets_by_platform():
    query = """
    query {
      search(input: {
        type: DATASET,
        query: "*",
        start: 0,
        count: 5,
        orFilters: [
          {
            and: [
              { field: "platform", values: ["hive"], condition: CONTAIN }
            ]
          }
        ]
      }) {
        searchResults {
          entity {
            ... on Dataset {
              name
              urn
            }
          }
        }
      }
    }
    """
    data = run_graphql_query(query)
    assert "data" in data
    results = data["data"]["search"]["searchResults"]
    assert isinstance(results, list)
    assert len(results) > 0
    assert "urn" in results[0]["entity"]

def test_dataset_column_descriptions():
    dataset_urn = "urn:li:dataset:(urn:li:dataPlatform:hive,fct_users_created,PROD)"
    query = """
    query($urn: String!) {
      dataset(urn: $urn) {
        schemaMetadata {
          fields {
            fieldPath
            description
          }
        }
      }
    }
    """
    data = run_graphql_query(query, {"urn": dataset_urn})
    assert "data" in data
    assert data["data"]["dataset"] is not None
    fields = data["data"]["dataset"]["schemaMetadata"]["fields"]
    assert isinstance(fields, list)
    assert "fieldPath" in fields[0]
    assert "description" in fields[0]
