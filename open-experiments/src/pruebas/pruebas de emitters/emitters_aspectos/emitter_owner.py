import datahub.emitter.mce_builder as builder
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import (
    OwnershipClass,
    OwnerClass,
    OwnershipTypeClass,
    CorpGroupInfoClass,
)
from datahub.emitter.rest_emitter import DatahubRestEmitter
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

# ========================
# Namespaces
# ========================
ns = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
}

# ========================
# Extracción de ownership (organisationName)
# ========================
orgs = [
    el.text.strip()
    for el in tree.findall(
        ".//gmd:pointOfContact//gmd:organisationName//gco:CharacterString", ns
    )
    if el.text
]

if orgs:
    org_name = orgs[0]
    group_urn = f"urn:li:corpGroup:{org_name.replace(' ', '_')}"

    # Emitir el corpGroup
    corpgroup_info = CorpGroupInfoClass(
        displayName=org_name,
        description=f"Organisation from CSW metadata: {org_name}",
        admins=[],
        members=[],
        groups=[]
    )
    emitter.emit(
        MetadataChangeProposalWrapper(entityUrn=group_urn, aspect=corpgroup_info)
    )
    print(f"CorpGroup emitido: {group_urn}")

    # Construcción del Ownership
    ownership_aspect = OwnershipClass(
        owners=[
            OwnerClass(
                owner=group_urn,
                type=OwnershipTypeClass.TECHNICAL_OWNER,  # puedes ajustar el tipo
            )
        ]
    )

    # URN del dataset (ejemplo)
    dataset_urn = builder.make_dataset_urn(
        platform="geoserver",
        name=record_id,
        env="PROD",
    )

    # Emitir ownership al dataset
    emitter.emit(
        MetadataChangeProposalWrapper(entityUrn=dataset_urn, aspect=ownership_aspect)
    )
    print(f"Ownership asociado a {dataset_urn}: {org_name}")
else:
    print("No se encontró organisationName en el XML.")
