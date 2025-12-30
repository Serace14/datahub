from datahub.metadata._internal_schema_classes import ChangeAuditStampsClass
from datahub.specific.dataset import DatasetPatchBuilder
from lxml import etree
import time
import random
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import (
    StructuredPropertyValueAssignmentClass,
    DistributionInfoClass,
    AuditStampClass,
)

STRUCTURED_PROP_DISTRIBUTION = "urn:li:structuredProperty:distribution"


def extract_distributions(tree):
    """Extrae las Distribution ISO 19139 para convertirlas a entidades Distribution."""
    ns = {
        "gmd": "http://www.isotc211.org/2005/gmd",
        "gco": "http://www.isotc211.org/2005/gco",
    }

    links = tree.xpath(
        "//gmd:distributionInfo//gmd:CI_OnlineResource",
        namespaces=ns
    )

    dists = []
    for link in links:
        url = link.xpath("gmd:linkage/gmd:URL/text()", namespaces=ns)
        protocol = link.xpath("gmd:protocol/gco:CharacterString/text()", namespaces=ns)
        name = link.xpath("gmd:name/gco:CharacterString/text()", namespaces=ns)

        dists.append({
            "url": url[0] if url else None,
            "protocol": protocol[0] if protocol else None,
            "name": name[0] if name else None,
        })

    return dists


def create_distribution_and_attach(emitter, dataset_urn: str, tree):
    """
    Busca Distribution en XML ISO, crea entidad Distribution y la asocia
    al Dataset mediante la structuredProperty 'distribution'.
    """

    distributions = extract_distributions(tree)   # <-- ya la definimos antes

    if not distributions:
        print(f"ℹ No hay Distribution en {dataset_urn}")
        return

    print(f"📦 Encontradas {len(distributions)} Distribution en el XML")

    for dist in distributions:

        # -----------------------------
        # 1. Construir URN único
        # -----------------------------
        ts = int(time.time() * 1000)
        dist_id = f"dist-{ts}"
        distribution_urn = f"urn:li:distribution:{dist_id}"

        # -----------------------------
        # 2. Construir aspecto DistributionInfoClass
        # -----------------------------
        now_ts = int(time.time() * 1000)

        aspect = DistributionInfoClass(
            title=dist["name"] or "Unnamed Distribution",
            description=(
                f"URL: {dist['url'] or 'N/A'} | "
                f"Protocol: {dist['protocol'] or 'N/A'}"
            ),
            lastModified=ChangeAuditStampsClass(
                created=AuditStampClass(
                    time=now_ts,
                    actor="urn:li:corpuser:ingestion"
                )
            )
        )

        emitter.emit(
            MetadataChangeProposalWrapper(
                entityUrn=distribution_urn,
                aspect=aspect,
                aspectName="distributionInfo"   # EXACTO según tu PDL
            )
        )

        print(f"✅ Distribution creada: {distribution_urn}")

        # -----------------------------
        # 3. Asociarla al Dataset vía structured property
        # -----------------------------
        patch_builder = DatasetPatchBuilder(dataset_urn)
        patch_builder.set_structured_property(
            "urn:li:structuredProperty:distribution",  # tu StructuredProperty para la asociación
            distribution_urn
        )

        for patch_mcp in patch_builder.build():
            emitter.emit(patch_mcp)


        print(f"🔗 Dataset {dataset_urn} → Distribution {distribution_urn}")