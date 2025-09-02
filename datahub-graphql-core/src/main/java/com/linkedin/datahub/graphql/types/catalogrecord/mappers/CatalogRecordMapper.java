package com.linkedin.datahub.graphql.types.catalogrecord.mappers;

import com.linkedin.application.Applications;
import com.linkedin.common.Access;
import com.linkedin.common.DataPlatformInstance;
import com.linkedin.common.Deprecation;
import com.linkedin.common.Embed;
import com.linkedin.common.Forms;
import com.linkedin.common.GlobalTags;
import com.linkedin.common.GlossaryTerms;
import com.linkedin.common.InstitutionalMemory;
import com.linkedin.common.Ownership;
import com.linkedin.common.Status;
import com.linkedin.common.SubTypes;
import com.linkedin.common.VersionProperties;
import com.linkedin.common.*;
import com.linkedin.common.urn.Urn;
import com.linkedin.data.DataMap;
import com.linkedin.datahub.graphql.QueryContext;
import com.linkedin.datahub.graphql.authorization.AuthorizationUtils;
import com.linkedin.datahub.graphql.generated.AuditStamp;
import com.linkedin.datahub.graphql.generated.FabricType;
import com.linkedin.datahub.graphql.generated.*;
import com.linkedin.datahub.graphql.types.application.ApplicationAssociationMapper;
import com.linkedin.datahub.graphql.types.common.mappers.*;
import com.linkedin.datahub.graphql.types.common.mappers.util.MappingHelper;
import com.linkedin.datahub.graphql.types.common.mappers.util.SystemMetadataUtils;
import com.linkedin.datahub.graphql.types.domain.DomainAssociationMapper;
import com.linkedin.datahub.graphql.types.form.FormsMapper;
import com.linkedin.datahub.graphql.types.glossary.mappers.GlossaryTermsMapper;
import com.linkedin.datahub.graphql.types.mappers.ModelMapper;
import com.linkedin.datahub.graphql.types.rolemetadata.mappers.AccessMapper;
import com.linkedin.datahub.graphql.types.structuredproperty.StructuredPropertiesMapper;
import com.linkedin.datahub.graphql.types.tag.mappers.GlobalTagsMapper;
import com.linkedin.datahub.graphql.types.versioning.VersionPropertiesMapper;
import com.linkedin.dataset.DatasetDeprecation;
import com.linkedin.dataset.DatasetProperties;
import com.linkedin.dataset.ViewProperties;
import com.linkedin.dataset.*;
import com.linkedin.domain.Domains;
import com.linkedin.entity.EntityResponse;
import com.linkedin.entity.EnvelopedAspectMap;
import com.linkedin.metadata.key.DatasetKey;
import com.linkedin.metadata.key.CatalogRecordKey;
import com.linkedin.schema.EditableSchemaMetadata;
import com.linkedin.schema.SchemaMetadata;
import com.linkedin.structured.StructuredProperties;
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
public class CatalogRecordMapper implements ModelMapper<EntityResponse, CatalogRecord> {

  public static final CatalogRecordMapper INSTANCE = new CatalogRecordMapper();

  public static CatalogRecord map(
      @Nullable final QueryContext context, @Nonnull final EntityResponse catalogrecord) {
    return INSTANCE.apply(context, catalogrecord);
  }

  public CatalogRecord apply(@Nonnull final EntityResponse entityResponse) {
    return apply(null, entityResponse);
  }

