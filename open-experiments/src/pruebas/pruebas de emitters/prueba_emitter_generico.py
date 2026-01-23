import datahub.emitter.mce_builder as builder
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata.schema_classes import DatasetPropertiesClass

from datahub.emitter.rest_emitter import DatahubRestEmitter

# Create an emitter to DataHub over REST
emitter = DatahubRestEmitter(gms_server="http://localhost:8080", token="eyJhbGciOiJIUzI1NiJ9.eyJhY3RvclR5cGUiOiJVU0VSIiwiYWN0b3JJZCI6ImRhdGFodWIiLCJ0eXBlIjoiUEVSU09OQUwiLCJ2ZXJzaW9uIjoiMiIsImp0aSI6ImQyNDU4YTRkLTc2YTYtNDQ4My1iNWYyLTA2MDRiMjZiYmE4NiIsInN1YiI6ImRhdGFodWIiLCJleHAiOjE3NTU2ODA3NzksImlzcyI6ImRhdGFodWItbWV0YWRhdGEtc2VydmljZSJ9.pO264G1P2YRwLdIumiiT5s49wY7tmD0MLSpKHNaCOH8")

# For DataHub Cloud, you will want to point to your DataHub Cloud's server's GMS endpoint
# emitter = DatahubRestEmitter(gms_server="https://<your-domain>.acryl.io/gms", token="<your token>", extra_headers={})

# Test the connection
emitter.test_connection()

# Construct a dataset properties object
dataset_properties = DatasetPropertiesClass(description="This table stored the canonical User profile",
    customProperties={
         "governance": "ENABLED"
    })

# Construct a MetadataChangeProposalWrapper object.
metadata_event = MetadataChangeProposalWrapper(
    entityUrn=builder.make_dataset_urn("bigquery", "my-project.my-dataset.user-table"),
    aspect=dataset_properties,
)

# Emit metadata! This is a blocking call
emitter.emit(metadata_event)