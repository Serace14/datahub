from datahub.emitter.mce_builder import make_dataset_urn
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.specific.dataset import DatasetPatchBuilder
# Conexión a DataHub
emitter = DatahubRestEmitter(
    gms_server="http://localhost:8080",
    token="eyJhbGciOiJIUzI1NiJ9.eyJhY3RvclR5cGUiOiJVU0VSIiwiYWN0b3JJZCI6ImRhdGFodWIiLCJ0eXBlIjoiUEVSU09OQUwiLCJ2ZXJzaW9uIjoiMiIsImp0aSI6ImQyNDU4YTRkLTc2YTYtNDQ4My1iNWYyLTA2MDRiMjZiYmE4NiIsInN1YiI6ImRhdGFodWIiLCJleHAiOjE3NTU2ODA3NzksImlzcyI6ImRhdGFodWItbWV0YWRhdGEtc2VydmljZSJ9.pO264G1P2YRwLdIumiiT5s49wY7tmD0MLSpKHNaCOH8"
)
# URN del dataset
dataset_urn = make_dataset_urn(
    platform="geoserver",
    name="ef7d1ebc-be18-4cb0-af55-17a3cb509434",
    env="PROD"
)
# Crear el patch para la structured property
patch_builder = DatasetPatchBuilder(dataset_urn)
patch_builder.set_structured_property("date", date_value)
patch_mcps = patch_builder.build()
# Emitir el patch
for patch_mcp in patch_mcps:
    emitter.emit(patch_mcp)
    print(f"Structured property 'date' actualizada para (dataset_urn): {date_value}")