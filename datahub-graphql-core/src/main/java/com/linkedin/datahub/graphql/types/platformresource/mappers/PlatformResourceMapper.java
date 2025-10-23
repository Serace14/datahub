package com.linkedin.datahub.graphql.types.platformresource.mappers;

import static com.linkedin.datahub.graphql.authorization.AuthorizationUtils.canView;
import static com.linkedin.metadata.Constants.*;

import com.linkedin.common.*;
import com.linkedin.common.urn.Urn;
import com.linkedin.data.DataMap;
import com.linkedin.datahub.graphql.QueryContext;
import com.linkedin.datahub.graphql.authorization.AuthorizationUtils;
import com.linkedin.datahub.graphql.generated.EntityType;
import com.linkedin.datahub.graphql.generated.PlatformResource;
import com.linkedin.datahub.graphql.generated.PlatformResourceInfo;
import com.linkedin.datahub.graphql.generated.SerializedValue;
// import com.linkedin.datahub.graphql.generated.SerializedValueContentType;
// import com.linkedin.datahub.graphql.generated.SerializedValueSchemaType;
import com.linkedin.datahub.graphql.types.common.mappers.DataPlatformInstanceAspectMapper;
import com.linkedin.datahub.graphql.types.common.mappers.SiblingsMapper;
import com.linkedin.datahub.graphql.types.common.mappers.StatusMapper;
import com.linkedin.datahub.graphql.types.common.mappers.UpstreamLineagesMapper;
import com.linkedin.datahub.graphql.types.common.mappers.util.MappingHelper;
import com.linkedin.datahub.graphql.types.mappers.ModelMapper;
import com.linkedin.datahub.graphql.types.structuredproperty.StructuredPropertiesMapper;
import com.linkedin.dataset.UpstreamLineage;
import com.linkedin.entity.EntityResponse;
import com.linkedin.entity.EnvelopedAspectMap;
import com.linkedin.platformresource.PlatformResourceKey;
import com.linkedin.structured.StructuredProperties;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Collections;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

public class PlatformResourceMapper implements ModelMapper<EntityResponse, PlatformResource> {

  public static final PlatformResourceMapper INSTANCE = new PlatformResourceMapper();

  public static PlatformResource map(
      @Nullable final QueryContext context, @Nonnull final EntityResponse entityResponse) {
    return INSTANCE.apply(context, entityResponse);
  }

  public PlatformResource apply(
      @Nullable final QueryContext context, @Nonnull final EntityResponse entityResponse) {
    final PlatformResource result = new PlatformResource();
    Urn entityUrn = entityResponse.getUrn();

    result.setUrn(entityResponse.getUrn().toString());
    result.setType(EntityType.PLATFORM_RESOURCE);
    EnvelopedAspectMap aspectMap = entityResponse.getAspects();

    MappingHelper<PlatformResource> mappingHelper = new MappingHelper<>(aspectMap, result);
    mappingHelper.mapToResult(PLATFORM_RESOURCE_KEY_ASPECT_NAME, this::mapPlatformResourceKey);
    mappingHelper.mapToResult(
        PLATFORM_RESOURCE_INFO_ASPECT_NAME,
        (entity, dataMap) -> this.mapPlatformResourceInfo(context, entity, dataMap, entityUrn));

    mappingHelper.mapToResult(
        STATUS_ASPECT_NAME,
        (platformResource, dataMap) ->
            platformResource.setStatus(StatusMapper.map(context, new Status(dataMap))));

    mappingHelper.mapToResult(
        DATA_PLATFORM_INSTANCE_ASPECT_NAME,
        (dataset, dataMap) ->
            dataset.setDataPlatformInstance(
                DataPlatformInstanceAspectMapper.map(context, new DataPlatformInstance(dataMap))));

    mappingHelper.mapToResult(
        STRUCTURED_PROPERTIES_ASPECT_NAME,
        ((platformResource, dataMap) ->
            platformResource.setStructuredProperties(
                StructuredPropertiesMapper.map(
                    context, new StructuredProperties(dataMap), entityUrn))));
    mappingHelper.mapToResult(
        SIBLINGS_ASPECT_NAME,
        (platformResource, dataMap) ->
            platformResource.setSiblings(SiblingsMapper.map(context, new Siblings(dataMap))));
    mappingHelper.mapToResult(
        UPSTREAM_LINEAGE_ASPECT_NAME,
        (platformResource, dataMap) ->
            platformResource.setFineGrainedLineages(
                UpstreamLineagesMapper.map(new UpstreamLineage(dataMap))));

    if (context != null && !canView(context.getOperationContext(), entityUrn)) {
      return AuthorizationUtils.restrictEntity(mappingHelper.getResult(), PlatformResource.class);
    } else {
      return mappingHelper.getResult();
    }
  }

