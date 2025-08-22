from datahub.metadata._internal_schema_classes import DomainsClass, DomainPropertiesClass, CorpGroupInfoClass, \
    OwnershipClass, OwnerClass, OwnershipTypeClass, TagAssociationClass, GlobalTagsClass, TagPropertiesClass
from owslib.csw import CatalogueServiceWeb
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.emitter.mce_builder import make_dataset_urn
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import DatasetPropertiesClass
from datahub.specific.dataset import DatasetPatchBuilder
from datahub.metadata.schema_classes import (
    DataProductPropertiesClass,
    DataProductAssociationClass,
)
from lxml import etree
import datahub.emitter.mce_builder as builder

# === Configuración DataHub ===
emitter = DatahubRestEmitter(
    gms_server="http://localhost:8080",  # Cambia si tu DataHub está en otra URL
    token="eyJhbGciOiJIUzI1NiJ9.eyJhY3RvclR5cGUiOiJVU0VSIiwiYWN0b3JJZCI6ImRhdGFodWIiLCJ0eXBlIjoiUEVSU09OQUwiLCJ2ZXJzaW9uIjoiMiIsImp0aSI6ImJjYzI0YTMwLThiZTUtNGNhMy04MzQ5LTEzYTU0MzJiODE5ZCIsInN1YiI6ImRhdGFodWIiLCJleHAiOjE3NjM0NjA2NTgsImlzcyI6ImRhdGFodWItbWV0YWRhdGEtc2VydmljZSJ9.5S4rfT3P7jdFAutiT5VlqcaOWpyibr7sxc1dD2_7BNw"
)
emitter.test_connection()

# === Conexión al CSW ===
csw = CatalogueServiceWeb('https://www.mapama.gob.es/ide/metadatos/srv/spa/csw')

# === Namespaces para parsear XML ===
ns = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ows": "http://www.opengis.net/ows"
}

start = 0
pagesize = 50  # Número de registros por petición

