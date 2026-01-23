from lxml import etree
import random
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.ingestion.graph.client import DataHubGraph
from datahub.ingestion.graph.config import DatahubClientConfig
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
    PlatformResourcesClass,
    PlatformResourceInfoClass,
)

# === CONFIGURACIÓN ===
GMS_SERVER = "http://localhost:8080"
TOKEN = "eyJhbGciOiJIUzI1NiJ9..."  # tu token válido
PLATFORM_RESOURCE_URN = "urn:li:platformResource:geoserver-7eea5c42-212f-4099-b9df-1e3703fbc616"

# === FUNCIONES AUXILIARES ===
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


# === 1. Conectar con DataHub y recuperar PlatformResourceInfo ===
print(f"🔍 Recuperando aspecto PlatformResourceInfo de {PLATFORM_RESOURCE_URN}")
graph = DataHubGraph(DatahubClientConfig(server=GMS_SERVER))
aspect_info: PlatformResourceInfoClass = graph.get_aspect(PLATFORM_RESOURCE_URN, PlatformResourceInfoClass)

if not aspect_info or not getattr(aspect_info, "xmlText", None):
    raise ValueError(f"❌ No se pudo recuperar xmlText del PlatformResource {PLATFORM_RESOURCE_URN}")

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
association_aspect = PlatformResourcesClass(resources=[PLATFORM_RESOURCE_URN])
emitter.emit(
    MetadataChangeProposalWrapper(
        entityUrn=catalog_urn,
        aspect=association_aspect,
    )
)
print(f"🔗 Relación establecida entre {catalog_urn} y {PLATFORM_RESOURCE_URN}")

emitter.close()
print("🎉 Ingesta y relación completadas exitosamente.")
