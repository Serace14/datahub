package com.linkedin.datahub.graphql.types.distribution;

import com.google.common.collect.ImmutableSet;
import com.linkedin.common.urn.Urn;
import com.linkedin.common.urn.UrnUtils;
import com.linkedin.datahub.graphql.QueryContext;
import com.linkedin.datahub.graphql.generated.Distribution;
import com.linkedin.datahub.graphql.generated.Entity;
import com.linkedin.datahub.graphql.generated.EntityType;
import com.linkedin.datahub.graphql.types.distribution.mappers.DistributionMapper;
import com.linkedin.entity.EntityResponse;
import com.linkedin.entity.client.EntityClient;
import com.linkedin.metadata.Constants;
import graphql.execution.DataFetcherResult;
import java.net.URISyntaxException;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;
import javax.annotation.Nonnull;

public class DistributionType
    implements com.linkedin.datahub.graphql.types.EntityType<Distribution, String> {

  static final Set<String> ASPECTS_TO_FETCH =
      ImmutableSet.of(
          Constants.DISTRIBUTION_INFO_ASPECT_NAME,
          Constants.STRUCTURED_PROPERTIES_ASPECT_NAME,
          Constants.OWNERSHIP_ASPECT_NAME);

  private static final Set<String> FACET_FIELDS = ImmutableSet.of("origin", "platform");
  private static final String ENTITY_NAME = "distribution";
  private final EntityClient _entityClient;

  public DistributionType(final EntityClient entityClient) {
    _entityClient = entityClient;
  }

  @Override
  public EntityType type() {
    return EntityType.DISTRIBUTION;
  }

  @Override
  public Function<Entity, String> getKeyProvider() {
    return Entity::getUrn;
  }

  @Override
  public Class<Distribution> objectClass() {
    return Distribution.class;
  }

  @Override
  public List<DataFetcherResult<Distribution>> batchLoad(
      @Nonnull List<String> urns, @Nonnull QueryContext context) throws Exception {
    final List<Urn> distributionUrns =
        urns.stream().map(UrnUtils::getUrn).collect(Collectors.toList());

    try {
      final Map<Urn, EntityResponse> entityMap =
          _entityClient.batchGetV2(
              context.getOperationContext(),
              Constants.DISTRIBUTION_ENTITY_NAME,
              new HashSet<>(distributionUrns),
              ASPECTS_TO_FETCH);

      final List<EntityResponse> gmsResults = new ArrayList<>();
      for (Urn urn : distributionUrns) {
        gmsResults.add(entityMap.getOrDefault(urn, null));
      }

      return gmsResults.stream()
          .map(
              gmsEntity ->
                  gmsEntity == null
                      ? null
                      : DataFetcherResult.<Distribution>newResult()
                          .data(DistributionMapper.map(context, gmsEntity))
                          .build())
          .collect(Collectors.toList());
    } catch (Exception e) {
      throw new RuntimeException("Failed to batch load Distribution", e);
    }
  }

  private Urn getUrn(final String urnStr) {
    try {
      return Urn.createFromString(urnStr);
    } catch (URISyntaxException e) {
      throw new RuntimeException(String.format("Failed to convert urn string %s into Urn", urnStr));
    }
  }
}
