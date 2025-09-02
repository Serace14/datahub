package com.linkedin.datahub.graphql.types.catalogrecord.mappers;

import com.linkedin.common.Deprecation;
import com.linkedin.common.GlobalTags;
import com.linkedin.common.GlossaryTerms;
import com.linkedin.common.InstitutionalMemory;
import com.linkedin.common.Ownership;
import com.linkedin.common.Status;
import com.linkedin.common.urn.Urn;
import com.linkedin.data.DataMap;
import com.linkedin.datahub.graphql.QueryContext;
import com.linkedin.datahub.graphql.authorization.AuthorizationUtils;
import com.linkedin.datahub.graphql.generated.FabricType;
import com.linkedin.datahub.graphql.generated.*;
import com.linkedin.datahub.graphql.types.common.mappers.*;
import com.linkedin.datahub.graphql.types.common.mappers.util.MappingHelper;
import com.linkedin.datahub.graphql.types.domain.DomainAssociationMapper;
import com.linkedin.datahub.graphql.types.glossary.mappers.GlossaryTermsMapper;
import com.linkedin.datahub.graphql.types.mappers.ModelMapper;
import com.linkedin.datahub.graphql.types.tag.mappers.GlobalTagsMapper;
import com.linkedin.dataset.DatasetDeprecation;
import com.linkedin.dataset.DatasetProperties;
import com.linkedin.dataset.EditableDatasetProperties;
import com.linkedin.dataset.ViewProperties;
import com.linkedin.domain.Domains;
import com.linkedin.entity.EntityResponse;
import com.linkedin.entity.EnvelopedAspectMap;
import com.linkedin.metadata.key.CatalogRecordKey;
import com.linkedin.metadata.key.DatasetKey;
import com.linkedin.mxe.SystemMetadata;
import com.linkedin.schema.EditableSchemaMetadata;
import com.linkedin.schema.SchemaMetadata;
import lombok.extern.slf4j.Slf4j;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;

import static com.linkedin.datahub.graphql.authorization.AuthorizationUtils.canView;
import static com.linkedin.metadata.Constants.*;

/**
 * Maps GMS response objects to objects conforming to the GQL schema.
 *
 * <p>To be replaced by auto-generated mappers implementations
 */
@Slf4j
public class VersionedCatalogRecordMapper implements ModelMapper<EntityResponse, VersionedCatalogRecord> {

  public static final VersionedCatalogRecordMapper INSTANCE = new VersionedCatalogRecordMapper();

  public static VersionedCatalogRecord map(
      @Nullable final QueryContext context, @Nonnull final EntityResponse catalogRecord) {
    return INSTANCE.apply(context, catalogRecord);
  }

  @Override
  public VersionedCatalogRecord apply(
      @Nullable final QueryContext context, @Nonnull final EntityResponse entityResponse) {
    VersionedCatalogRecord result = new VersionedCatalogRecord();
    Urn entityUrn = entityResponse.getUrn();
    result.setUrn(entityResponse.getUrn().toString());
    result.setType(EntityType.CATALOG_RECORD);

    EnvelopedAspectMap aspectMap = entityResponse.getAspects();
    MappingHelper<VersionedCatalogRecord> mappingHelper = new MappingHelper<>(aspectMap, result);
    SystemMetadata schemaSystemMetadata = getSystemMetadata(aspectMap, SCHEMA_METADATA_ASPECT_NAME);

    mappingHelper.mapToResult(CATALOGRECORD_KEY_ASPECT_NAME, this::mapCatalogRecordKey);
    mappingHelper.mapToResult(
        CATALOGRECORD_PROPERTIES_ASPECT_NAME,
        (entity, dataMap) -> this.mapCatalogRecordProperties(entity, dataMap, entityUrn));
    mappingHelper.mapToResult(
        CATALOGRECORD_DEPRECATION_ASPECT_NAME,
        (catalogRecord, dataMap) ->
            catalogRecord.setDeprecation(
                CatalogRecordDeprecationMapper.map(context, new DatasetDeprecation(dataMap))));
    mappingHelper.mapToResult(
        SCHEMA_METADATA_ASPECT_NAME,
        (catalogRecord, dataMap) ->
            catalogRecord.setSchema(
                SchemaMapper.map(
                    context, new SchemaMetadata(dataMap), schemaSystemMetadata, entityUrn)));
    mappingHelper.mapToResult(
        EDITABLE_CATALOGRECORD_PROPERTIES_ASPECT_NAME, this::mapEditableCatalogRecordProperties);
    mappingHelper.mapToResult(VIEW_PROPERTIES_ASPECT_NAME, this::mapViewProperties);
    mappingHelper.mapToResult(
        INSTITUTIONAL_MEMORY_ASPECT_NAME,
        (catalogRecord, dataMap) ->
                catalogRecord.setInstitutionalMemory(
                InstitutionalMemoryMapper.map(
                    context, new InstitutionalMemory(dataMap), entityUrn)));
    mappingHelper.mapToResult(
        OWNERSHIP_ASPECT_NAME,
        (catalogRecord, dataMap) ->
                catalogRecord.setOwnership(OwnershipMapper.map(context, new Ownership(dataMap), entityUrn)));
    mappingHelper.mapToResult(
        STATUS_ASPECT_NAME,
        (catalogRecord, dataMap) -> catalogRecord.setStatus(StatusMapper.map(context, new Status(dataMap))));
    mappingHelper.mapToResult(
        GLOBAL_TAGS_ASPECT_NAME,
        (catalogRecord, dataMap) -> mapGlobalTags(context, catalogRecord, dataMap, entityUrn));
    mappingHelper.mapToResult(
        EDITABLE_SCHEMA_METADATA_ASPECT_NAME,
        (catalogRecord, dataMap) ->
                catalogRecord.setEditableSchemaMetadata(
                EditableSchemaMetadataMapper.map(
                    context, new EditableSchemaMetadata(dataMap), entityUrn)));
    mappingHelper.mapToResult(
        GLOSSARY_TERMS_ASPECT_NAME,
        (catalogRecord, dataMap) ->
                catalogRecord.setGlossaryTerms(
                GlossaryTermsMapper.map(context, new GlossaryTerms(dataMap), entityUrn)));
    mappingHelper.mapToResult(
        context, CONTAINER_ASPECT_NAME, VersionedCatalogRecordMapper::mapContainers);
    mappingHelper.mapToResult(context, DOMAINS_ASPECT_NAME, VersionedCatalogRecordMapper::mapDomains);
    mappingHelper.mapToResult(
        DEPRECATION_ASPECT_NAME,
        (catalogRecord, dataMap) ->
                catalogRecord.setDeprecation(DeprecationMapper.map(context, new Deprecation(dataMap))));

    if (context != null && !canView(context.getOperationContext(), entityUrn)) {
      return AuthorizationUtils.restrictEntity(mappingHelper.getResult(), VersionedCatalogRecord.class);
    } else {
      return mappingHelper.getResult();
    }
  }

