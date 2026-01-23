import pytest
from datahub.emitter.mce_builder import make_dataset_urn, make_schema_field_urn
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.com.linkedin.pegasus2avro.dataset import (
    FineGrainedLineage,
    FineGrainedLineageDownstreamType,
    FineGrainedLineageUpstreamType,
    Upstream,
    UpstreamLineage, DatasetLineageType,
)
from datahub.ingestion.graph.client import DatahubClientConfig, DataHubGraph

@pytest.fixture(scope="module")
def datahub_emitter():
    # Cambia la URL si tu GMS no está en localhost
    return DatahubRestEmitter("http://localhost:8080")

@pytest.fixture(scope="module")
def datahub_graph():
    return DataHubGraph(DatahubClientConfig(server="http://localhost:8080"))

def test_fine_grained_lineage_ingestion_and_verification(datahub_emitter, datahub_graph):
    # Definición de URNs
    source_table = "source_table"
    target_table = "target_table"
    source_column = "source_column"
    target_column = "target_column"

    source_dataset_urn = make_dataset_urn("postgres", source_table)
    target_dataset_urn = make_dataset_urn("postgres", target_table)
    source_field_urn = make_schema_field_urn(source_dataset_urn, source_column)
    target_field_urn = make_schema_field_urn(target_dataset_urn, target_column)

    # Definir fine-grained lineage
    fine_grained_lineages = [
        FineGrainedLineage(
            upstreamType=FineGrainedLineageUpstreamType.FIELD_SET,
            upstreams=[source_field_urn],
            downstreamType=FineGrainedLineageDownstreamType.FIELD,
            downstreams=[target_field_urn],
        ),
    ]

    upstream = Upstream(
        dataset=source_dataset_urn,
        type=DatasetLineageType.TRANSFORMED)
    field_lineages = UpstreamLineage(
        upstreams=[upstream],
        fineGrainedLineages=fine_grained_lineages,
    )

    lineage_mcp = MetadataChangeProposalWrapper(
        entityUrn=target_dataset_urn,
        aspect=field_lineages,
    )

    # Emitir el lineage
    datahub_emitter.emit_mcp(lineage_mcp)

    # Comprobar que el lineage se ha registrado correctamente
    # Espera breve para que el backend procese la ingesta
    import time
    time.sleep(2)

    # Consulta el aspecto upstreamLineage del dataset destino
    aspect = datahub_graph.get_aspect(
        entity_urn=target_dataset_urn,
        aspect_type=UpstreamLineage,
    )

    assert aspect is not None, "No se encontró el aspecto upstreamLineage"
    assert hasattr(aspect, "fineGrainedLineages")
    assert len(aspect.fineGrainedLineages) > 0

    # Verifica que la relación específica está presente
    found = any(
        fg.upstreams == [source_field_urn] and fg.downstreams == [target_field_urn]
        for fg in aspect.fineGrainedLineages
    )
    assert found, "No se encontró el fine-grained lineage esperado"

