import pytest
import pprint
import requests
from datahub.emitter.mce_builder import make_dataset_urn
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import DatasetPropertiesClass, ApplicationsClass

GRAPHQL_URL = "http://localhost:8080/api/graphql"

def run_graphql_query(query: str, variables=None):
    resp = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        headers={"Content-Type": "application/json"},
    )
    resp.raise_for_status()
    return resp.json()


@pytest.mark.integration
def test_ingest_dataset_with_application():
    """Ingesta un dataset y lo asocia a una aplicación."""
    emitter = DatahubRestEmitter(gms_server="http://localhost:8080", token="")

    dataset_urn = make_dataset_urn("hive", "test_db.test_table", "PROD")

    # 1. Ingesta el dataset
    dataset_properties = DatasetPropertiesClass(
        description="Tabla de prueba para asociar aplicación"
    )
    emitter.emit(MetadataChangeProposalWrapper(
        entityUrn=dataset_urn,
        aspect=dataset_properties,
    ))

    # 2. Asocia la aplicación existente
    application_urn = "urn:li:application:mi_aplicacion_existente"  # Cambiar por el URN real
    applications_aspect = ApplicationsClass(applications=[application_urn])
    emitter.emit(MetadataChangeProposalWrapper(
        entityUrn=dataset_urn,
        aspect=applications_aspect,
    ))

    emitter.close()