  public CatalogRecord apply(
      @Nullable final QueryContext context, @Nonnull final EntityResponse entityResponse) {
    CatalogRecord result = new CatalogRecord();
    Urn entityUrn = entityResponse.getUrn();
    result.setUrn(entityResponse.getUrn().toString());
    result.setType(EntityType.CATALOG_RECORD);

    EnvelopedAspectMap aspectMap = entityResponse.getAspects();
    Long lastIngested = SystemMetadataUtils.getLastIngestedTime(aspectMap);
    result.setLastIngested(lastIngested);

    MappingHelper<CatalogRecord> mappingHelper = new MappingHelper<>(aspectMap, result);
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
                catalogRecord.setSchema(SchemaMapper.map(context, new SchemaMetadata(dataMap), entityUrn)));
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
    mappingHelper.mapToResult(context, CONTAINER_ASPECT_NAME, CatalogRecordMapper::mapContainers);
    mappingHelper.mapToResult(context, DOMAINS_ASPECT_NAME, CatalogRecordMapper::mapDomains);
    mappingHelper.mapToResult(
        APPLICATION_MEMBERSHIP_ASPECT_NAME,
        (catalogRecord, dataMap) -> mapApplicationAssociation(context, catalogRecord, dataMap));
    mappingHelper.mapToResult(
        DEPRECATION_ASPECT_NAME,
        (catalogRecord, dataMap) ->
                catalogRecord.setDeprecation(DeprecationMapper.map(context, new Deprecation(dataMap))));
    mappingHelper.mapToResult(
        DATA_PLATFORM_INSTANCE_ASPECT_NAME,
        (catalogRecord, dataMap) ->
                catalogRecord.setDataPlatformInstance(
                DataPlatformInstanceAspectMapper.map(context, new DataPlatformInstance(dataMap))));
    mappingHelper.mapToResult(
        "applications", (catalogRecord, dataMap) -> mapApplicationAssociation(context, catalogRecord, dataMap));
    mappingHelper.mapToResult(
        SIBLINGS_ASPECT_NAME,
        (catalogRecord, dataMap) ->
                catalogRecord.setSiblings(SiblingsMapper.map(context, new Siblings(dataMap))));
    mappingHelper.mapToResult(
        UPSTREAM_LINEAGE_ASPECT_NAME,
        (catalogRecord, dataMap) ->
                catalogRecord.setFineGrainedLineages(
                UpstreamLineagesMapper.map(new UpstreamLineage(dataMap))));
    mappingHelper.mapToResult(
        EMBED_ASPECT_NAME,
        (catalogRecord, dataMap) -> catalogRecord.setEmbed(EmbedMapper.map(context, new Embed(dataMap))));
    mappingHelper.mapToResult(
        BROWSE_PATHS_V2_ASPECT_NAME,
        (catalogRecord, dataMap) ->
                catalogRecord.setBrowsePathV2(BrowsePathsV2Mapper.map(context, new BrowsePathsV2(dataMap))));
    mappingHelper.mapToResult(
        ACCESS_ASPECT_NAME,
        ((catalogRecord, dataMap) ->
                catalogRecord.setAccess(AccessMapper.map(new Access(dataMap), entityUrn))));
    mappingHelper.mapToResult(
        STRUCTURED_PROPERTIES_ASPECT_NAME,
        ((entity, dataMap) ->
            entity.setStructuredProperties(
                StructuredPropertiesMapper.map(
                    context, new StructuredProperties(dataMap), entityUrn))));
    mappingHelper.mapToResult(
        FORMS_ASPECT_NAME,
        ((catalogRecord, dataMap) ->
                catalogRecord.setForms(FormsMapper.map(new Forms(dataMap), entityUrn.toString()))));
    mappingHelper.mapToResult(
        SUB_TYPES_ASPECT_NAME,
        (dashboard, dataMap) ->
            dashboard.setSubTypes(SubTypesMapper.map(context, new SubTypes(dataMap))));
    mappingHelper.mapToResult(
        VERSION_PROPERTIES_ASPECT_NAME,
        (entity, dataMap) ->
            entity.setVersionProperties(
                VersionPropertiesMapper.map(context, new VersionProperties(dataMap))));

