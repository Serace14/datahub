from datahub.metadata._internal_schema_classes import DomainsClass, DomainPropertiesClass, CorpGroupInfoClass, \
    OwnershipClass, OwnerClass, OwnershipTypeClass, TagAssociationClass, GlobalTagsClass, TagPropertiesClass
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.emitter.mce_builder import make_dataset_urn
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import DatasetPropertiesClass
from datahub.specific.dataset import DatasetPatchBuilder
from datahub.metadata.schema_classes import DataProductPropertiesClass, DataProductAssociationClass, PlatformResourceInfoClass
from lxml import etree
import datahub.emitter.mce_builder as builder
import random
from datahub.ingestion.graph.client import DataHubGraph
from datahub.ingestion.graph.config import DatahubClientConfig

# === Configuración DataHub ===
GMS_SERVER = "http://localhost:8080"
TOKEN = "eyJhbGciOiJIUzI1NiJ9..."  # tu token válido

emitter = DatahubRestEmitter(gms_server=GMS_SERVER, token=TOKEN)
emitter.test_connection()
graph = DataHubGraph(DatahubClientConfig(server=GMS_SERVER))

# === Namespaces para parsear XML ===
ns = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ows": "http://www.opengis.net/ows"
}

# === Lista de CatalogRecords a procesar (puedes modificar según tu caso) ===
catalog_record_urns = [
    "urn:li:catalogRecord:(urn:li:dataPlatform:geoserver,7eea5c42-212f-4099-b9df-1e3703fbc616,PROD)",
    # agrega más si es necesario
]

