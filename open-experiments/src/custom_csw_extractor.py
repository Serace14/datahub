# custom_csw_extractor.py

from typing import Iterable, Dict, Any
from datahub.ingestion.api.source import Source
from datahub.ingestion.api.common import PipelineContext
from datahub.metadata.schema_classes import DatasetSnapshotClass, MetadataChangeProposalWrapper, DataPlatformInstanceClass, StatusClass, DatasetPropertiesClass, DatasetUrn
from owslib.csw import CatalogueServiceWeb
from owslib.fes import PropertyIsLike
import logging

logger = logging.getLogger(__name__)

class CSWExtractor(Source):
    def __init__(self, ctx: PipelineContext, config: Dict[str, Any], **kwargs):
        super().__init__(ctx)
        self.csw_endpoint = config["csw_endpoint"]
        self.filter_keywords = config.get("filter_keywords", [])
        self.limit = config.get("limit", 20)
        self.platform_urn = config.get("platform_urn", "urn:li:dataPlatform:csw")
        self.environment = config.get("environment", "PROD")
        self.csw = CatalogueServiceWeb(self.csw_endpoint)

    def get_workunits(self) -> Iterable[MetadataChangeProposalWrapper]:
        constraints = [
            PropertyIsLike(propertyname="csw:AnyText", literal=f"*{kw}*", wildCard="*", escapeChar="\\", singleChar="?")
            for kw in self.filter_keywords
        ]

        if constraints:
            self.csw.getrecords2(constraints=constraints, maxrecords=self.limit)
        else:
            self.csw.getrecords2(maxrecords=self.limit)

        logger.info(f"Found {len(self.csw.records)} records")

        for identifier, record in self.csw.records.items():
            name = record.title or "unknown"
            description = record.abstract or ""
            urn = DatasetUrn.create_from_ids(
                platform=self.platform_urn.split(":")[-1],
                name=name.replace(" ", "_").lower(),
                env=self.environment
            )

            yield MetadataChangeProposalWrapper(
                entityUrn=str(urn),
                aspect=DatasetSnapshotClass(
                    urn=str(urn),
                    aspects=[
                        StatusClass(removed=False),
                        DatasetPropertiesClass(
                            name=name,
                            description=description,
                            customProperties={
                                "identifier": identifier,
                                "keywords": ", ".join(record.subjects or []),
                                "type": record.type,
                                "modified": str(record.modified),
                                "source": self.csw_endpoint,
                            }
                        ),
                        DataPlatformInstanceClass(
                            platform=self.platform_urn,
                            instance="csw-instance"
                        ),
                    ]
                )
            )

    def close(self):
        pass
