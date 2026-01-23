import datahub.emitter.mce_builder as builder
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import DatasetPropertiesClass, TagPropertiesClass, GlobalTagsClass, TagAssociationClass
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
# Extracción de tags (keywords)
# ========================
tags = [
    el.text.strip()
    for el in tree.findall(".//gmd:keyword/gco:CharacterString", ns)
    if el.text
]
print("Tags extraídos:", tags)

# ========================
# Ingesta de tags en DataHub
# ========================
for tag in tags:
    tag_urn = builder.make_tag_urn(tag.replace(" ", "_"))
    tag_aspect = TagPropertiesClass(
        name=tag,
        description=f"Tag importado desde CSW: {tag}"
    )
    emitter.emit(MetadataChangeProposalWrapper(entityUrn=tag_urn, aspect=tag_aspect))
    print(f"Tag creado/actualizado: {tag_urn}")

# ========================
# Asignar tags a un dataset ya creado
# ========================
if tags:
    # Convertir los tags a URNs
    tag_associations = [TagAssociationClass(tag=builder.make_tag_urn(t.replace(" ", "_"))) for t in tags]

    # URN del dataset existente
    dataset_urn = builder.make_dataset_urn(
        platform="geoserver",
        name=record_id,
        env="PROD",
    )

    # Crear la propuesta de cambio solo para GlobalTags
    dataset_tags_mcp = MetadataChangeProposalWrapper(
        entityUrn=dataset_urn,
        aspect=GlobalTagsClass(tags=tag_associations)
    )

    emitter.emit(dataset_tags_mcp)
    print(f"Tags asignados al dataset existente {dataset_urn}: {tags}")
else:
    print("No se encontraron tags en el XML.")
