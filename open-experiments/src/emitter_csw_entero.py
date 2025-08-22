from owslib.csw import CatalogueServiceWeb
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.emitter.mce_builder import make_dataset_urn
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import DatasetPropertiesClass

# === Configuración DataHub ===
emitter = DatahubRestEmitter(
    gms_server="http://localhost:8080",  # Cambia si tu DataHub está en otra URL
    token="eyJhbGciOiJIUzI1NiJ9.eyJhY3RvclR5cGUiOiJVU0VSIiwiYWN0b3JJZCI6ImRhdGFodWIiLCJ0eXBlIjoiUEVSU09OQUwiLCJ2ZXJzaW9uIjoiMiIsImp0aSI6ImQyNDU4YTRkLTc2YTYtNDQ4My1iNWYyLTA2MDRiMjZiYmE4NiIsInN1YiI6ImRhdGFodWIiLCJleHAiOjE3NTU2ODA3NzksImlzcyI6ImRhdGFodWItbWV0YWRhdGEtc2VydmljZSJ9.pO264G1P2YRwLdIumiiT5s49wY7tmD0MLSpKHNaCOH8"  # Pon tu token si usas auth
)
emitter.test_connection()

# === Conexión al CSW ===
csw = CatalogueServiceWeb('https://www.mapama.gob.es/ide/metadatos/srv/spa/csw')

start = 0
pagesize = 50  # Número de registros por petición

while True:
    # Obtener un lote de registros
    csw.getrecords2(startposition=start + 1, maxrecords=pagesize, esn='full')

    if not csw.records:
        break

    for rec_id, record in csw.records.items():
        dataset_id = record.identifier or f"csw-{rec_id}"
        title = record.title or "Sin título"
        abstract = record.abstract or "Sin descripción"
        keywords = record.subjects or []
        date = record.date or "N/A"
        formato = record.format or "N/A"
        tipo = record.type or "N/A"
        uri = record.source or None
        lenguaje = record.language or None
        bbox = record.bbox or None
        proveedor = record.creator or None
        organizacion = record.publisher or None
        acceso = record.references or []

        # Crear URN
        dataset_urn = make_dataset_urn(
            platform="geoserver",  # También puedes usar "geoserver" si prefieres
            name=dataset_id,
            env="PROD"
        )

        # Crear propiedades del dataset
        dataset_properties = DatasetPropertiesClass(
            name=title,
            description=abstract,
            customProperties={
                "keywords": ", ".join(keywords) if isinstance(keywords, list) else str(keywords),
                "date": str(date),
                "format": str(formato),
                "type": str(tipo),
                "uri": str(uri),
                "language": str(lenguaje),
                "bbox": str(bbox),
                "provider": str(proveedor),
                "organization": str(organizacion),
                "access": str(acceso)
            }
        )

        # Empaquetar evento
        metadata_event = MetadataChangeProposalWrapper(
            entityUrn=dataset_urn,
            aspect=dataset_properties
        )

        # Emitir a DataHub
        emitter.emit(metadata_event)
        print(f"Dataset enviado: {title}")

    # Pasar a la siguiente página
    start += pagesize
    if start >= csw.results.get('matches', 0):
        break

print("Todos los datasets del CSW han sido enviados a DataHub.")