  private void mapPlatformResourceKey(
      @Nonnull PlatformResource platformResource, @Nonnull DataMap dataMap) {
    final PlatformResourceKey gmsKey = new PlatformResourceKey(dataMap);
    platformResource.setId(gmsKey.getId());
  }

  private void mapPlatformResourceInfo(
      @Nonnull QueryContext context,
      @Nonnull PlatformResource PlatformResource,
      @Nonnull DataMap dataMap,
      Urn entityUrn) {
    final com.linkedin.platformresource.PlatformResourceInfo gmsPlatformResourceInfo =
        new com.linkedin.platformresource.PlatformResourceInfo(dataMap);
    PlatformResource.setInfo(mapInfo(context, gmsPlatformResourceInfo, entityUrn));
  }

  /**
   * Maps GMS {@link com.linkedin.platformresource.PlatformResourceInfo} to deprecated GraphQL
   * {@link PlatformResourceInfo}
   */
  private static PlatformResourceInfo mapInfo(
      @Nullable final QueryContext context,
      final com.linkedin.platformresource.PlatformResourceInfo info,
      Urn entityUrn) {

    final PlatformResourceInfo result = new PlatformResourceInfo();

    // Mapeo simple
    result.setResourceType(info.getResourceType());
    result.setPrimaryKey(info.getPrimaryKey());
    result.setSecondaryKeys(
        info.getSecondaryKeys() != null
            ? new ArrayList<>(info.getSecondaryKeys())
            : Collections.emptyList());

    // Mapeo del SerializedValue
    if (info.getValue() != null) {
      SerializedValue sv = new SerializedValue();
      if (info.getValue().getBlob() != null) {
        // convertir ByteString a byte[] y luego a Base64 String
        String blobBase64 =
            Base64.getEncoder().encodeToString(info.getValue().getBlob().copyBytes());
        sv.setBlob(blobBase64);
      }
      sv.setContentType(mapContentType(info.getValue().getContentType()));
      if (info.getValue().hasSchemaType()) {
        sv.setSchemaType(mapSchemaType(info.getValue().getSchemaType()));
      }
      if (info.getValue().hasSchemaRef()) {
        sv.setSchemaRef(info.getValue().getSchemaRef());
      }
      result.setValue(sv);
    }

    if (info.getXmlText() != null) {
      result.setXmlText(info.getXmlText());
    }

    return result;
  }

  private static com.linkedin.datahub.graphql.generated.SerializedValueContentType mapContentType(
      SerializedValueContentType ct) {
    switch (ct) {
      case JSON:
        return com.linkedin.datahub.graphql.generated.SerializedValueContentType.JSON;
      case BINARY:
        return com.linkedin.datahub.graphql.generated.SerializedValueContentType.BINARY;
      default:
        throw new IllegalArgumentException("Unknown content type: " + ct);
    }
  }

  private static com.linkedin.datahub.graphql.generated.SerializedValueSchemaType mapSchemaType(
      SerializedValueSchemaType st) {
    switch (st) {
      case AVRO:
        return com.linkedin.datahub.graphql.generated.SerializedValueSchemaType.AVRO;
      case PROTOBUF:
        return com.linkedin.datahub.graphql.generated.SerializedValueSchemaType.PROTOBUF;
      case PEGASUS:
        return com.linkedin.datahub.graphql.generated.SerializedValueSchemaType.PEGASUS;
      case THRIFT:
        return com.linkedin.datahub.graphql.generated.SerializedValueSchemaType.THRIFT;
      case JSON:
        return com.linkedin.datahub.graphql.generated.SerializedValueSchemaType.JSON;
      case NONE:
        return com.linkedin.datahub.graphql.generated.SerializedValueSchemaType.NONE;
      default:
        throw new IllegalArgumentException("Unknown schema type: " + st);
    }
  }
}
