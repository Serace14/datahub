from lxml import etree
import random
import re
import unicodedata
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.ingestion.graph.client import DataHubGraph
from datahub.ingestion.graph.config import DatahubClientConfig
from datahub.metadata.schema_classes import (
    PlatformResourceInfoClass,
    PlatformResourcesClass,
    DatasetPropertiesClass,
    OwnershipClass,
    OwnerClass,
    OwnershipTypeClass,
    TagPropertiesClass,
    TagAssociationClass,
    GlobalTagsClass,
    CorpGroupInfoClass,
)
from datahub.specific.dataset import DatasetPatchBuilder
import datahub.emitter.mce_builder as builder
from dataset_creator import create_dataset_from_catalog_record, enrich_dataset

def normalize_for_urn(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8")
    s = s.replace(" ", "_")
    s = re.sub(r"[^A-Za-z0-9_-]", "", s)
    return s

def extract_text(tree, ns, xpath_list):
    """Extrae texto del primer XPath válido encontrado."""
    for xp in xpath_list:
        elements = tree.xpath(xp, namespaces=ns)
        if elements:
            el = elements[0]
            if isinstance(el, etree._Element):
                if el.text and el.text.strip():
                    return el.text.strip()
                elif el.get("codeListValue"):
                    return el.get("codeListValue").strip()
            elif isinstance(el, str):
                return el.strip()
    return None

def get_text(tree, xpaths, ns):
    for xp in xpaths:
        try:
            elements = tree.xpath(xp, namespaces=ns)
        except Exception:
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

def associate_platform_resource_to_catalogrecord(GMS_SERVER: str, TOKEN: str, platform_resource_urn: str):
    """
    Crea un CatalogRecord a partir de un PlatformResource y lo asocia a él.
    """
    # === 1. Conectar con DataHub y recuperar PlatformResourceInfo ===
    print(f"🔍 Recuperando aspecto PlatformResourceInfo de {platform_resource_urn}")
    graph = DataHubGraph(DatahubClientConfig(server=GMS_SERVER))
    aspect_info: PlatformResourceInfoClass = graph.get_aspect(platform_resource_urn, PlatformResourceInfoClass)

    if not aspect_info or not getattr(aspect_info, "xmlText", None):
        raise ValueError(f"❌ No se pudo recuperar xmlText del PlatformResource {platform_resource_urn}")

    xml_text = aspect_info.xmlText
    primary_key = getattr(aspect_info, "primaryKey", None)
    print(f"✅ Recuperado xmlText ({len(xml_text)} bytes)")
    if primary_key:
        print(f"🔑 primaryKey encontrado: {primary_key}")
    else:
        print("⚠️ primaryKey no encontrado, se usará título como identificador alternativo")

    # === 2. Parsear XML y extraer campos relevantes ===
    tree = etree.fromstring(xml_text.encode("utf-8"))
    ns = {
        "gmd": "http://www.isotc211.org/2005/gmd",
        "gco": "http://www.isotc211.org/2005/gco",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    def extract_text(tree, ns, xpath_list):
        """Extrae texto del primer XPath válido encontrado."""
        for xp in xpath_list:
            elements = tree.xpath(xp, namespaces=ns)
            if elements:
                el = elements[0]
                if isinstance(el, etree._Element):
                    if el.text and el.text.strip():
                        return el.text.strip()
                    elif el.get("codeListValue"):
                        return el.get("codeListValue").strip()
                elif isinstance(el, str):
                    return el.strip()
        return None

    title = extract_text(tree, ns, [
        "//gmd:title/gco:CharacterString",
        "//dc:title",
    ])
    description = extract_text(tree, ns, [
        "//gmd:abstract/gco:CharacterString",
        "//dc:description",
    ])
    language = extract_text(tree, ns, [
        "//gmd:language/gmd:LanguageCode/@codeListValue",
        "//gmd:language/gmd:LanguageCode/text()",
    ])

    if not title:
        title = f"catalog-{random.randint(1000, 9999)}"

    print(f"📄 Campos extraídos:")
    print(f"   • title: {title}")
    print(f"   • description: {description or '(sin descripción)'}")
    print(f"   • language: {language or '(sin idioma)'}")

    # === 3. Crear CatalogRecord con esos datos ===
    catalog_id = primary_key or title.replace(" ", "_").lower()
    catalog_urn = f"urn:li:catalogRecord:(urn:li:dataPlatform:geoserver,{catalog_id},PROD)"

    emitter = DatahubRestEmitter(gms_server=GMS_SERVER, token=TOKEN)
    emitter.test_connection()

    dataset_properties = DatasetPropertiesClass(
        name=title,
        description=description or "Catálogo generado a partir de PlatformResource",
    )

    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=catalog_urn,
            aspect=dataset_properties,
        )
    )
    print(f"✅ CatalogRecord emitido con URN: {catalog_urn}")

    # === 4. Relacionar el PlatformResource con el CatalogRecord ===
    association_aspect = PlatformResourcesClass(resources=[platform_resource_urn])
    emitter.emit(
        MetadataChangeProposalWrapper(
            entityUrn=catalog_urn,
            aspect=association_aspect,
        )
    )
    print(f"🔗 Relación establecida entre {catalog_urn} y {platform_resource_urn}")

    # Llamada al enriquecimiento automático
    enrich_catalogrecord(GMS_SERVER, TOKEN, catalog_urn)
    dataset_urn = create_dataset_from_catalog_record(catalog_urn)
    enrich_dataset(dataset_urn, catalog_urn)

    emitter.close()
    print("🎉 Ingesta y relación completadas exitosamente.")



