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
from propiedades_simples import PROPERTIES_TO_EXTRACT
from XMLFinder import XMLFinder
from helpers import *

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
        dataset_urn = make_dataset_urn("geoserver", dataset_id, "PROD")

        # Emitir propiedades básicas (title, abstract)...
        # ...

        # Obtener XML
        csw.getrecordbyid(id=[record.identifier], outputschema="http://www.isotc211.org/2005/gmd")
        xml_raw = csw.response
        if isinstance(xml_raw, str):
            xml_raw = xml_raw.encode("utf-8")
        tree = etree.fromstring(xml_raw)

        # 1) Extraer propiedades simples (id, date, language, type...)
        finder = XMLFinder(tree, ns)

        # recorrer todas las propiedades declaradas
        for prop_name, config in PROPERTIES_TO_EXTRACT.items():
            value = None
            for xp in config["xpaths"]:
                el = tree.find(xp, namespaces=ns)
                if el is not None:
                    # casos especiales: algunos valores vienen como atributo
                    if xp.endswith("LanguageCode") or xp.endswith("MD_ScopeCode"):
                        val = el.get("codeListValue")
                    else:
                        val = el.text
                    if val:
                        value = val.strip()
                        break
            if value:
                emit_structured_property(dataset_urn, config["urn"], value, emitter)
            else:
                print(f"⚠ No se encontró {prop_name} en {dataset_id}")

        # 2) Extraer bbox
        #extract_and_emit_bbox(tree, ns, dataset_urn, emitter)
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

        bbox_urn="urn:li:structuredProperty:boundingbox"
        if bbox_values:
            emit_structured_property(dataset_urn, bbox_urn, bbox_values, emitter)
        else:
            print(f"⚠ No se encontró bbox en {dataset_id}")

        # 3) Ownership
        #extract_and_emit_ownership(tree, ns, dataset_urn, emitter)
        orgs = [
            el.text.strip()
            for el in tree.findall(
                ".//gmd:pointOfContact//gmd:organisationName//gco:CharacterString", ns
            )
            if el.text
        ]
        for org in orgs:
            org_name = org
            group_urn= group_urn = f"urn:li:corpGroup:{org_name.replace(' ', '_')}"
            create_new_corpgroup(org_name, group_urn, emitter)
            set_ownership(group_urn, dataset_urn, emitter)


        # 4) Rights
        #extract_and_emit_rights(tree, ns, dataset_urn, emitter)
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

        if rights_values:
            rights_urn = "urn:li:structuredProperty:rights"
            emit_structured_property(dataset_urn, rights_urn, rights_values, emitter)
        else:
            print(f"⚠ No se encontraron derechos en {dataset_id}")

        # 5) Tags
        #extract_and_emit_tags(tree, ns, dataset_urn, emitter)
        tags = [
            el.text.strip()
            for el in tree.findall(".//gmd:keyword/gco:CharacterString", ns)
            if el.text
        ]
        for tag in tags:
            create_new_tag(tag, emitter)

        if tags:
            # Convertir los tags a URNs
            tag_associations = [TagAssociationClass(tag=builder.make_tag_urn(t.replace(" ", "_"))) for t in tags]
            emit_tags(dataset_urn, tag_associations, emitter)
        else:
            print(f"⚠ No se encontraron tags en {dataset_id}")

        # 6) URLs
        #extract_and_emit_urls(csw, dataset_id, dataset_urn, emitter)
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
            url_urn = "urn:li:structuredProperty:c4fe8236-87ff-4310-ac79-6468b4633634"
            emit_structured_property(dataset_urn, url_urn, urls_list, emitter)
        else:
            print("No se encontró ninguna URL en el XML.")


    start += pagesize
    if start >= csw.results.get('matches', 0):
        break

print("✅ Todos los datasets enviados con ID, BoundingBox y DataProduct.")