while True:
    csw.getrecords2(startposition=start + 1, maxrecords=pagesize, esn='full')

    if not csw.records:
        break

    for rec_id, record in csw.records.items():
        dataset_id = record.identifier or f"csw-{rec_id}"
        title = record.title or "Sin título"
        abstract = record.abstract or "Sin descripción"

        dataset_urn = make_dataset_urn(
            platform="geoserver",
            name=dataset_id,
            env="PROD"
        )

        # Emitir propiedades básicas
        dataset_properties = DatasetPropertiesClass(
            name=title,
            description=abstract
        )
        metadata_event = MetadataChangeProposalWrapper(
            entityUrn=dataset_urn,
            aspect=dataset_properties
        )
        emitter.emit(metadata_event)
        print(f"Dataset enviado: {title}")

        # === Obtener XML completo del dataset ===
        csw.getrecordbyid(id=[record.identifier], outputschema="http://www.isotc211.org/2005/gmd")
        xml_raw = csw.response
        if isinstance(xml_raw, str):
            xml_raw = xml_raw.encode("utf-8")
        tree = etree.fromstring(xml_raw)

        # ========================
        # (1) Extraer y guardar ID
        # ========================
        id_value = None
        el = tree.find(".//dc:identifier", ns)
        if el is not None and el.text:
            id_value = el.text.strip()

        if not id_value:
            el = tree.find(".//gmd:fileIdentifier/gco:CharacterString", ns)
            if el is not None and el.text:
                id_value = el.text.strip()

        if id_value:
            patch_builder = DatasetPatchBuilder(dataset_urn)
            patch_builder.set_structured_property(
                "urn:li:structuredProperty:37a61c93-b1aa-4261-90e8-947771c3582b",  # structured property ID
                id_value
            )
            for patch_mcp in patch_builder.build():
                emitter.emit(patch_mcp)
            print(f"→ ID agregado al dataset {dataset_urn}: {id_value}")
        else:
            print(f"⚠ No se encontró ID en {dataset_id}")

        # ========================
        # (2) Extraer y guardar BoundingBox
        # ========================
        bbox_values = []

        # Intentar OWS
        bbox_el = tree.find(".//ows:BoundingBox", ns)
        if bbox_el is not None:
            lower = bbox_el.find("ows:LowerCorner", ns)
            upper = bbox_el.find("ows:UpperCorner", ns)
            if lower is not None and upper is not None:
                lower_coords = lower.text.strip().split()
                upper_coords = upper.text.strip().split()
                bbox_values = lower_coords + upper_coords

        # Intentar ISO si no hay OWS
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
            patch_builder.set_structured_property(
                "urn:li:structuredProperty:boundingbox",  # tu structured property para bbox
                bbox_values
            )
            for patch_mcp in patch_builder.build():
                emitter.emit(patch_mcp)
            print(f"→ BoundingBox agregado al dataset {dataset_urn}: {bbox_values}")
        else:
            print(f"⚠ No se encontró bbox en {dataset_id}")

        # ========================
        # (3) Crear DataProduct si no existe y asociarlo al dataset
        # ========================
        dataproduct_name = "CSW"  # Nombre genérico, puedes ajustarlo
        dataproduct_urn = f"urn:li:dataProduct:{dataproduct_name}"

        dataset_urn = builder.make_dataset_urn(
            platform="geoserver",
            name=dataset_id,
            env="PROD"
        )

        dp_properties = DataProductPropertiesClass(
            name=dataproduct_name,
            description=f"DataProduct generado automáticamente a partir del dataset {dataset_id}",
            assets=[DataProductAssociationClass(destinationUrn=dataset_urn)],
        )

        mcp = MetadataChangeProposalWrapper(
            entityUrn=dataproduct_urn,
            aspect=dp_properties,
        )
        emitter.emit(mcp)
        print(f"→ DataProduct {dataproduct_urn} creado/actualizado y asociado con {dataset_urn}")

        # ========================
        # (4) Extraer y guardar Fecha
        # ========================
        date_value = None

        # Intentar dc:date
        el = tree.find(".//dc:date", ns)
        if el is not None and el.text:
            date_value = el.text.strip()

        # Si no hay, intentar gmd:dateStamp/gco:Date
        if not date_value:
            el = tree.find(".//gmd:dateStamp/gco:Date", ns)
            if el is not None and el.text:
                date_value = el.text.strip()

        # Si no hay, intentar gmd:citation//gmd:date/gco:Date
        if not date_value:
            el = tree.find(".//gmd:citation//gmd:date/gco:Date", ns)
            if el is not None and el.text:
                date_value = el.text.strip()

        print("Fecha encontrada:", date_value)

        # Asignar la fecha al dataset usando GenericAspect

        if date_value:
            # URN del dataset
            dataset_urn = make_dataset_urn(
                platform="geoserver",
                name=dataset_id,
                env="PROD"
            )

            # Crear el patch para la structured property
            patch_builder = DatasetPatchBuilder(dataset_urn)
            patch_builder.set_structured_property(
                "urn:li:structuredProperty:be175e19-c07a-40ab-8228-52094c78edd8",
                date_value
            )
            patch_mcps = patch_builder.build()

            # Emitir el patch
            for patch_mcp in patch_mcps:
                emitter.emit(patch_mcp)

            print(f"Structured property 'date' actualizada para (dataset_urn): {date_value}")
            print(f"Fecha asignada al dataset {dataset_urn}: {date_value}")
        else:
            print("No se encontró ninguna fecha en el XML.")

        # ========================
        # Definir el dominio
        # ========================
        domain_name = "Datos_Espaciales"
        domain_description = "Dominio general para datasets espaciales importados desde CSW"
        domain_urn = builder.make_domain_urn(domain_name)

        # ========================
        # (5)Crear y asignar dominio
        # ========================
        domain_aspect = DomainPropertiesClass(
            name=domain_name,
            description=domain_description
        )
        emitter.emit(MetadataChangeProposalWrapper(entityUrn=domain_urn, aspect=domain_aspect))
        print(f"Dominio creado/actualizado: {domain_urn}")

        # Asignar el dominio al dataset
        domains_aspect = DomainsClass(domains=[domain_urn])
        dataset_domain_mcp = MetadataChangeProposalWrapper(
            entityUrn=dataset_urn,
            aspect=domains_aspect
        )
        emitter.emit(dataset_domain_mcp)
        print(f"Dominio asignado al dataset (dataset_urn): {domain_name}")

        # ========================
        # (6)Crear y asignar el lenguaje
        # ========================
        language_value = None

        # Intentar dc:language
        el = tree.find(".//dc:language", ns)
        if el is not None and el.text:
            language_value = el.text.strip()

        # Si no hay, intentar gmd:language/gmd:LanguageCode/@codeListValue
        if not language_value:
            el = tree.find(".//gmd:language/gmd:LanguageCode", ns)
            if el is not None:
                language_value = el.get("codeListValue")
                if language_value:
                    language_value = language_value.strip()

        print("Language encontrado:", language_value)

        # Asignar el lenguaje al dataset
        if language_value:
            # URN del dataset
            dataset_urn = make_dataset_urn(
                platform="geoserver",
                name=dataset_id,
                env="PROD"
            )

            # Crear el patch para la structured property
            patch_builder = DatasetPatchBuilder(dataset_urn)
            patch_builder.set_structured_property(
                "urn:li:structuredProperty:acdd5c4c-5463-47b5-a748-55d9955c776d",
                language_value
            )
            patch_mcps = patch_builder.build()

            # Emitir el patch
            for patch_mcp in patch_mcps:
                emitter.emit(patch_mcp)

            print(f"Structured property 'id' actualizada para ({dataset_urn}) {language_value}")
        else:
            print("No se encontró ningun id en el XML.")

        # ========================
        # (7) Extracción Y asignación de ownership (organisationName)
        # ========================
        orgs = [
            el.text.strip()
            for el in tree.findall(
                ".//gmd:pointOfContact//gmd:organisationName//gco:CharacterString", ns
            )
            if el.text
        ]

        if orgs:
            org_name = orgs[0]
            group_urn = f"urn:li:corpGroup:{org_name.replace(' ', '_')}"

            # Emitir el corpGroup
            corpgroup_info = CorpGroupInfoClass(
                displayName=org_name,
                description=f"Organisation from CSW metadata: {org_name}",
                admins=[],
                members=[],
                groups=[]
            )
            emitter.emit(
                MetadataChangeProposalWrapper(entityUrn=group_urn, aspect=corpgroup_info)
            )
            print(f"CorpGroup emitido: {group_urn}")

            # Construcción del Ownership
            ownership_aspect = OwnershipClass(
                owners=[
                    OwnerClass(
                        owner=group_urn,
                        type=OwnershipTypeClass.TECHNICAL_OWNER,  # puedes ajustar el tipo
                    )
                ]
            )

            # URN del dataset (ejemplo)
            dataset_urn = builder.make_dataset_urn(
                platform="geoserver",
                name=dataset_id,
                env="PROD",
            )

            # Emitir ownership al dataset
            emitter.emit(
                MetadataChangeProposalWrapper(entityUrn=dataset_urn, aspect=ownership_aspect)
            )
            print(f"Ownership asociado a {dataset_urn}: {org_name}")
        else:
            print("No se encontró organisationName en el XML.")

        # ========================
        # (8) Extracción de rights y asignarlas
        # ========================
        rights_values = []

        # CSW simple: <dc:rights>
        els = tree.findall(".//dc:rights", ns)
        for el in els:
            if el is not None and el.text:
                rights_values.append(el.text.strip())

        # ISO: gmd:resourceConstraints/gmd:MD_LegalConstraints
        legal_constraints = tree.findall(".//gmd:resourceConstraints//gmd:MD_LegalConstraints", ns)
        for lc in legal_constraints:
            # accessConstraints
            els = lc.findall(".//gmd:accessConstraints//gmd:MD_RestrictionCode", ns)
            for el in els:
                if el is not None and el.get("codeListValue"):
                    rights_values.append(el.get("codeListValue"))

            # useConstraints
            els = lc.findall(".//gmd:useConstraints//gmd:MD_RestrictionCode", ns)
            for el in els:
                if el is not None and el.get("codeListValue"):
                    rights_values.append(el.get("codeListValue"))

            # otherConstraints
            els = lc.findall(".//gmd:otherConstraints//gco:CharacterString", ns)
            for el in els:
                if el is not None and el.text:
                    rights_values.append(el.text.strip())

        print("Rights encontrados:", rights_values)

        # Asignar las rights al dataset usando GenericAspect
        if rights_values:
            dataset_urn = make_dataset_urn(
                platform="geoserver",
                name=dataset_id,
                env="PROD"
            )

            patch_builder = DatasetPatchBuilder(dataset_urn)
            patch_builder.set_structured_property(
                "urn:li:structuredProperty:rights",
                rights_values
            )
            patch_mcps = patch_builder.build()

            for patch_mcp in patch_mcps:
                emitter.emit(patch_mcp)

            print(f"Structured property 'rights' actualizada para ({dataset_urn})")
        else:
            print("No se encontró ningún rights en el XML.")

        # ========================
        # (9)Extracción de tags (keywords), creación y asignación
        # ========================
        tags = [
            el.text.strip()
            for el in tree.findall(".//gmd:keyword/gco:CharacterString", ns)
            if el.text
        ]
        print("Tags extraídos:", tags)

        # Ingesta de tags en DataHub
        for tag in tags:
            tag_urn = builder.make_tag_urn(tag.replace(" ", "_"))
            tag_aspect = TagPropertiesClass(
                name=tag,
                description=f"Tag importado desde CSW: {tag}"
            )
            emitter.emit(MetadataChangeProposalWrapper(entityUrn=tag_urn, aspect=tag_aspect))
            print(f"Tag creado/actualizado: {tag_urn}")

        # Asignar tags a un dataset ya creado
        if tags:
            # Convertir los tags a URNs
            tag_associations = [TagAssociationClass(tag=builder.make_tag_urn(t.replace(" ", "_"))) for t in tags]

            # URN del dataset existente
            dataset_urn = builder.make_dataset_urn(
                platform="geoserver",
                name=dataset_id,
                env="PROD",
            )

            # Crear la propuesta de cambio solo para GlobalTags
            dataset_tags_mcp = MetadataChangeProposalWrapper(
                entityUrn=dataset_urn,
                aspect=GlobalTagsClass(tags=tag_associations)
            )

            emitter.emit(dataset_tags_mcp)
            print(f"Tags asignados al dataset existente {dataset_urn}: {tags}")
        else:
            print("No se encontraron tags en el XML.")

        # ========================
        # (10)Extracción del tipo y asignación
        # ========================
        type_value = None

        # Intentar dc:type
        el = tree.find(".//dc:type", ns)
        if el is not None and el.text:
            type_value = el.text.strip()

        # Si no hay, intentar gmd:hierarchyLevel/gmd:MD_ScopeCode/@codeListValue
        if not type_value:
            el = tree.find(".//gmd:hierarchyLevel/gmd:MD_ScopeCode", ns)
            if el is not None:
                type_value = el.get("codeListValue")
                if type_value:
                    type_value = type_value.strip()

        print("Type encontrado:", type_value)

        # Asignar el ID al dataset usando GenericAspect
        if type_value:
            # URN del dataset
            dataset_urn = make_dataset_urn(
                platform="geoserver",
                name=dataset_id,
                env="PROD"
            )

            # Crear el patch para la structured property
            patch_builder = DatasetPatchBuilder(dataset_urn)
            patch_builder.set_structured_property(
                "urn:li:structuredProperty:dce65839-7577-4ddf-881c-95df4c30a514",
                type_value
            )
            patch_mcps = patch_builder.build()

            # Emitir el patch
            for patch_mcp in patch_mcps:
                emitter.emit(patch_mcp)

            print(f"Structured property 'id' actualizada para ({dataset_urn}) {type_value}")
        else:
            print("No se encontró ningun id en el XML.")

        # ========================
        # Extracción de URLs y asignación
        # ========================
        urls = set()

        # Extracción desde CSW (dc:*)
        csw.getrecordbyid(id=[dataset_id], outputschema="http://www.opengis.net/cat/csw/2.0.2")
        xml_raw = csw.response
        if isinstance(xml_raw, str):
            xml_raw = xml_raw.encode("utf-8")
        tree_csw = etree.fromstring(xml_raw)

        ns_csw = {
            "dc": "http://purl.org/dc/elements/1.1/",
            "dct": "http://purl.org/dc/terms/",
        }

        # dc:references
        for el in tree_csw.findall(".//dc:references", ns_csw):
            if el is not None and el.text:
                urls.add(el.text.strip())

        # dc:URI
        for el in tree_csw.findall(".//dc:URI", ns_csw):
            if el is not None and el.text:
                urls.add(el.text.strip())

        # ========================
        # Extracción desde GMD (gmd:*)
        # ========================
        csw.getrecordbyid(id=[dataset_id], outputschema="http://www.isotc211.org/2005/gmd")
        xml_raw = csw.response
        if isinstance(xml_raw, str):
            xml_raw = xml_raw.encode("utf-8")
        tree_gmd = etree.fromstring(xml_raw)

        ns_gmd = {
            "gmd": "http://www.isotc211.org/2005/gmd",
            "gco": "http://www.isotc211.org/2005/gco",
        }

        # gmd:distributionInfo/onLine/linkage/URL
        for el in tree_gmd.findall(".//gmd:distributionInfo//gmd:onLine//gmd:linkage//gmd:URL", ns_gmd):
            if el is not None and el.text:
                urls.add(el.text.strip())

        # gmd:distributionInfo/MD_DigitalTransferOptions/onLine/URL
        for el in tree_gmd.findall(".//gmd:distributionInfo//gmd:MD_DigitalTransferOptions//gmd:onLine//gmd:URL",
                                   ns_gmd):
            if el is not None and el.text:
                urls.add(el.text.strip())

        # ========================
        # Guardar en DataHub
        # ========================
        urls_list = list(urls)
        print("URLs encontradas:", urls_list)

        if urls_list:
            dataset_urn = make_dataset_urn(
                platform="geoserver",
                name=dataset_id,
                env="PROD"
            )

            patch_builder = DatasetPatchBuilder(dataset_urn)
            patch_builder.set_structured_property(
                "urn:li:structuredProperty:c4fe8236-87ff-4310-ac79-6468b4633634",
                urls_list
            )
            patch_mcps = patch_builder.build()

            for patch_mcp in patch_mcps:
                emitter.emit(patch_mcp)

            print(f"Structured property 'urls' actualizada para ({dataset_urn})")
        else:
            print("No se encontró ninguna URL en el XML.")

    start += pagesize
    if start >= csw.results.get('matches', 0):
        break

print("✅ Todos los datasets enviados con ID, BoundingBox y DataProduct.")
