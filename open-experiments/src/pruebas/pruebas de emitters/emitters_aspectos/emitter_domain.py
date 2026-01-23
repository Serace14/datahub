import datahub.emitter.mce_builder as builder
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import DomainPropertiesClass, DomainsClass
from datahub.emitter.rest_emitter import DatahubRestEmitter

# ========================
# Conexión a DataHub
# ========================
emitter = DatahubRestEmitter(
    gms_server="http://localhost:8080",
    token="eyJhbGciOiJIUzI1NiJ9.eyJhY3RvclR5cGUiOiJVU0VSIiwiYWN0b3JJZCI6ImRhdGFodWIiLCJ0eXBlIjoiUEVSU09OQUwiLCJ2ZXJzaW9uIjoiMiIsImp0aSI6ImJjYzI0YTMwLThiZTUtNGNhMy04MzQ5LTEzYTU0MzJiODE5ZCIsInN1YiI6ImRhdGFodWIiLCJleHAiOjE3NjM0NjA2NTgsImlzcyI6ImRhdGFodWItbWV0YWRhdGEtc2VydmljZSJ9.5S4rfT3P7jdFAutiT5VlqcaOWpyibr7sxc1dD2_7BNw"
)
emitter.test_connection()

# ========================
# URN del dataset existente
# ========================
record_id = "ef7d1ebc-be18-4cb0-af55-17a3cb509434"
dataset_urn = builder.make_dataset_urn(
    platform="geoserver",
    name=record_id,
    env="PROD",
)

# ========================
# Definir el dominio
# ========================
domain_name = "Datos_Espaciales"
domain_description = "Dominio general para datasets espaciales importados desde CSW"
domain_urn = builder.make_domain_urn(domain_name)

# ========================
# Crear/actualizar el dominio
# ========================
domain_aspect = DomainPropertiesClass(
    name=domain_name,
    description=domain_description
)
emitter.emit(MetadataChangeProposalWrapper(entityUrn=domain_urn, aspect=domain_aspect))
print(f"Dominio creado/actualizado: {domain_urn}")

# ========================
# Asignar el dominio al dataset
# ========================
domains_aspect = DomainsClass(domains=[domain_urn])
dataset_domain_mcp = MetadataChangeProposalWrapper(
    entityUrn=dataset_urn,
    aspect=domains_aspect
)
emitter.emit(dataset_domain_mcp)
print(f"Dominio asignado al dataset (dataset_urn): {domain_name}")
