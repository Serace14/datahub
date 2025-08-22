import datahub.emitter.mce_builder as builder
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import DatasetPropertiesClass
from datahub.emitter.rest_emitter import DatahubRestEmitter

# Conexión al servidor de DataHub
emitter = DatahubRestEmitter(
    gms_server="http://localhost:8080",
    token="eyJhbGciOiJIUzI1NiJ9.eyJhY3RvclR5cGUiOiJVU0VSIiwiYWN0b3JJZCI6ImRhdGFodWIiLCJ0eXBlIjoiUEVSU09OQUwiLCJ2ZXJzaW9uIjoiMiIsImp0aSI6ImQyNDU4YTRkLTc2YTYtNDQ4My1iNWYyLTA2MDRiMjZiYmE4NiIsInN1YiI6ImRhdGFodWIiLCJleHAiOjE3NTU2ODA3NzksImlzcyI6ImRhdGFodWItbWV0YWRhdGEtc2VydmljZSJ9.pO264G1P2YRwLdIumiiT5s49wY7tmD0MLSpKHNaCOH8"
)

# Verificar conexión
emitter.test_connection()

# Construcción del objeto con propiedades del dataset
dataset_properties = DatasetPropertiesClass(
    name="DATASET Natura 2000 Balearic Islands",
    description=(
        "Xarxa Natura 2000 ecological protection network at the level of regional "
        "management and state management. Delimitation of areas declared as Sites "
        "of Community Importance (LIC), Special Bird Protection Areas (ZEPA) and "
        "Special Conservation Areas (ZEC). The areas of the different protection "
        "sites may overlap."
    ),
    customProperties={
        "id": "A5C3E8E6-6451-4453-960C-CA82B953E83E",
        "keywords": "Protected sites, environment"
    }
)

# Crear el URN usando datasetKey
dataset_urn = builder.make_dataset_urn(
    platform="geoserver",  # puedes cambiar la plataforma si no es BigQuery
    name="A5C3E8E6-6451-4453-960C-CA82B953E83E",
    env="PROD"
)

# Construcción del evento de cambio de metadatos
metadata_event = MetadataChangeProposalWrapper(
    entityUrn=dataset_urn,
    aspect=dataset_properties
)

# Enviar el dataset a DataHub
emitter.emit(metadata_event)

print(f"Dataset insertado con URN: {dataset_urn}")
