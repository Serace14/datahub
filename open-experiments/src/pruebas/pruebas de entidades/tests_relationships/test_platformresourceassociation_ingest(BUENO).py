import pytest
import pprint
import requests
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
    PlatformResourceInfoClass,
    PlatformResourcesClass,
)

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
def test_ingest_catalog_record_and_platform_resource():
    """Solo se encarga de la ingesta y asociación, sin verificaciones."""
    emitter = DatahubRestEmitter(gms_server="http://localhost:8080", token="")

    catalog_urn = "urn:li:catalogRecord:(urn:li:dataPlatform:test_platform,record_1,PROD)"
    platform_resource_urn = "urn:li:platformResource:test_platform_resource"

    # 1. Ingesta CatalogRecord con datasetProperties
    catalog_properties = DatasetPropertiesClass(
        name="Test Catalog Record",
        description="CatalogRecord de prueba para asociar PlatformResource",
    )
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=catalog_urn,
            aspect=catalog_properties,
        )
    )

    # 2. Ingesta PlatformResource
    platform_resource_info = PlatformResourceInfoClass(
        resourceType="test_type",
        primaryKey="test_pk",
        secondaryKeys=["alt_pk1", "alt_pk2"],
        value=None,
    )
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=platform_resource_urn,
            aspect=platform_resource_info,
        )
    )

    # 3. Asocia PlatformResource al CatalogRecord
    association_aspect = PlatformResourcesClass(resources=[platform_resource_urn])
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=catalog_urn,
            aspect=association_aspect,
        )
    )
    emitter.close()


@pytest.mark.integration
def test_verify_catalog_record_properties():
    """Verifica vía GraphQL que el CatalogRecord existe y tiene la descripción esperada."""
    catalog_urn = "urn:li:catalogRecord:(urn:li:dataPlatform:test_platform,record_1,PROD)"

    # Consultar el CatalogRecord
    catalog_query = """
    query getCatalog($urn: String!) {
      catalogRecord(urn: $urn) {
        urn
        properties {
          description
        }
      }
    }
    """
    catalog_data = run_graphql_query(catalog_query, {"urn": catalog_urn})

    print("\n=== CatalogRecord GraphQL response ===")
    pprint.pprint(catalog_data)

    # Validaciones básicas
    assert "data" in catalog_data, "Respuesta inválida de GraphQL"
    catalog = catalog_data["data"].get("catalogRecord")
    assert catalog is not None, f"No se encontró el CatalogRecord {catalog_urn}"

    # Verificar que el CatalogRecord tiene la descripción esperada
    description = catalog.get("properties", {}).get("description")
    assert description == "CatalogRecord de prueba para asociar PlatformResource"

@pytest.mark.integration
def test_verify_catalog_and_resource_relationship():
    """Verifica vía GraphQL que el CatalogRecord está asociado al PlatformResource."""
    catalog_urn = "urn:li:catalogRecord:(urn:li:dataPlatform:test_platform,record_1,PROD)"
    platform_resource_urn = "urn:li:platformResource:test_platform_resource"

    # ==== Consultar catalogRecord con relaciones ====
    rel_query = """
    query getCatalogWithRelationships($urn: String!) {
      catalogRecord(urn: $urn) {
        urn
        properties {
          description
        }
        relationships(input: {types: ["AssociatedWith"], direction: OUTGOING}) {
          relationships {
            entity {
              urn
            }
            type
          }
        }
      }
    }
    """
    rel_data = run_graphql_query(rel_query, {"urn": catalog_urn})

    print("\n=== CatalogRecord GraphQL response (with relationships) ===")
    pprint.pprint(rel_data)

    catalog = rel_data.get("data", {}).get("catalogRecord")
    assert catalog is not None, f"No se encontró el CatalogRecord {catalog_urn}"

    rels = catalog.get("relationships", {}).get("relationships", [])
    related_urns = [r["entity"]["urn"] for r in rels]
    assert platform_resource_urn in related_urns, (
        f"No se encontró relación 'AssociatedWith' entre {catalog_urn} y {platform_resource_urn}"
    )
