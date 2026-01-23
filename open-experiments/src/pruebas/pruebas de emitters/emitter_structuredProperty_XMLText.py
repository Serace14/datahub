#Este emitter fue hecho para probar la creación de una structured property XMLText y asignarla a un PlatformResource temporal.
#Tras varias pruebas, se determinó que no sirve ya que no se puede crear StructuredProperties en PlatformResource porque la
#estrcutura de su urn no s ecorresponde con la de verificación que s ehace al asociar un StructuredProperty.

import pytest
import time
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.ingestion.graph.config import DatahubClientConfig
from datahub.ingestion.graph.client import DataHubGraph
from datahub.metadata.schema_classes import (
    StructuredPropertyDefinitionClass,
    StructuredPropertiesClass,
    PlatformResourceInfoClass
)

@pytest.fixture(scope="module")
def rest_emitter():
    return DatahubRestEmitter(gms_server="http://localhost:8080")

@pytest.fixture(scope="module")
def graph_client():
    config = DatahubClientConfig(server="http://localhost:8080")
    return DataHubGraph(config)

def test_structured_property_on_temp_platform_resource(rest_emitter, graph_client):
    # 1️⃣ Definir la Structured Property global
    property_urn = "urn:li:structuredProperty:(io.acryl.platformResource.XMLText)"
    property_definition = StructuredPropertyDefinitionClass(
        qualifiedName="io.acryl.platformResource.XMLText",
        displayName="XMLText",
        valueType="urn:li:dataType:datahub.string",
        cardinality="SINGLE",
        entityTypes=["urn:li:entityType:datahub.platformResource"],
        description="Campo de texto XML para PlatformResource",
        immutable=False,
    )
    rest_emitter.emit(MetadataChangeProposalWrapper(entityUrn=property_urn, aspect=property_definition))

    from datahub.metadata.schema_classes import PlatformResourceInfoClass

    # 2️⃣ Crear un PlatformResource temporal (mínimo)
    temp_urn = "urn:li:platformResource:(test_platform,temp_resource,PROD)"
    #temp_urn = "urn:li:platformResource:temp_resource"
    platform_resource_info = PlatformResourceInfoClass(
        resourceType="TEST",
        primaryKey="temp_resource",
        secondaryKeys=[],
        value=None
    )
    rest_emitter.emit(MetadataChangeProposalWrapper(entityUrn=temp_urn, aspect=platform_resource_info))

    # 3️⃣ Asignar un valor a la Structured Property
    structured_properties = StructuredPropertiesClass(
        properties=[
            {
                "propertyUrn": property_urn,
                "values": ["<xml>valor de prueba</xml>"]
            }
        ]
    )
    rest_emitter.emit(MetadataChangeProposalWrapper(entityUrn=temp_urn, aspect=structured_properties))

    # 4️⃣ Esperar un momento para que el servidor procese los MCP
    #time.sleep(1)

    # 5️⃣ Recuperar y verificar el aspecto
    #aspect = graph_client.get_aspect(temp_urn, StructuredPropertiesClass)
    #print("Aspect recuperado:", aspect)
    #assert aspect is not None, "El aspecto structuredProperties no se recuperó correctamente"
    #assert any(
    #    p["propertyUrn"].endswith("XMLText") and "<xml>valor de prueba</xml>" in p["values"]
    #    for p in aspect.properties
    #), "La propiedad XMLText no contiene el valor esperado"
