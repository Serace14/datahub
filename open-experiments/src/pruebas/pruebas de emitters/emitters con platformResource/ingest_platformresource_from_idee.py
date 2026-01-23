import requests
from lxml import etree
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import PlatformResourceInfoClass

# === Configuración ===
GMS_SERVER = "http://localhost:8080"
TOKEN = "eyJhbGciOiJIUzI1NiJ9..."  # <-- tu token DataHub
IDE_URL = "https://www.idee.es/csw-codsi-idee/srv/api/records/7eea5c42-212f-4099-b9df-1e3703fbc616/formatters/xml"

# === Inicializar emisor ===
emitter = DatahubRestEmitter(gms_server=GMS_SERVER, token=TOKEN)
emitter.test_connection()

# === Descargar XML ===
response = requests.get(IDE_URL)
xml_text = response.text
tree = etree.fromstring(xml_text.encode("utf-8"))

# === Namespaces ===
ns = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
    "dc": "http://purl.org/dc/elements/1.1/",
}

# === Función auxiliar para extracción con XPath ===
def extract_text(xpath_list):
    """Devuelve el primer valor textual o atributo encontrado en las rutas dadas."""
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


# === Extracción de campos ===
id_value = extract_text([
    "//dc:identifier",
    "//gmd:fileIdentifier/gco:CharacterString"
])

date_value = extract_text([
    "//gmd:CI_Date[gmd:dateType/gmd:CI_DateTypeCode/@codeListValue='creation']/gmd:date/gco:Date",
    "//gmd:dateStamp/gco:Date"
])

status_nodes = tree.xpath("//*[local-name()='status']/*[local-name()='MD_ProgressCode']")
status_value = status_nodes[0].get("codeListValue").strip() if status_nodes else None

language_value = extract_text([
    "//gmd:language/gmd:LanguageCode/@codeListValue",
    "//gmd:language/gmd:LanguageCode/text()"
])

# === Mensajes de diagnóstico ===
print(f"ID: {id_value or '⚠️ No encontrado'}")
print(f"Date: {date_value or '⚠️ No encontrado'}")
print(f"Status: {status_value or '⚠️ No encontrado'}")
print(f"Language: {language_value or '⚠️ No encontrado'}")

# === Crear URN válido para platformResource ===
URN = f"urn:li:platformResource:geoserver-{id_value}"
print(f"URN: {URN}")

# === Emitir PlatformResourceInfo con xmlText ===
platform_resource_info = PlatformResourceInfoClass(
    resourceType="metadata",
    primaryKey=id_value,
    secondaryKeys=[v for v in [date_value, language_value, status_value] if v],
    value=None,
    xmlText=xml_text,
)

emitter.emit(MetadataChangeProposalWrapper(entityUrn=URN, aspect=platform_resource_info))
print("✅ Aspecto PlatformResourceInfo emitido con xmlText")