for catalog_record_urn in catalog_record_urns:
    print(f"🔍 Procesando CatalogRecord {catalog_record_urn}...")

    # === Obtener PlatformResource asociado ===
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
    relationships = res["catalogRecord"].get("relationships", {}).get("relationships", [])
    if not relationships:
        print(f"⚠ No se encontró PlatformResource asociado a {catalog_record_urn}")
        continue

    platform_urn = relationships[0]["entity"]["urn"]
    print(f"✅ CatalogRecord asociado a PlatformResource {platform_urn}")

    # === Obtener xmlText del PlatformResource ===
    aspect_info: PlatformResourceInfoClass = graph.get_aspect(platform_urn, PlatformResourceInfoClass)
    if not aspect_info or not getattr(aspect_info, "xmlText", None):
        print(f"⚠ No se pudo recuperar xmlText de {platform_urn}")
        continue

    xml_text = aspect_info.xmlText
    if isinstance(xml_text, str):
        xml_text = xml_text.encode("utf-8")
    tree = etree.fromstring(xml_text)

    # === Extraer dataset_id y título ===
    primary_key = getattr(aspect_info, "primaryKey", None)

    identifier = None
    el = tree.find(".//dc:identifier", ns)
    if el is not None and el.text:
        identifier = el.text.strip()
    if not identifier:
        el = tree.find(".//gmd:fileIdentifier/gco:CharacterString", ns)
        if el is not None and el.text:
            identifier = el.text.strip()

    title_el = tree.find(".//gmd:title/gco:CharacterString", ns)
    title = title_el.text.strip() if title_el is not None else f"dataset-{random.randint(1000,9999)}"

    dataset_id = (primary_key or identifier or title).replace(" ", "_").lower()
    abstract_el = tree.find(".//gmd:abstract/gco:CharacterString", ns)
    abstract = abstract_el.text.strip() if abstract_el is not None else "Sin descripción"

    dataset_urn = make_dataset_urn(platform="geoserver", name=dataset_id, env="PROD")

    # === Emitir Dataset básico ===
    dataset_properties = DatasetPropertiesClass(
        name=title,
        description=abstract
    )
    emitter.emit(MetadataChangeProposalWrapper(entityUrn=dataset_urn, aspect=dataset_properties))
    print(f"✅ Dataset creado: {dataset_urn}")

    # ========================
    # (1) StructuredProperty: ID
    # ========================
    id_value = primary_key or identifier
    if id_value:
        patch_builder = DatasetPatchBuilder(dataset_urn)
        patch_builder.set_structured_property("urn:li:structuredProperty:id", id_value)
        for patch_mcp in patch_builder.build():
            emitter.emit(patch_mcp)
        print(f"→ ID agregado: {id_value}")

    # ========================
    # (2) BoundingBox
    # ========================
    bbox_values = []
    bbox_el = tree.find(".//ows:BoundingBox", ns)
    if bbox_el is not None:
        lower = bbox_el.find("ows:LowerCorner", ns)
        upper = bbox_el.find("ows:UpperCorner", ns)
        if lower is not None and upper is not None:
            lower_coords = lower.text.strip().split()
            upper_coords = upper.text.strip().split()
            bbox_values = lower_coords + upper_coords
    if not bbox_values:
        bbox_el = tree.find(".//gmd:EX_GeographicBoundingBox", ns)
        if bbox_el is not None:
            west = bbox_el.find("gmd:westBoundLongitude/gco:Decimal", ns)
            east = bbox_el.find("gmd:eastBoundLongitude/gco:Decimal", ns)
            south = bbox_el.find("gmd:southBoundLatitude/gco:Decimal", ns)
            north = bbox_el.find("gmd:northBoundLatitude/gco:Decimal", ns)
            if west is not None and east is not None and south is not None and north is not None:
                bbox_values = [west.text, south.text, east.text, north.text]

    if bbox_values:
        patch_builder = DatasetPatchBuilder(dataset_urn)
        patch_builder.set_structured_property("urn:li:structuredProperty:boundingbox", bbox_values)
        for patch_mcp in patch_builder.build():
            emitter.emit(patch_mcp)
        print(f"→ BoundingBox agregado: {bbox_values}")

    # ========================
    # (3) DataProduct
    # ========================
    dataproduct_name = "CSW"
    dataproduct_urn = f"urn:li:dataProduct:{dataproduct_name}"
    dp_properties = DataProductPropertiesClass(
        name=dataproduct_name,
        description=f"DataProduct generado automáticamente a partir del dataset {dataset_id}",
        assets=[DataProductAssociationClass(destinationUrn=dataset_urn)],
    )
    emitter.emit(MetadataChangeProposalWrapper(entityUrn=dataproduct_urn, aspect=dp_properties))
    print(f"→ DataProduct {dataproduct_urn} creado y asociado con {dataset_urn}")

    # ========================
    # (4) Fecha
    # ========================
    date_value = None
    el = tree.find(".//dc:date", ns)
    if el is not None and el.text:
        date_value = el.text.strip()
    if not date_value:
        el = tree.find(".//gmd:dateStamp/gco:Date", ns)
        if el is not None and el.text:
            date_value = el.text.strip()
    if not date_value:
        el = tree.find(".//gmd:citation//gmd:date/gco:Date", ns)
        if el is not None and el.text:
            date_value = el.text.strip()

    if date_value:
        patch_builder = DatasetPatchBuilder(dataset_urn)
        patch_builder.set_structured_property("urn:li:structuredProperty:date", date_value)
        for patch_mcp in patch_builder.build():
            emitter.emit(patch_mcp)
        print(f"→ Fecha asignada: {date_value}")

    # ========================
    # (5) Dominio
    # ========================
    domain_name = "Datos_Espaciales"
    domain_description = "Dominio general para datasets espaciales importados desde PlatformResource"
    domain_urn = builder.make_domain_urn(domain_name)
    emitter.emit(MetadataChangeProposalWrapper(entityUrn=domain_urn, aspect=DomainPropertiesClass(name=domain_name, description=domain_description)))
    emitter.emit(MetadataChangeProposalWrapper(entityUrn=dataset_urn, aspect=DomainsClass(domains=[domain_urn])))
    print(f"→ Dominio asignado: {domain_name}")

    # ========================
    # (6) Lenguaje
    # ========================
    language_value = None
    el = tree.find(".//dc:language", ns)
    if el is not None and el.text:
        language_value = el.text.strip()
    if not language_value:
        el = tree.find(".//gmd:language/gmd:LanguageCode", ns)
        if el is not None:
            language_value = el.get("codeListValue", None)
            if language_value:
                language_value = language_value.strip()
    if language_value:
        patch_builder = DatasetPatchBuilder(dataset_urn)
        patch_builder.set_structured_property("urn:li:structuredProperty:language", language_value)
        for patch_mcp in patch_builder.build():
            emitter.emit(patch_mcp)
        print(f"→ Language asignado: {language_value}")

    # ========================
    # (7) Ownership (organisationName)
    # ========================
    orgs = [el.text.strip() for el in tree.findall(".//gmd:pointOfContact//gmd:organisationName//gco:CharacterString", ns) if el.text]
    if orgs:
        org_name = orgs[0]
        group_urn = f"urn:li:corpGroup:{org_name.replace(' ', '_')}"
        corpgroup_info = CorpGroupInfoClass(displayName=org_name, description=f"Organisation from metadata: {org_name}", admins=[], members=[], groups=[])
        emitter.emit(MetadataChangeProposalWrapper(entityUrn=group_urn, aspect=corpgroup_info))
        ownership_aspect = OwnershipClass(owners=[OwnerClass(owner=group_urn, type=OwnershipTypeClass.TECHNICAL_OWNER)])
        emitter.emit(MetadataChangeProposalWrapper(entityUrn=dataset_urn, aspect=ownership_aspect))
        print(f"→ Ownership asignado: {org_name}")

    # ========================
    # (8) Rights
    # ========================
    rights_values = []
    els = tree.findall(".//dc:rights", ns)
    for el in els:
        if el is not None and el.text:
            rights_values.append(el.text.strip())
    legal_constraints = tree.findall(".//gmd:resourceConstraints//gmd:MD_LegalConstraints", ns)
    for lc in legal_constraints:
        for el in lc.findall(".//gmd:accessConstraints//gmd:MD_RestrictionCode", ns):
            if el is not None and el.get("codeListValue"):
                rights_values.append(el.get("codeListValue"))
        for el in lc.findall(".//gmd:useConstraints//gmd:MD_RestrictionCode", ns):
            if el is not None and el.get("codeListValue"):
                rights_values.append(el.get("codeListValue"))
        for el in lc.findall(".//gmd:otherConstraints//gco:CharacterString", ns):
            if el is not None and el.text:
                rights_values.append(el.text.strip())
    if rights_values:
        patch_builder = DatasetPatchBuilder(dataset_urn)
        patch_builder.set_structured_property("urn:li:structuredProperty:rights", rights_values)
        for patch_mcp in patch_builder.build():
            emitter.emit(patch_mcp)
        print(f"→ Rights asignados: {rights_values}")

    # ========================
    # (9) Tags & GlossaryTerms
    # ========================

    from datahub.metadata.schema_classes import (
        GlossaryTermInfoClass,
        GlossaryTermsClass,
        GlossaryTermAssociationClass,
        AuditStampClass,
        TagPropertiesClass,
        TagAssociationClass,
        GlobalTagsClass,
    )
    from datahub.emitter.mce_builder import make_term_urn
    import time

    ns["gmx"] = "http://www.isotc211.org/2005/gmx"

    simple_tags = []
    glossary_candidates = []

    # ================
    # 1. CharacterString → TAG
    # ================
    for el in tree.findall(".//gmd:keyword/gco:CharacterString", ns):
        if el.text:
            kw = el.text.strip()
            simple_tags.append(kw)

    # ================
    # 2. gmx:Anchor → GLOSSARY
    # ================
    for el in tree.findall(".//gmd:keyword/gmx:Anchor", ns):
        if el.text:
            glossary_candidates.append({
                "term": el.text.strip(),
                "definition": el.get("href", "Imported from CSW Anchor")
            })
            # evitar duplicado como tag
            if el.text.strip() in simple_tags:
                simple_tags.remove(el.text.strip())

    # ================
    # 3. Keywords con tipo → depende
    # ================
    CONTROLLED_TYPES = {"place", "discipline", "temporal", "stratum"}

    for block in tree.findall(".//gmd:descriptiveKeywords", ns):

        kw_type_el = block.find(".//gmd:type/gmd:MD_KeywordTypeCode", ns)
        kw_type = kw_type_el.get("codeListValue") if kw_type_el is not None else None
        kw_type_lower = kw_type.lower() if kw_type else None

        kws = [
            el.text.strip()
            for el in block.findall(".//gmd:keyword//gco:CharacterString", ns)
            if el.text
        ]

        # Caso 1: sin tipo → TAGS
        if not kw_type:
            continue

        # Caso 2: theme → TAGS
        if kw_type_lower == "theme":
            continue

        # Caso 3: tipo controlado → GLOSSARY
        if kw_type_lower in CONTROLLED_TYPES:
            for kw in kws:
                glossary_candidates.append({
                    "term": kw,
                    "definition": f"Keyword ({kw_type}) imported from CSW"
                })
                if kw in simple_tags:
                    simple_tags.remove(kw)
            continue

        # Caso 4: otros tipos raros → TAGS
        continue

    # ================
    # 4. dc:subject → TAGS
    # ================
    for el in tree.findall(".//dc:subject", ns):
        if el.text:
            kw = el.text.strip()
            if kw not in simple_tags:
                simple_tags.append(kw)

    # ========================
    # Crear TAGS
    # ========================
    for tag in simple_tags:
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

    if simple_tags:
        tag_associations = [
            TagAssociationClass(tag=builder.make_tag_urn(t.replace(" ", "_")))
            for t in simple_tags
        ]
        emitter.emit(
            MetadataChangeProposalWrapper(
                entityUrn=dataset_urn,
                aspect=GlobalTagsClass(tags=tag_associations)
            )
        )
        print(f"→ Tags asignados: {simple_tags}")
    else:
        print("⚠ No se encontraron tags simples.")

    # ========================
    # Crear Glossary Terms
    # ========================

    glossary_associations = []

    for item in glossary_candidates:
        term_name = item["term"]
        definition = item.get("definition") or "Imported from metadata"

        if not definition or definition.strip() == "":
            definition = "Imported from metadata"

        term_id = term_name.replace(" ", "_").replace("/", "_")
        term_urn = make_term_urn(term_id)

        term_info = GlossaryTermInfoClass(
            name=term_name,
            definition=definition,
            termSource="EXTERNAL"
        )

        emitter.emit(
            MetadataChangeProposalWrapper(
                entityUrn=term_urn,
                aspect=term_info,
            )
        )

        glossary_associations.append(
            GlossaryTermAssociationClass(urn=term_urn)
        )

    if glossary_associations:
        emitter.emit(
            MetadataChangeProposalWrapper(
                entityUrn=dataset_urn,
                aspect=GlossaryTermsClass(
                    terms=glossary_associations,
                    auditStamp=AuditStampClass(
                        time=int(time.time() * 1000),
                        actor="urn:li:corpuser:ingestion"
                    )
                )
            )
        )
        print(f"→ Glossary terms asignados: {[g.urn for g in glossary_associations]}")
    else:
        print("⚠ No se encontraron glossary terms.")

    # ========================
    # (10) Tipo
    # ========================
    type_value = None
    el = tree.find(".//dc:type", ns)
    if el is not None and el.text:
        type_value = el.text.strip()
    if not type_value:
        el = tree.find(".//gmd:hierarchyLevel/gmd:MD_ScopeCode", ns)
        if el is not None:
            type_value = el.get("codeListValue", None)
            if type_value:
                type_value = type_value.strip()
    if type_value:
        patch_builder = DatasetPatchBuilder(dataset_urn)
        patch_builder.set_structured_property("urn:li:structuredProperty:type", type_value)
        for patch_mcp in patch_builder.build():
            emitter.emit(patch_mcp)
        print(f"→ Type asignado: {type_value}")

    # ========================
    # (11) URLs
    # ========================
    urls = set()

    # Buscar URLs en GMD directamente desde xmlText del PlatformResource
    # gmd:distributionInfo/onLine/linkage/URL
    for el in tree.findall(".//gmd:distributionInfo//gmd:onLine//gmd:linkage//gmd:URL", ns):
        if el is not None and el.text:
            urls.add(el.text.strip())

    # gmd:distributionInfo/MD_DigitalTransferOptions/onLine/URL
    for el in tree.findall(".//gmd:distributionInfo//gmd:MD_DigitalTransferOptions//gmd:onLine//gmd:URL", ns):
        if el is not None and el.text:
            urls.add(el.text.strip())

    # dc:references
    for el in tree.findall(".//dc:references", ns):
        if el is not None and el.text:
            urls.add(el.text.strip())

    # dc:URI
    for el in tree.findall(".//dc:URI", ns):
        if el is not None and el.text:
            urls.add(el.text.strip())

    # Guardar en DataHub
    urls_list = list(urls)
    print("URLs encontradas:", urls_list)

    if urls_list:
        patch_builder = DatasetPatchBuilder(dataset_urn)
        patch_builder.set_structured_property(
            "urn:li:structuredProperty:urls",
            urls_list
        )
        for patch_mcp in patch_builder.build():
            emitter.emit(patch_mcp)
        print(f"→ Structured property 'urls' actualizada para {dataset_urn}")
    else:
        print("⚠ No se encontró ninguna URL en el XML.")

print("✅ Todos los datasets procesados correctamente.")
