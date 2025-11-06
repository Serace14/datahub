# =========================
# EMITTER FUNCIONAL CORREGIDO
# =========================

from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.ingestion.graph.client import DataHubGraph
from datahub.ingestion.graph.config import DatahubClientConfig
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
    OwnershipClass,
    OwnerClass,
    OwnershipTypeClass,
    TagPropertiesClass,
    TagAssociationClass,
    GlobalTagsClass,
    CorpGroupInfoClass,
    PlatformResourceInfoClass,
)
from datahub.specific.dataset import DatasetPatchBuilder
from lxml import etree
import datahub.emitter.mce_builder as builder
import re
import unicodedata
import sys

# === CONFIGURACIÓN ===
GMS_SERVER = "http://localhost:8080"
TOKEN = "eyJhbGciOiJIUzI1NiJ9..."  # reemplaza con tu token válido

emitter = DatahubRestEmitter(gms_server=GMS_SERVER, token=TOKEN)
emitter.test_connection()
graph = DataHubGraph(DatahubClientConfig(server=GMS_SERVER))

# === Funciones auxiliares ===
def normalize_for_urn(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8")
    s = s.replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9_-]", "", s)
    return s

def get_text(tree, xpaths, ns):
    for xp in xpaths:
        try:
            elements = tree.xpath(xp, namespaces=ns)
        except Exception as e:
            continue
        if not elements:
            continue
        el = elements[0]
        if isinstance(el, str):
            if el.strip():
                return el.strip()
            else:
                continue
        if hasattr(el, "text") and el.text and el.text.strip():
            return el.text.strip()
        for attr in ("codeListValue", "{http://www.w3.org/1999/xlink}href", "href"):
            val = el.get(attr) if hasattr(el, "get") else None
            if val:
                return val.strip()
    return None

# === Namespaces ===
ns = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dct": "http://purl.org/dc/terms/",
    "gmx": "http://www.isotc211.org/2005/gmx",
    "xlink": "http://www.w3.org/1999/xlink",
    "ows": "http://www.opengis.net/ows",
}

# === CatalogRecords a procesar ===
catalog_record_urns = [
    "urn:li:catalogRecord:(urn:li:dataPlatform:geoserver,7eea5c42-212f-4099-b9df-1e3703fbc616,PROD)"
]

