from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.ingestion.graph.client import DataHubGraph
from datahub.ingestion.graph.config import DatahubClientConfig
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
    StructuredPropertiesClass,
)
from datahub.emitter.mce_builder import make_dataset_urn
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.specific.dataset import DatasetPatchBuilder
from datahub.metadata.schema_classes import PlatformResourceInfoClass
from lxml import etree
import random

# === CONFIGURACIÓN ===
GMS_SERVER = "http://localhost:8080"
TOKEN = "eyJhbGciOiJIUzI1NiJ9..."  # tu token válido
CATALOG_RECORD_URN = "urn:li:catalogRecord:(urn:li:dataPlatform:geoserver,7eea5c42-212f-4099-b9df-1e3703fbc616,PROD)"

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


# === 1. Conectar con DataHub ===
graph = DataHubGraph(DatahubClientConfig(server=GMS_SERVER))
emitter = DatahubRestEmitter(gms_server=GMS_SERVER, token=TOKEN)
emitter.test_connection()
print("✅ Conexión a DataHub establecida correctamente.")

# === 2. Obtener el PlatformResource asociado al CatalogRecord ===
print(f"🔍 Buscando PlatformResource asociado a {CATALOG_RECORD_URN}")
query = """
query getCatalogWithRelationships($urn: String!) {
  catalogRecord(urn: $urn) {
    urn
    relationships(input: {types: ["AssociatedWith"], direction: OUTGOING}) {
      relationships {
        entity {
          urn
        }
        type
      }
    }
  }
}
"""

res = graph.execute_graphql(query, {"urn": CATALOG_RECORD_URN})

# Depuración: ver la respuesta completa
print("\n=== GraphQL Response ===")
print(res)

# Validar que haya datos válidos
if not res or not res.get("catalogRecord"):
    raise ValueError(f"❌ No se encontró el CatalogRecord {CATALOG_RECORD_URN} o la respuesta es inválida: {res}")

relationships = res["catalogRecord"].get("relationships", {}).get("relationships", [])
if not relationships:
    raise ValueError(f"❌ No se encontró relación 'AssociatedWith' para {CATALOG_RECORD_URN}")

# Tomar el primer PlatformResource relacionado
platform_urn = relationships[0]["entity"]["urn"]
print(f"✅ CatalogRecord asociado con PlatformResource: {platform_urn}")

# === 3. Obtener xmlText del PlatformResource ===
aspect_info: PlatformResourceInfoClass = graph.get_aspect(platform_urn, PlatformResourceInfoClass)
if not aspect_info or not getattr(aspect_info, "xmlText", None):
    raise ValueError(f"❌ No se pudo recuperar xmlText de {platform_urn}")

xml_text = aspect_info.xmlText
print(f"📦 xmlText recuperado ({len(xml_text)} bytes).")

# === 4. Parsear el XML y extraer metadatos ===
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
    title = f"dataset-{random.randint(1000, 9999)}"

print(f"📄 Campos extraídos:")
print(f"   • title: {title}")
print(f"   • description: {description or '(sin descripción)'}")
print(f"   • language: {language or '(sin idioma)'}")

# === 5. Crear el Dataset ===

# Obtener el primaryKey del PlatformResource
primary_key = getattr(aspect_info, "primaryKey", None)

# Intentar extraer identificador desde el XML si no hay primaryKey
identifier = extract_text(tree, ns, [
    "//dc:identifier",
    "//gmd:fileIdentifier/gco:CharacterString",
])

# Prioridad: primaryKey > dc:identifier > gmd:fileIdentifier > title
dataset_id = (primary_key or identifier or title).replace(" ", "_").lower()

dataset_urn = make_dataset_urn(platform="geoserver", name=dataset_id, env="PROD")

dataset_props = DatasetPropertiesClass(
    name=title,
    description=description or "Dataset derivado de CatalogRecord",
)

emitter.emit(
    MetadataChangeProposalWrapper(
        entityUrn=dataset_urn,
        aspect=dataset_props,
    )
)
print(f"✅ Dataset creado con URN: {dataset_urn}")

# === 6. Asociar el Dataset con el CatalogRecord mediante StructuredProperty ===
patch_builder = DatasetPatchBuilder(dataset_urn)
patch_builder.set_structured_property(
    "urn:li:structuredProperty:catalog",  # tu StructuredProperty para la asociación
    CATALOG_RECORD_URN
)

# También puedes incluir el lenguaje extraído como structured property adicional
if language:
    patch_builder.set_structured_property(
        "urn:li:structuredProperty:language",
        language
    )

for patch_mcp in patch_builder.build():
    emitter.emit(patch_mcp)

print(f"🔗 Dataset asociado correctamente con CatalogRecord mediante 'CatalogAsociado'.")

emitter.close()
print("🎉 Ingesta de Dataset completada exitosamente.")
