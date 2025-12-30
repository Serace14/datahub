import os
from datahub.emitter.mce_builder import make_term_urn
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import GlossaryTermInfoClass

# Configura la conexión a DataHub
gms_server = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080")
token = os.getenv("DATAHUB_GMS_TOKEN")  # Opcional, si usas autenticación

# Crea el URN del término de glosario
term_urn = make_term_urn("CustomerLifetimeValue")

# Define la información principal del término
term_info = GlossaryTermInfoClass(
    name="Customer Lifetime Value",
    definition="El ingreso total que se espera de una cuenta de cliente durante toda la relación comercial.",
    termSource="INTERNAL",
)

# Crea el evento de cambio de metadatos
event = MetadataChangeProposalWrapper(
    entityUrn=term_urn,
    aspect=term_info,
)

# Emite el evento a DataHub
rest_emitter = DatahubRestEmitter(gms_server=gms_server, token=token)
rest_emitter.emit(event)

print(f"Creado término de glosario: (term_urn)")
