import os
import random
import pytest
import pprint
import requests
import time
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import (
    DistributionInfoClass,
    DatasetPropertiesClass,
    ChangeAuditStampsClass,
    AuditStampClass,
)

GRAPHQL_URL = "http://localhost:8080/api/graphql"

# --- Configuración ---
TOKEN = os.getenv("DATAHUB_TOKEN", "")
ENTITY_TYPE = "distribution"
ENTITY_ID = f"dist-{random.randint(1000, 9999)}"
URN = f"urn:li:distribution:{ENTITY_ID}"

# URNs de los datasets
ACCESS_URL_URN = "urn:li:dataset:(urn:li:dataPlatform:geoserver,00b386be-b5d1-43e4-8c80-347fff7cbb16,PROD)"
ACCESS_SERVICE_URN = "urn:li:dataset:(urn:li:dataPlatform:geoserver,05f9482-c1d7-4473-8078-1262b49ecb3b,PROD)"


def run_graphql_query(query: str, variables=None):
    resp = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    )
    resp.raise_for_status()
    return resp.json()


@pytest.fixture(scope="module")
def emit_distribution_with_datasets():
    emitter = DatahubRestEmitter(gms_server="http://localhost:8080", token=TOKEN)
    now = int(time.time() * 1000)
    audit = ChangeAuditStampsClass(created=AuditStampClass(time=now, actor="urn:li:corpuser:datahub"))

    # Emitir datasets
    for dataset_urn, name in [(ACCESS_URL_URN, "Access URL Dataset"),
                              (ACCESS_SERVICE_URN, "Access Service Dataset")]:
        emitter.emit(MetadataChangeProposalWrapper(
            entityUrn=dataset_urn,
            aspect=DatasetPropertiesClass(name=name)
        ))

    # Emitir distribución con relaciones incluidas
    info = DistributionInfoClass(
        title="Customer Data Export",
        description="Distribución periódica de datos de clientes hacia servicio externo.",
        accessURL=ACCESS_URL_URN,
        accessService=ACCESS_SERVICE_URN,
        lastModified=audit,
    )
    emitter.emit(MetadataChangeProposalWrapper(entityUrn=URN, aspect=info))

    emitter.close()



# --- Tests básicos ---
def test_entity_registered():
    payload = {"input": "*", "entity": ENTITY_TYPE, "start": 0, "count": 10}
    r = requests.post(f"http://localhost:8080/entities?action=search",
                      headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
                      json=payload)
    assert "value" in r.json()

def test_query_distribution_by_urn(emit_distribution_with_datasets):
    query = {
        "query": f'''
        query {{
          distribution(urn: "{URN}") {{
            urn
            type
            id
            info {{
              name
              description
            }}
          }}
        }}
        '''
    }
    r = run_graphql_query(query["query"])
    data = r.get("data", {}).get("distribution", {})
    assert data.get("urn") == URN
    assert data.get("info", {}).get("name") == "Customer Data Export"


@pytest.mark.integration
def test_print_distribution_full_content(emit_distribution_with_datasets):
    """Imprime todo el contenido de la distribución registrada en DataHub."""
    query = f"""
    query {{
      distribution(urn: "{URN}") {{
        urn
        type
        id
        info {{
          name
          description
          accessURL {{ urn }}
          accessService {{ urn }}
        }}
      }}
    }}
    """
    data = run_graphql_query(query)
    distribution = data.get("data", {}).get("distribution")
    assert distribution is not None, f"No se encontró la distribución {URN}"

    print("\n=== Contenido completo de la distribución ===")
    pprint.pprint(distribution)

@pytest.mark.integration
def test_print_distribution_access_urns(emit_distribution_with_datasets):
    """Extrae e imprime los URNs de accessURL y accessService desde la distribución."""
    query = f"""
    query {{
      distribution(urn: "{URN}") {{
        urn
        info {{
          accessURL {{ urn }}
          accessService {{ urn }}
        }}
      }}
    }}
    """
    data = run_graphql_query(query)
    distribution = data.get("data", {}).get("distribution")
    assert distribution is not None, f"No se encontró la distribución {URN}"

    access_url_urn = distribution.get("info", {}).get("accessURL", {}).get("urn")
    access_service_urn = distribution.get("info", {}).get("accessService", {}).get("urn")

    print("\n=== URNs asociados a la distribución ===")
    pprint.pprint([access_url_urn, access_service_urn])

    assert access_url_urn == ACCESS_URL_URN
    assert access_service_urn == ACCESS_SERVICE_URN


@pytest.mark.integration
def test_distribution_relationships(emit_distribution_with_datasets):
    """Comprueba las relaciones de datasets asociadas a la distribución."""
    query = f"""
    query {{
      distribution(urn: "{URN}") {{
        urn
        relationships(input: {{start:0, count:10}}) {{
          total
          entities {{
            entity {{
              urn
              type
            }}
            type
          }}
        }}
      }}
    }}
    """
    data = run_graphql_query(query)
    distribution = data.get("data", {}).get("distribution")
    assert distribution is not None, f"No se encontró la distribución {URN}"

    relationships = distribution.get("relationships", {})
    total = relationships.get("total", 0)
    entities = relationships.get("entities", [])

    print("\n=== Relationships de la distribución ===")
    pprint.pprint(entities)

    # Verificamos que ambos datasets están presentes en las relaciones
    related_urns = [e["entity"]["urn"] for e in entities if e.get("entity")]
    assert ACCESS_URL_URN in related_urns, "accessURL no está en las relaciones"
    assert ACCESS_SERVICE_URN in related_urns, "accessService no está en las relaciones"
    assert total >= 2, "No se registraron todas las relaciones esperadas"