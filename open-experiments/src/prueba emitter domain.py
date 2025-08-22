# Inlined from /metadata-ingestion/examples/library/dataset_add_domain.py
from datahub.metadata.urns import DatasetUrn, DomainUrn
from datahub.sdk import DataHubClient

client = DataHubClient.from_env()

dataset = client.entities.get(DatasetUrn(platform="geoserver", name="ef7d1ebc-be18-4cb0-af55-17a3cb509434"))

# if you don't know the domain id, you can get it from resolve client by name
# domain_urn = client.resolve.domain(name="marketing")

# NOTE : This will overwrite the existing domain
dataset.set_domain(DomainUrn(id="Datos_Espaciales"))

client.entities.update(dataset)
