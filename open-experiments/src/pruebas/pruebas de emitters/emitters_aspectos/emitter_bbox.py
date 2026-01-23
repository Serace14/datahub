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
# Conexión al CSW y obtención del XML desde record.xml
# ========================
csw = CatalogueServiceWeb("https://www.idee.es/csw-inspire-idee/srv/spa/csw")
record_id = "ef7d1ebc-be18-4cb0-af55-17a3cb509434"
csw.getrecordbyid(id=[record_id], outputschema="http://www.isotc211.org/2005/gmd")

# Tomamos el primer registro
record = list(csw.records.values())[0]
xml_bytes = record.xml
root = etree.fromstring(xml_bytes)

# ========================
# Namespaces para OWS e ISO
# ========================
ns_ows = {
    "ows": "http://www.opengis.net/ows"
}

ns_iso = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco"
}

# ========================
# Extracción del BoundingBox
# ========================
bbox_values = []

# Primero intentamos OWS
bbox_el = root.find(".//ows:BoundingBox", ns_ows)
if bbox_el is not None:
    lower = bbox_el.find("ows:LowerCorner", ns_ows)
    upper = bbox_el.find("ows:UpperCorner", ns_ows)
    if lower is not None and upper is not None:
        lower_coords = lower.text.strip().split()
        upper_coords = upper.text.strip().split()
        bbox_values = lower_coords + upper_coords

# Si no hay OWS, intentamos ISO
if not bbox_values:
    bbox_el = root.find(".//gmd:EX_GeographicBoundingBox", ns_iso)
    if bbox_el is not None:
        west = bbox_el.find("gmd:westBoundLongitude/gco:Decimal", ns_iso)
        east = bbox_el.find("gmd:eastBoundLongitude/gco:Decimal", ns_iso)
        south = bbox_el.find("gmd:southBoundLatitude/gco:Decimal", ns_iso)
        north = bbox_el.find("gmd:northBoundLatitude/gco:Decimal", ns_iso)
        if west is not None and east is not None and south is not None and north is not None:
            bbox_values = [west.text, south.text, east.text, north.text]

print("BoundingBox extraído:", bbox_values)

# ========================
# Asignar el BoundingBox al dataset usando GenericAspect
# ========================
if bbox_values:
    dataset_urn = make_dataset_urn(
        platform="geoserver",
        name=record_id,
        env="PROD"
    )

    patch_builder = DatasetPatchBuilder(dataset_urn)
    patch_builder.set_structured_property(
        "urn:li:structuredProperty:boundingbox",
        bbox_values
    )
    patch_mcps = patch_builder.build()

    for patch_mcp in patch_mcps:
        emitter.emit(patch_mcp)

    print(f"Structured property 'bbox' actualizada para ({dataset_urn}) {bbox_values}")
else:
    print("No se encontró ningún bbox en el XML.")
