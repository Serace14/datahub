import datahub.emitter.mce_builder as builder
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
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
# Conexión al CSW
# ========================
csw = CatalogueServiceWeb("https://www.idee.es/csw-inspire-idee/srv/spa/csw")
record_id = "ef7d1ebc-be18-4cb0-af55-17a3cb509434"

urls = set()

# ========================
# Extracción desde CSW (dc:*)
# ========================
csw.getrecordbyid(id=[record_id], outputschema="http://www.opengis.net/cat/csw/2.0.2")
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
csw.getrecordbyid(id=[record_id], outputschema="http://www.isotc211.org/2005/gmd")
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
for el in tree_gmd.findall(".//gmd:distributionInfo//gmd:MD_DigitalTransferOptions//gmd:onLine//gmd:URL", ns_gmd):
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
        name=record_id,
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
