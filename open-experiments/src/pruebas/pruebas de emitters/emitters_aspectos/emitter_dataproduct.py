import datahub.emitter.mce_builder as builder
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import (
    DataProductPropertiesClass,
    DataProductAssociationClass,
)
from owslib.csw import CatalogueServiceWeb
from lxml import etree
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

dataproduct_name = "CSW"

# ========================
# Crear DataProduct si no existe
# ========================
dataproduct_urn = f"urn:li:dataProduct:{dataproduct_name}"
# URN del dataset
dataset_urn = builder.make_dataset_urn(
    platform="geoserver",
    name=record_id,
    env="PROD"
)
# Definición del DataProduct con el dataset como asset
dp_properties = DataProductPropertiesClass(
    name=dataproduct_name,
    description=f"DataProduct generado automáticamente a partir del dataset {record_id}",
    assets=[
        DataProductAssociationClass(destinationUrn=dataset_urn)
    ]
)
mcp = MetadataChangeProposalWrapper(
    entityUrn=dataproduct_urn,
    aspect=dp_properties,
)
emitter.emit(mcp)
print(f"DataProduct creado o actualizado: {dataproduct_urn} y asociado el dataset {dataset_urn}")