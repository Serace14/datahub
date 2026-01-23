import pytest
import time
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.ingestion.graph.client import DatahubClientConfig, DataHubGraph
from datahub.metadata.schema_classes import StatusClass
from datahub.metadata.com.linkedin.pegasus2avro.dataset import UpstreamLineage, UpstreamClass, DatasetLineageTypeClass as DatasetLineageType


@pytest.fixture(scope="module")
def datahub_emitter():
    return DatahubRestEmitter("http://localhost:8080")

@pytest.fixture(scope="module")
def datahub_graph():
    return DataHubGraph(DatahubClientConfig(server="http://localhost:8080"))

def make_platform_resource_urn(resource_id: str) -> str:
    return f"urn:li:platformResource:{resource_id}"

def make_catalog_record_urn(platform: str, name: str, origin: str = "PROD") -> str:
    platform_urn = f"urn:li:dataPlatform:{platform}"
    return f"urn:li:catalogRecord:({platform_urn},{name},{origin})"

def test_catalog_record_depends_on_platform_resource(datahub_emitter, datahub_graph):
    platform_resource_urn = make_platform_resource_urn("platform_res_1")
    catalog_record_urn = make_catalog_record_urn("geoserver", "catalog_rec_1")

    # Emitir PlatformResource
    platform_resource_status = MetadataChangeProposalWrapper(
        entityUrn=platform_resource_urn,
        aspect=StatusClass(removed=False),
    )
    datahub_emitter.emit_mcp(platform_resource_status)

    # Conectar con lineage
    upstream = UpstreamClass(dataset=platform_resource_urn, type=DatasetLineageType.VIEW)
    lineage = UpstreamLineage(upstreams=[upstream])

    catalog_record_lineage = MetadataChangeProposalWrapper(
        entityUrn=catalog_record_urn,
        aspect=lineage,
    )
    datahub_emitter.emit_mcp(catalog_record_lineage)

    time.sleep(2)

    aspect = datahub_graph.get_aspect(
        entity_urn=catalog_record_urn,
        aspect_type=UpstreamLineage,
    )
    assert aspect is not None, "No se encontró el aspecto UpstreamLineage"
    print(f"\n✅ Lineage registrado: {platform_resource_urn} -> {catalog_record_urn}")
