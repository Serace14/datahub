from typing import Any

from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.metadata._internal_schema_classes import CorpGroupInfoClass, OwnershipClass, OwnershipTypeClass, \
    OwnerClass, GlobalTagsClass, TagPropertiesClass
from datahub.specific.dataset import DatasetPatchBuilder
import datahub.emitter.mce_builder as builder


def emit_structured_property(dataset_urn: str, property_urn: str, value: Any, emitter):
    patch_builder = DatasetPatchBuilder(dataset_urn)
    patch_builder.set_structured_property(property_urn, value)
    for patch_mcp in patch_builder.build():
        emitter.emit(patch_mcp)
    print(f"✅ Structured property '{property_urn}' actualizada para {dataset_urn}: {value}")

def emit_tags(dataset_urn: str, value: Any, emitter):
    # Crear la propuesta de cambio solo para GlobalTags
    dataset_tags_mcp = MetadataChangeProposalWrapper(
        entityUrn=dataset_urn,
        aspect=GlobalTagsClass(tags=value)
    )
    emitter.emit(dataset_tags_mcp)
    print(f"Tags asignados al dataset existente {dataset_urn}: {value}")

def create_new_tag(tag: str, emitter):
    tag_urn = builder.make_tag_urn(tag.replace(" ", "_"))
    tag_aspect = TagPropertiesClass(
        name=tag,
        description=f"Tag importado desde CSW: {tag}"
    )
    emitter.emit(MetadataChangeProposalWrapper(entityUrn=tag_urn, aspect=tag_aspect))
    print(f"Tag creado/actualizado: {tag_urn}")

def create_new_corpgroup(org_name: str, group_urn: str, emitter):
    # Emitir el corpGroup
    corpgroup_info = CorpGroupInfoClass(
        displayName=org_name,
        description=f"Organisation from CSW metadata: {org_name}",
        admins=[],
        members=[],
        groups=[]
    )
    emitter.emit(
        MetadataChangeProposalWrapper(entityUrn=group_urn, aspect=corpgroup_info)
    )
    print(f"CorpGroup emitido: {group_urn}")
    return group_urn

def set_ownership(group_urn:str, dataset_urn: str, emitter):
    # Construcción del Ownership
    ownership_aspect = OwnershipClass(
        owners=[
            OwnerClass(
                owner=group_urn,
                type=OwnershipTypeClass.TECHNICAL_OWNER,  # puedes ajustar el tipo
            )
        ]
    )

    # Emitir ownership al dataset
    emitter.emit(
        MetadataChangeProposalWrapper(entityUrn=dataset_urn, aspect=ownership_aspect)
    )
    print(f"Ownership asociado a {dataset_urn}: {group_urn}")

def set_urls(dataset_urn: str, url_urn: str, url_value: str, emitter):
    patch_builder = DatasetPatchBuilder(dataset_urn)
    patch_builder.set_structured_property(
        url_urn,
        url_value
    )
    patch_mcps = patch_builder.build()

    for patch_mcp in patch_mcps:
        emitter.emit(patch_mcp)

    print(f"Structured property 'urls' actualizada para ({dataset_urn})")