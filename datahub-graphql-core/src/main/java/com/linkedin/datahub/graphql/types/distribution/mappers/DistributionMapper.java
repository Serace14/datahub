package com.linkedin.datahub.graphql.types.distribution.mappers;

import static com.linkedin.datahub.graphql.authorization.AuthorizationUtils.canView;
import static com.linkedin.metadata.Constants.*;
import static com.linkedin.metadata.Constants.STRUCTURED_PROPERTIES_ASPECT_NAME;

import com.linkedin.common.Ownership;
import com.linkedin.common.urn.Urn;
import com.linkedin.data.DataMap;
import com.linkedin.datahub.graphql.QueryContext;
import com.linkedin.datahub.graphql.authorization.AuthorizationUtils;
import com.linkedin.datahub.graphql.generated.*;
import com.linkedin.datahub.graphql.types.common.mappers.AuditStampMapper;
import com.linkedin.datahub.graphql.types.common.mappers.OwnershipMapper;
import com.linkedin.datahub.graphql.types.common.mappers.util.MappingHelper;
import com.linkedin.datahub.graphql.types.mappers.ModelMapper;
import com.linkedin.datahub.graphql.types.structuredproperty.StructuredPropertiesMapper;
import com.linkedin.entity.EntityResponse;
import com.linkedin.entity.EnvelopedAspectMap;
import com.linkedin.metadata.key.DistributionKey;
import com.linkedin.structured.StructuredProperties;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

public class DistributionMapper implements ModelMapper<EntityResponse, Distribution> {
  public static final DistributionMapper INSTANCE = new DistributionMapper();

  public static Distribution map(
      @Nullable final QueryContext context, @Nonnull final EntityResponse entityResponse) {
    return INSTANCE.apply(context, entityResponse);
  }

  public Distribution apply(
      @Nullable final QueryContext context, @Nonnull final EntityResponse entityResponse) {
    final Distribution result = new Distribution();
    Urn entityUrn = entityResponse.getUrn();

    result.setUrn(entityResponse.getUrn().toString());
    result.setType(EntityType.DISTRIBUTION);
    EnvelopedAspectMap aspectMap = entityResponse.getAspects();

    MappingHelper<Distribution> mappingHelper = new MappingHelper<>(aspectMap, result);
    mappingHelper.mapToResult(DISTRIBUTION_KEY_ASPECT_NAME, this::mapDistributionKey);
    mappingHelper.mapToResult(
        DISTRIBUTION_INFO_ASPECT_NAME,
        (entity, dataMap) -> this.mapDistributionInfo(context, entity, dataMap, entityUrn));

    mappingHelper.mapToResult(
        STRUCTURED_PROPERTIES_ASPECT_NAME,
        ((distribution, dataMap) ->
            distribution.setStructuredProperties(
                StructuredPropertiesMapper.map(
                    context, new StructuredProperties(dataMap), entityUrn))));

    mappingHelper.mapToResult(
        OWNERSHIP_ASPECT_NAME,
        ((distribution, dataMap) ->
            distribution.setOwnership(
                OwnershipMapper.map(context, new Ownership(dataMap), entityUrn))));

    if (context != null && !canView(context.getOperationContext(), entityUrn)) {
      return AuthorizationUtils.restrictEntity(mappingHelper.getResult(), Distribution.class);
    } else {
      return mappingHelper.getResult();
    }
  }

  private void mapDistributionKey(@Nonnull Distribution distribution, @Nonnull DataMap dataMap) {
    final DistributionKey gmsKey = new DistributionKey(dataMap);
    distribution.setId(gmsKey.getId());
  }

  private void mapDistributionInfo(
      @Nonnull QueryContext context,
      @Nonnull Distribution Distribution,
      @Nonnull DataMap dataMap,
      Urn entityUrn) {
    final com.linkedin.distribution.DistributionInfo gmsDistributionInfo =
        new com.linkedin.distribution.DistributionInfo(dataMap);
    Distribution.setInfo(mapInfo(context, gmsDistributionInfo, entityUrn));
  }

  private static DistributionInfo mapInfo(
      @Nullable final QueryContext context,
      final com.linkedin.distribution.DistributionInfo info,
      Urn entityUrn) {

    final DistributionInfo result = new DistributionInfo();

    // --- Mapeo de campos simples ---
    if (info.hasTitle()) {
      result.setName(info.getTitle());
    }
    if (info.hasDescription()) {
      result.setDescription(info.getDescription());
    }

    result.setLastModified(AuditStampMapper.map(context, info.getLastModified().getLastModified()));

    // --- Mapeo de lastRefreshed ---
    if (info.hasLastRefreshed()) {
      result.setLastRefreshed(info.getLastRefreshed());
    }

    // --- Mapeo de accessURL y accessService ---
    if (info.hasAccessURL()) {
      Dataset accessUrlDataset = new Dataset();
      accessUrlDataset.setUrn(info.getAccessURL().toString());
      result.setAccessURL(accessUrlDataset);
    }

    if (info.hasAccessService()) {
      Dataset accessServiceDataset = new Dataset();
      accessServiceDataset.setUrn(info.getAccessService().toString());
      result.setAccessService(accessServiceDataset);
    }

    return result;
  }
}