def enrich_catalogrecord(GMS_SERVER: str, TOKEN: str, catalog_record_urn: str):
    emitter = DatahubRestEmitter(gms_server=GMS_SERVER, token=TOKEN)
    emitter.test_connection()
    graph = DataHubGraph(DatahubClientConfig(server=GMS_SERVER))

    ns = {
        "gmd": "http://www.isotc211.org/2005/gmd",
        "gco": "http://www.isotc211.org/2005/gco",
        "dc": "http://purl.org/dc/elements/1.1/",
        "dct": "http://purl.org/dc/terms/",
        "gmx": "http://www.isotc211.org/2005/gmx",
        "xlink": "http://www.w3.org/1999/xlink",
        "ows": "http://www.opengis.net/ows",
    }

    # Recuperar PlatformResource asociado
    query = """
    query getCatalogWithRelationships($urn: String!) {
      catalogRecord(urn: $urn) {
        relationships(input: {types: ["AssociatedWith"], direction: OUTGOING}) {
          relationships { entity { urn } type }
        }
      }
    }
    """
    res = graph.execute_graphql(query, {"urn": catalog_record_urn})
    relationships = res.get("catalogRecord", {}).get("relationships", {}).get("relationships", [])
    if not relationships:
        print(f"No se encontró PlatformResource asociado a {catalog_record_urn}")
        return

    platform_urn = relationships[0]["entity"]["urn"]
    aspect_info: PlatformResourceInfoClass = graph.get_aspect(platform_urn, PlatformResourceInfoClass)
    xml_text = aspect_info.xmlText.encode("utf-8")
    tree = etree.fromstring(xml_text)

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
    ) if el.text]

    # tags
    tags = [el.text.strip() for el in tree.findall(".//gmd:keyword/gco:CharacterString", ns) if el.text]
    ns["gmx"] = "http://www.isotc211.org/2005/gmx"
    tags += [el.text.strip() for el in tree.findall(".//gmd:keyword/gmx:Anchor", ns) if el.text]

    # Emitir DatasetProperties
    props = DatasetPropertiesClass(name=title or "Sin título", description=description or "Sin descripción")
    emitter.emit(MetadataChangeProposalWrapper(entityUrn=catalog_record_urn, aspect=props))

    # Ownership
    if orgs:
        org_name = orgs[0]
        group_urn = f"urn:li:corpGroup:{org_name.replace(' ', '_')}"
        corpgroup_info = CorpGroupInfoClass(displayName=org_name,
                                            description=f"Organisation from metadata: {org_name}",
                                            admins=[], members=[], groups=[])
        emitter.emit(MetadataChangeProposalWrapper(entityUrn=group_urn, aspect=corpgroup_info))
        ownership_aspect = OwnershipClass(owners=[OwnerClass(owner=group_urn, type=OwnershipTypeClass.TECHNICAL_OWNER)])
        emitter.emit(MetadataChangeProposalWrapper(entityUrn=catalog_record_urn, aspect=ownership_aspect))

    # Tags
    if tags:
        for tag in tags:
            tag_urn = builder.make_tag_urn(tag.replace(" ", "_"))
            emitter.emit(MetadataChangeProposalWrapper(
                entityUrn=tag_urn,
                aspect=TagPropertiesClass(name=tag, description=f"Tag importado: {tag}")
            ))
        tag_associations = [TagAssociationClass(tag=builder.make_tag_urn(t.replace(" ", "_"))) for t in tags]
        emitter.emit(MetadataChangeProposalWrapper(entityUrn=catalog_record_urn, aspect=GlobalTagsClass(tags=tag_associations)))

    # Structured properties
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

    emitter.close()
    print(f"Enriquecimiento completado para {catalog_record_urn}")
