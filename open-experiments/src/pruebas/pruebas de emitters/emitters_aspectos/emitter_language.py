import datahub.emitter.mce_builder as builder
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import GenericAspectClass
from owslib.csw import CatalogueServiceWeb
from lxml import etree
from datahub.emitter.mce_builder import make_dataset_urn
from datahub.specific.dataset import DatasetPatchBuilder

# ========================
# Conexión a DataHub
# ========================
emitter = DatahubRestEmitter(
    gms_server="http://localhost:8080",
    token="eyJhbGciOiJIUzI1NiJ9.eyJhY3RvclR5cGUiOiJVU0VSIiwiYWN0b3JJZCI6ImRhdGFodWIiLCJ0eXBlIjoiUEVSU09OQUwiLCJ2ZXJzaW9uIjoiMiIsImp0aSI6ImJjYzI0YTMwLThiZTUtNGNhMy04MzQ5LTEzYTU0MzJiODE5ZCIsInN1YiI6ImRhdGFodWIiLCJleHAiOjE3NjM0NjA2NTgsImlzcyI6ImRhdGFodWItbWV0YWRhdGEtc2VydmljZSJ9.5S4rfT3P7jdFAutiT5VlqcaOWpyibr7sxc1dD2_7BNw"
)
emitter.test_connection()

# ========================
# Conexión al CSW y obtención del XML
# ========================
csw = CatalogueServiceWeb("https://www.idee.es/csw-inspire-idee/srv/spa/csw")
record_id = "ef7d1ebc-be18-4cb0-af55-17a3cb509434"
csw.getrecordbyid(id=[record_id], outputschema="http://www.isotc211.org/2005/gmd")
xml_raw = csw.response
if isinstance(xml_raw, str):
    xml_raw = xml_raw.encode("utf-8")
tree = etree.fromstring(xml_raw)

# ========================
# Namespaces
# ========================
ns = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
    "dc": "http://purl.org/dc/elements/1.1/",
}

# ========================
# Extracción del lenguaje
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

# ========================
# Asignar el ID al dataset usando GenericAspect
# ========================
if language_value:
    # URN del dataset
    dataset_urn = make_dataset_urn(
        platform="geoserver",
        name=record_id,
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
