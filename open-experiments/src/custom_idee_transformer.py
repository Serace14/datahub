# custom_idee_transformer.py
from typing import List
from datahub.configuration.common import ConfigModel
from datahub.ingestion.api.common import PipelineContext
from datahub.ingestion.api.transform import Transformer
from datahub.ingestion.transformer.base_transformer import BaseTransformer, SingleAspectTransformer
from datahub.metadata.schema_classes import (
    MetadataChangeEventClass,
    GlobalTagsClass,
    TagAssociationClass,
    OwnershipClass,
    OwnerClass,
    DatasetPropertiesClass,
)

class IdeeTransformerConfig(ConfigModel):
    pass  #Se pueden añadir mas cosas

class IdeeTransformer(BaseTransformer, SingleAspectTransformer):
    ctx: PipelineContext
    config: IdeeTransformerConfig

    def __init__(self, config: IdeeTransformerConfig, ctx: PipelineContext):
        super().__init__()
        self.ctx = ctx
        self.config = config

    @classmethod
    def create(cls, config_dict: dict, ctx: PipelineContext) -> "IdeeTransformer":
        config = IdeeTransformerConfig.parse_obj(config_dict)
        return cls(config, ctx)

    def entity_types(self) -> List[str]:
        return ["dataset"]

    def transform_aspect(self, entity_urn: str, aspect_name: str, aspect) -> object:
        # Ejemplo: agregar tags y customProperties
        if aspect_name == "datasetProperties" and isinstance(aspect, DatasetPropertiesClass):
            # Suponiendo que los valores de CSW están en customProperties
            tags = aspect.customProperties.get("tags", "")
            if tags:
                aspect.customProperties["tags"] = tags
            aspect.customProperties["source"] = aspect.customProperties.get("source", "portal IDEE")
            aspect.customProperties["identifier"] = aspect.customProperties.get("identifier", "")
            aspect.customProperties["date"] = aspect.customProperties.get("date", "")
        elif aspect_name == "globalTags":
            tags = aspect.customProperties.get("tags", "")
            if tags:
                tag_list = [TagAssociationClass(tag=f"urn:li:tag:(tag.strip())") for tag in tags.split(",")]
                return GlobalTagsClass(tags=tag_list)
        elif aspect_name == "ownership":
            owner = aspect.customProperties.get("provider", "")
            if owner:
                return OwnershipClass(owners=[OwnerClass(owner=f"urn:li:corpuser:{owner}", type="DATAOWNER")])
        return aspect