for catalog_record_urn in catalog_record_urns:
    print(f"🔍 Procesando CatalogRecord {catalog_record_urn}...")

    # Obtener PlatformResource asociado
    query = """
    query getCatalogWithRelationships($urn: String!) {
      catalogRecord(urn: $urn) {
        relationships(input: {types: ["AssociatedWith"], direction: OUTGOING}) {
          relationships {
            entity { urn }
            type
          }
        }
      }
    }
    """
    res = graph.execute_graphql(query, {"urn": catalog_record_urn})
    relationships = (
        res.get("catalogRecord", {}).get("relationships", {}).get("relationships", [])
    )
    if not relationships:
        print(f"⚠ No se encontró PlatformResource asociado a {catalog_record_urn}")
        continue

    platform_urn = relationships[0]["entity"]["urn"]
    print(f"✅ CatalogRecord asociado a PlatformResource {platform_urn}")

    # Obtener xmlText
    aspect_info: PlatformResourceInfoClass = graph.get_aspect(
        platform_urn, PlatformResourceInfoClass
    )
    if not aspect_info or not getattr(aspect_info, "xmlText", None):
        print(f"⚠ No se pudo recuperar xmlText de {platform_urn}")
        continue

    xml_text = aspect_info.xmlText
    if isinstance(xml_text, str):
        xml_text = xml_text.encode("utf-8")
    try:
        tree = etree.fromstring(xml_text)
    except Exception as e:
        print(f"❌ Error parseando XML: {e}", file=sys.stderr)
        continue

    # === Extraer campos ===
    title = get_text(tree, [
        ".//gmd:identificationInfo//gmd:citation//gmd:title/gco:CharacterString",
        ".//dc:title",
        ".//gmd:title/gco:CharacterString",
    ], ns)

    description = get_text(tree, [
        ".//gmd:identificationInfo//gmd:abstract/gco:CharacterString",
        ".//dc:description",
        ".//dct:abstract",
        ".//gmd:abstract/gco:CharacterString",
    ], ns)

    language = get_text(tree, [
        "//gmd:language/gmd:LanguageCode/@codeListValue",
        "//dc:language",
        ".//gmd:language/gmd:LanguageCode/text()",
    ], ns)

    # issued
    issued_nodes = tree.xpath(
        "//gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='creation']/gmd:date/*",
        namespaces=ns
    )
    issued = issued_nodes[0].text.strip() if issued_nodes and issued_nodes[0].text else None

    # modified
    modified_nodes = tree.xpath("//gmd:dateStamp//text()", namespaces=ns)
    modified = [m.strip() for m in modified_nodes if m.strip()]

    # linkxmlmetadato
    link_nodes = tree.xpath("//gmd:distributionInfo//gmd:onLine//gmd:linkage//gmd:URL/text()", namespaces=ns)
    linkxmlmetadato = [l.strip() for l in link_nodes if l.strip()]

    # ownership
    orgs = [el.text.strip() for el in tree.xpath(
        "//gmd:pointOfContact//gmd:organisationName//gco:CharacterString", namespaces=ns
    ) if el is not None and el.text]

    # tags
    tags = [el.text.strip() for el in tree.findall(".//gmd:keyword/gco:CharacterString", ns) if el.text]

    ns["gmx"] = "http://www.isotc211.org/2005/gmx"
    tags += [el.text.strip() for el in tree.findall(".//gmd:keyword/gmx:Anchor", ns) if el.text]

    # === Emitir datasetProperties ===
    props = DatasetPropertiesClass(
        name=title or "Sin título",
        description=description or "Sin descripción"
    )
    emitter.emit(MetadataChangeProposalWrapper(entityUrn=catalog_record_urn, aspect=props))
    print(f"→ DatasetProperties asignado: {title or '(sin título)'}")

    # === Ownership ===
    if orgs:
        org_name = orgs[0]
        group_urn = f"urn:li:corpGroup:{org_name.replace(' ', '_')}"
        corpgroup_info = CorpGroupInfoClass(displayName=org_name,
                                            description=f"Organisation from metadata: {org_name}", admins=[],
                                            members=[], groups=[])
        emitter.emit(MetadataChangeProposalWrapper(entityUrn=group_urn, aspect=corpgroup_info))
        ownership_aspect = OwnershipClass(
            owners=[OwnerClass(owner=group_urn, type=OwnershipTypeClass.TECHNICAL_OWNER)])
        emitter.emit(MetadataChangeProposalWrapper(entityUrn=catalog_record_urn, aspect=ownership_aspect))
        print(f"→ Ownership asignado: {org_name}")

    # === Tags ===
    if tags:
        for tag in tags:
            tag_urn = builder.make_tag_urn(tag.replace(" ", "_"))
            emitter.emit(
                MetadataChangeProposalWrapper(
                    entityUrn=tag_urn,
                    aspect=TagPropertiesClass(
                        name=tag,
                        description=f"Tag importado: {tag}"
                    )
                )
            )
        tag_associations = [
            TagAssociationClass(tag=builder.make_tag_urn(t.replace(" ", "_"))) for t in tags
        ]
        emitter.emit(
            MetadataChangeProposalWrapper(
                entityUrn=catalog_record_urn,
                aspect=GlobalTagsClass(tags=tag_associations)
            )
        )
        print(f"→ Tags asignados: {tags}")
    else:
        print("⚠ No se encontraron tags en el XML.")

    # === StructuredProperties ===
    patch_builder = DatasetPatchBuilder(catalog_record_urn)
    if language:
        patch_builder.set_structured_property("urn:li:structuredProperty:language", language)
    if issued:
        patch_builder.set_structured_property("urn:li:structuredProperty:date", issued)
    if modified:
        patch_builder.set_structured_property("urn:li:structuredProperty:fechas", modified)
    if linkxmlmetadato:
        patch_builder.set_structured_property("urn:li:structuredProperty:linkxmlmetadato", linkxmlmetadato)
    for patch_mcp in patch_builder.build():
        emitter.emit(patch_mcp)
    print(f"→ StructuredProperties asignadas: language={language}, issued={issued}, modified={modified}, linkxmlmetadato={linkxmlmetadato}")

print("🎉 Proceso de enriquecimiento de CatalogRecords completado.")
