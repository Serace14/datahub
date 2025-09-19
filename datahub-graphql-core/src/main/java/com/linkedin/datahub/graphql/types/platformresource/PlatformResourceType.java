package com.linkedin.datahub.graphql.types.platformresource;

import static com.linkedin.metadata.Constants.*;

import com.google.common.collect.ImmutableSet;
import com.linkedin.common.urn.Urn;
import com.linkedin.common.urn.UrnUtils;
import com.linkedin.datahub.graphql.QueryContext;
import com.linkedin.datahub.graphql.generated.Entity;
import com.linkedin.datahub.graphql.generated.EntityType;
import com.linkedin.datahub.graphql.generated.PlatformResource;
import com.linkedin.datahub.graphql.types.platformresource.mappers.PlatformResourceMapper;
import com.linkedin.entity.EntityResponse;
import com.linkedin.entity.client.EntityClient;
import com.linkedin.metadata.Constants;
import graphql.execution.DataFetcherResult;
import java.net.URISyntaxException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;
import javax.annotation.Nonnull;

public class PlatformResourceType
    implements com.linkedin.datahub.graphql.types.EntityType<PlatformResource, String> {

  static final Set<String> ASPECTS_TO_FETCH =
      ImmutableSet.of(
          Constants.PLATFORM_RESOURCE_INFO_ASPECT_NAME,
          Constants.DATA_PLATFORM_INSTANCE_ASPECT_NAME,
          Constants.STATUS_ASPECT_NAME,
          Constants.STRUCTURED_PROPERTIES_ASPECT_NAME);

  private static final Set<String> FACET_FIELDS = ImmutableSet.of("origin", "platform");
  private static final String ENTITY_NAME = "platformResource";
  private final EntityClient _entityClient;

  public PlatformResourceType(final EntityClient entityClient) {
    _entityClient = entityClient;
  }

  @Override
  public EntityType type() {
    return EntityType.PLATFORM_RESOURCE;
  }

  @Override
  public Function<Entity, String> getKeyProvider() {
    return Entity::getUrn;
  }

  @Override
  public Class<PlatformResource> objectClass() {
    return PlatformResource.class;
  }

  @Override
  public List<DataFetcherResult<PlatformResource>> batchLoad(
      @Nonnull List<String> urns, @Nonnull QueryContext context) throws Exception {
    final List<Urn> platformResourceUrns =
        urns.stream().map(UrnUtils::getUrn).collect(Collectors.toList());

    try {
      final Map<Urn, EntityResponse> entityMap =
          _entityClient.batchGetV2(
              context.getOperationContext(),
              Constants.PLATFORM_RESOURCE_ENTITY_NAME,
              new HashSet<>(platformResourceUrns),
              ASPECTS_TO_FETCH);

      final List<EntityResponse> gmsResults = new ArrayList<>();
      for (Urn urn : platformResourceUrns) {
        gmsResults.add(entityMap.getOrDefault(urn, null));
      }

      return gmsResults.stream()
          .map(
              gmsEntity ->
                  gmsEntity == null
                      ? null
                      : DataFetcherResult.<PlatformResource>newResult()
                          .data(PlatformResourceMapper.map(context, gmsEntity))
                          .build())
          .collect(Collectors.toList());
    } catch (Exception e) {
      throw new RuntimeException("Failed to batch load PlatformResource", e);
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
