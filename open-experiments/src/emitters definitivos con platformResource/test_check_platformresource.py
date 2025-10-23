import pytest
from datahub.ingestion.graph.client import DataHubGraph
from datahub.ingestion.graph.config import DatahubClientConfig
from datahub.metadata.schema_classes import PlatformResourceInfoClass

GMS_SERVER = "http://localhost:8080"

@pytest.fixture(scope="module")
def graph_client():
    config = DatahubClientConfig(server=GMS_SERVER)
    return DataHubGraph(config)

def test_check_platform_resource(graph_client):
    # URN de la entidad emitida
    urn = "urn:li:platformResource:geonetwork-7eea5c42-212f-4099-b9df-1e3703fbc616"

    # Recuperar PlatformResourceInfo
    try:
        aspect_info = graph_client.get_aspect(urn, PlatformResourceInfoClass)
        print("\n=== PlatformResourceInfo ===")
        print(f"resourceType: {aspect_info.resourceType}")
        print(f"primaryKey: {aspect_info.primaryKey}")
        print(f"secondaryKeys: {aspect_info.secondaryKeys}")

        # Mostrar xmlText truncado para evitar saturar salida
        if hasattr(aspect_info, "xmlText") and aspect_info.xmlText:
            xml_preview = aspect_info.xmlText[:200].replace("\n", " ")
            print(f"xmlText (preview): {xml_preview}...")
        else:
            print("⚠️ xmlText vacío o no encontrado")

        # Validaciones básicas
        assert aspect_info.resourceType == "metadata"
        assert aspect_info.primaryKey is not None
        assert aspect_info.xmlText is not None and len(aspect_info.xmlText) > 0

    except Exception as e:
        pytest.fail(f"❌ No se pudo recuperar PlatformResourceInfo: {e}")
