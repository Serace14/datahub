import requests
from owslib.csw import CatalogueServiceWeb
from lxml import etree
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import PlatformResourceInfoClass
from associate_platform_resource_to_catalogrecord import associate_platform_resource_to_catalogrecord

# === Configuración ===
GMS_SERVER = "http://localhost:8080"
TOKEN = "eyJhbGciOiJIUzI1NiJ9..."  # <-- tu token DataHub
CSW_URL = "https://www.idee.es/csw-codsi-idee/srv/spa/csw"

# === Inicializar DataHub emitter ===
emitter = DatahubRestEmitter(gms_server=GMS_SERVER, token=TOKEN)
emitter.test_connection()

# === Conectar al CSW ===
csw = CatalogueServiceWeb(CSW_URL)

# === Namespaces ===
ns = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
    "dc": "http://purl.org/dc/elements/1.1/",
}

# === Función auxiliar ===
def extract_text(tree, xpath_list):
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


# === Iteración paginada del CSW ===
start = 0
pagesize = 50

while True:
    csw.getrecords2(startposition=start + 1, maxrecords=pagesize, esn='full')

    if not csw.records:
        break

    for rec_id, record in csw.records.items():
        rec_identifier = record.identifier
        print(f"\n📄 Procesando registro: {rec_identifier}")

        # === Descargar el XML ISO del registro ===
        csw.getrecordbyid(id=[rec_identifier], outputschema="http://www.isotc211.org/2005/gmd")
        xml_raw = csw.response

        if isinstance(xml_raw, str):
            xml_raw = xml_raw.encode("utf-8")

        xml_text = xml_raw.decode("utf-8")
        tree = etree.fromstring(xml_raw)

        # === Extraer campos igual que tu código ===
        id_value = extract_text(tree, [
            "//dc:identifier",
            "//gmd:fileIdentifier/gco:CharacterString"
        ])

        date_value = extract_text(tree, [
            "//gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='creation']/gmd:date/gco:Date",
            "//gmd:dateStamp/gco:Date"
        ])

        status_nodes = tree.xpath("//*[local-name()='status']/*[local-name()='MD_ProgressCode']")
        status_value = status_nodes[0].get("codeListValue").strip() if status_nodes else None

        language_value = extract_text(tree, [
            "//gmd:language/gmd:LanguageCode/@codeListValue",
            "//gmd:language/gmd:LanguageCode/text()"
        ])

        print(f"ID: {id_value}")
        print(f"Date: {date_value}")
        print(f"Status: {status_value}")
        print(f"Language: {language_value}")

        # === Crear URN ===
        URN = f"urn:li:platformResource:geoserver-{id_value}"
        print(f"URN: {URN}")

        # === Crear y emitir PlatformResourceInfo ===
        platform_resource_info = PlatformResourceInfoClass(
            resourceType="metadata",
            primaryKey=id_value,
            secondaryKeys=[v for v in [date_value, language_value, status_value] if v],
            value=None,
            xmlText=xml_text,
        )

        emitter.emit(MetadataChangeProposalWrapper(entityUrn=URN, aspect=platform_resource_info))
        print("✅ PlatformResourceInfo emitido")

        associate_platform_resource_to_catalogrecord(GMS_SERVER, TOKEN, URN)

    start += pagesize
    if start >= csw.results.get('matches', 0):
        break

print("\n🎉 INGESTA COMPLETA DE TODOS LOS REGISTROS CSW")
