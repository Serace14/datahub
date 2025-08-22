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
# Extracción de rights (CSW y GMD) incluyendo todas las restricciones legales
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


# ========================
# Asignar las rights al dataset usando GenericAspect
# ========================
if rights_values:
    dataset_urn = make_dataset_urn(
        platform="geoserver",
        name=record_id,
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