  private SystemMetadata getSystemMetadata(EnvelopedAspectMap aspectMap, String aspectName) {
    if (aspectMap.containsKey(aspectName) && aspectMap.get(aspectName).hasSystemMetadata()) {
      return aspectMap.get(aspectName).getSystemMetadata();
    }
    return null;
  }

  private void mapCatalogRecordKey(@Nonnull VersionedCatalogRecord dataset, @Nonnull DataMap dataMap) {
    final CatalogRecordKey gmsKey = new CatalogRecordKey(dataMap);
    dataset.setName(gmsKey.getName());
    dataset.setPlatform(
        DataPlatform.builder()
            .setType(EntityType.DATA_PLATFORM)
            .setUrn(gmsKey.getPlatform().toString())
            .build());
  }

  private void mapCatalogRecordProperties(
      @Nonnull VersionedCatalogRecord catalogrecord, @Nonnull DataMap dataMap, Urn entityUrn) {
    final DatasetProperties gmsProperties = new DatasetProperties(dataMap);
    final com.linkedin.datahub.graphql.generated.DatasetProperties properties =
        new com.linkedin.datahub.graphql.generated.DatasetProperties();
    properties.setDescription(gmsProperties.getDescription());
    if (gmsProperties.getExternalUrl() != null) {
      properties.setExternalUrl(gmsProperties.getExternalUrl().toString());
    }
    properties.setCustomProperties(
        CustomPropertiesMapper.map(gmsProperties.getCustomProperties(), entityUrn));
    if (gmsProperties.getName() != null) {
      properties.setName(gmsProperties.getName());
    } else {
      properties.setName(catalogrecord.getName());
    }
    properties.setQualifiedName(gmsProperties.getQualifiedName());
    catalogrecord.setProperties(properties);
  }

  private void mapEditableCatalogRecordProperties(
      @Nonnull VersionedCatalogRecord catalogRecord, @Nonnull DataMap dataMap) {
    final EditableDatasetProperties editableDatasetProperties =
        new EditableDatasetProperties(dataMap);
    final DatasetEditableProperties editableProperties = new DatasetEditableProperties();
    editableProperties.setDescription(editableDatasetProperties.getDescription());
    catalogRecord.setEditableProperties(editableProperties);
  }

  private void mapViewProperties(@Nonnull VersionedCatalogRecord catalogRecord, @Nonnull DataMap dataMap) {
    final ViewProperties properties = new ViewProperties(dataMap);
    final com.linkedin.datahub.graphql.generated.ViewProperties graphqlProperties =
        new com.linkedin.datahub.graphql.generated.ViewProperties();
    graphqlProperties.setMaterialized(properties.isMaterialized());
    graphqlProperties.setLanguage(properties.getViewLanguage());
    graphqlProperties.setLogic(properties.getViewLogic());
    catalogRecord.setViewProperties(graphqlProperties);
  }

  private static void mapGlobalTags(
      @Nullable final QueryContext context,
      @Nonnull VersionedCatalogRecord catalogRecord,
      @Nonnull DataMap dataMap,
      @Nonnull Urn entityUrn) {
    com.linkedin.datahub.graphql.generated.GlobalTags globalTags =
        GlobalTagsMapper.map(context, new GlobalTags(dataMap), entityUrn);
    catalogRecord.setTags(globalTags);
  }

  private static void mapContainers(
      @Nullable final QueryContext context,
      @Nonnull VersionedCatalogRecord catalogRecord,
      @Nonnull DataMap dataMap) {
    final com.linkedin.container.Container gmsContainer =
        new com.linkedin.container.Container(dataMap);
    catalogRecord.setContainer(
        Container.builder()
            .setType(EntityType.CONTAINER)
            .setUrn(gmsContainer.getContainer().toString())
            .build());
  }

  private static void mapDomains(
      @Nullable final QueryContext context,
      @Nonnull VersionedCatalogRecord catalogRecord,
      @Nonnull DataMap dataMap) {
    final Domains domains = new Domains(dataMap);
    // Currently we only take the first domain if it exists.
    catalogRecord.setDomain(DomainAssociationMapper.map(context, domains, catalogRecord.getUrn()));
  }
}
