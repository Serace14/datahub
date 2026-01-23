import datahub.emitter.mce_builder as builder
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
    OwnershipClass,
    OwnerClass,
    OwnershipTypeClass,
    CorpGroupInfoClass,
)
from datahub.emitter.rest_emitter import DatahubRestEmitter
from owslib.csw import CatalogueServiceWeb
from lxml import etree

# ========================
# Conexión al servidor de DataHub
# ========================
emitter = DatahubRestEmitter(
    gms_server="http://localhost:8080",
    token="eyJhbGciOiJIUzI1NiJ9.eyJhY3RvclR5cGUiOiJVU0VSIiwiYWN0b3JJZCI6ImRhdGFodWIiLCJ0eXBlIjoiUEVSU09OQUwiLCJ2ZXJzaW9uIjoiMiIsImp0aSI6ImQyNDU4YTRkLTc2YTYtNDQ4My1iNWYyLTA2MDRiMjZiYmE4NiIsInN1YiI6ImRhdGFodWIiLCJleHAiOjE3NTU2ODA3NzksImlzcyI6ImRhdGFodWItbWV0YWRhdGEtc2VydmljZSJ9.pO264G1P2YRwLdIumiiT5s49wY7tmD0MLSpKHNaCOH8"  # <-- tu token
)
emitter.test_connection()

# ========================
# Conexión al CSW y obtención de metadato
# ========================
csw = CatalogueServiceWeb("https://www.idee.es/csw-inspire-idee/srv/spa/csw")

record_id = "ef7d1ebc-be18-4cb0-af55-17a3cb509434"
csw.getrecordbyid(id=[record_id], outputschema="http://www.isotc211.org/2005/gmd")

xml_raw = csw.response
if isinstance(xml_raw, str):
    xml_raw = xml_raw.encode("utf-8")
tree = etree.fromstring(xml_raw)

# ========================
# Extracción de tags
# ========================
ns = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
}

tags = [
    el.text.strip()
    for el in tree.findall(".//gmd:keyword/gco:CharacterString", ns)
    if el.text
]
print("Tags extraídos:", tags)

# ========================
# Extracción de ownership (organisationName)
# ========================
orgs = [
    el.text.strip()
    for el in tree.findall(".//gmd:pointOfContact//gmd:organisationName//gco:CharacterString", ns)
    if el.text
]

ownership_aspect = None
if orgs:
    org_name = orgs[0]  # cogemos el primero
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

    # Construir el ownership
    ownership_aspect = OwnershipClass(
        owners=[
            OwnerClass(
                owner=group_urn,
                type=OwnershipTypeClass.TECHNICAL_OWNER,  # según tabla: creator/publisher
            )
        ]
    )

# ========================
# Construcción del objeto DatasetPropertiesClass
# ========================
dataset_properties = DatasetPropertiesClass(
    name="DATASET Protection areas of birds against collision and electrocution",
    description="Cartography of the areas where aerial wiring is required to have special isolation or increase visibility measures to avoid electrocution and collision, in accordance with the technical specifications of RC 1432/2008 .",
    tags=tags,
)

# ========================
# Crear el URN
# ========================
dataset_urn = builder.make_dataset_urn(
    platform="geoserver",
    name=record_id,
    env="PROD",
)

# ========================
# Enviar evento DatasetProperties
# ========================
emitter.emit(
    MetadataChangeProposalWrapper(entityUrn=dataset_urn, aspect=dataset_properties)
)
print(f"Dataset insertado con URN: {dataset_urn}")

# ========================
# Enviar evento Ownership
# ========================
if ownership_aspect:
    emitter.emit(
        MetadataChangeProposalWrapper(entityUrn=dataset_urn, aspect=ownership_aspect)
    )
    print(f"Ownership asociado a {dataset_urn}: {orgs[0]}")