    if (context != null && !canView(context.getOperationContext(), entityUrn)) {
      return AuthorizationUtils.restrictEntity(mappingHelper.getResult(), CatalogRecord.class);
    } else {
      return mappingHelper.getResult();
    }
  }

  private void mapCatalogRecordKey(@Nonnull CatalogRecord catalogRecord, @Nonnull DataMap dataMap) {
    final CatalogRecordKey gmsKey = new CatalogRecordKey(dataMap);
    catalogRecord.setName(gmsKey.getName());
    catalogRecord.setPlatform(
        DataPlatform.builder()
            .setType(EntityType.DATA_PLATFORM)
            .setUrn(gmsKey.getPlatform().toString())
            .build());
  }

  private void mapCatalogRecordProperties(
      @Nonnull CatalogRecord catalogRecord, @Nonnull DataMap dataMap, @Nonnull Urn entityUrn) {
    final DatasetProperties gmsProperties = new DatasetProperties(dataMap);
    final com.linkedin.datahub.graphql.generated.DatasetProperties properties =
        new com.linkedin.datahub.graphql.generated.DatasetProperties();
    properties.setDescription(gmsProperties.getDescription());
    catalogRecord.setDescription(gmsProperties.getDescription());
    properties.setOrigin(catalogRecord.getOrigin());
    if (gmsProperties.getExternalUrl() != null) {
      properties.setExternalUrl(gmsProperties.getExternalUrl().toString());
    }
    properties.setCustomProperties(
        CustomPropertiesMapper.map(gmsProperties.getCustomProperties(), entityUrn));
    if (gmsProperties.getName() != null) {
      properties.setName(gmsProperties.getName());
    } else {
      properties.setName(catalogRecord.getName());
    }
    properties.setQualifiedName(gmsProperties.getQualifiedName());
    catalogRecord.setProperties(properties);
    catalogRecord.setDescription(properties.getDescription());
    catalogRecord.setName(properties.getName());
    if (gmsProperties.getUri() != null) {
      catalogRecord.setUri(gmsProperties.getUri().toString());
    }
    TimeStamp created = gmsProperties.getCreated();
    if (created != null) {
      properties.setCreated(created.getTime());
      if (created.hasActor()) {
        properties.setCreatedActor(created.getActor().toString());
      }
    }
    TimeStamp lastModified = gmsProperties.getLastModified();
    if (lastModified != null) {
      Urn actor = lastModified.getActor();
      properties.setLastModified(
          new AuditStamp(lastModified.getTime(), actor == null ? null : actor.toString()));
      properties.setLastModifiedActor(actor == null ? null : actor.toString());
    } else {
      properties.setLastModified(new AuditStamp(0L, null));
    }
  }

  private void mapEditableCatalogRecordProperties(@Nonnull CatalogRecord catalogRecord, @Nonnull DataMap dataMap) {
    final EditableDatasetProperties editableDatasetProperties =
        new EditableDatasetProperties(dataMap);
    final DatasetEditableProperties editableProperties = new DatasetEditableProperties();
    editableProperties.setDescription(editableDatasetProperties.getDescription());
    if (editableDatasetProperties.getName() != null) {
      editableProperties.setName(editableDatasetProperties.getName());
    }
    catalogRecord.setEditableProperties(editableProperties);
  }

  private void mapViewProperties(@Nonnull CatalogRecord catalogRecord, @Nonnull DataMap dataMap) {
    final ViewProperties properties = new ViewProperties(dataMap);
    final com.linkedin.datahub.graphql.generated.ViewProperties graphqlProperties =
        new com.linkedin.datahub.graphql.generated.ViewProperties();
    graphqlProperties.setMaterialized(properties.isMaterialized());
    graphqlProperties.setLanguage(properties.getViewLanguage());
    graphqlProperties.setLogic(properties.getViewLogic());
    graphqlProperties.setFormattedLogic(properties.getFormattedViewLogic());
    catalogRecord.setViewProperties(graphqlProperties);
  }

  private static void mapGlobalTags(
      @Nullable final QueryContext context,
      @Nonnull CatalogRecord catalogRecord,
      @Nonnull DataMap dataMap,
      @Nonnull final Urn entityUrn) {
    com.linkedin.datahub.graphql.generated.GlobalTags globalTags =
        GlobalTagsMapper.map(context, new GlobalTags(dataMap), entityUrn);
    catalogRecord.setGlobalTags(globalTags);
    catalogRecord.setTags(globalTags);
  }

  private static void mapContainers(
      @Nullable final QueryContext context, @Nonnull CatalogRecord catalogRecord, @Nonnull DataMap dataMap) {
    final com.linkedin.container.Container gmsContainer =
        new com.linkedin.container.Container(dataMap);
    catalogRecord.setContainer(
        Container.builder()
            .setType(EntityType.CONTAINER)
            .setUrn(gmsContainer.getContainer().toString())
            .build());
  }

  private static void mapDomains(
      @Nullable final QueryContext context, @Nonnull CatalogRecord catalogRecord, @Nonnull DataMap dataMap) {
    final Domains domains = new Domains(dataMap);
    catalogRecord.setDomain(DomainAssociationMapper.map(context, domains, catalogRecord.getUrn()));
  }

  private static void mapApplicationAssociation(
      @Nullable final QueryContext context, @Nonnull CatalogRecord catalogRecord, @Nonnull DataMap dataMap) {
    final Applications applications = new Applications(dataMap);
    catalogRecord.setApplication(
        ApplicationAssociationMapper.map(context, applications, catalogRecord.getUrn()));
  }
}
