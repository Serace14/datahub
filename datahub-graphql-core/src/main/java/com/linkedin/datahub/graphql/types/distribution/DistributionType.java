package com.linkedin.datahub.graphql.types.distribution;

import static com.linkedin.datahub.graphql.Constants.BROWSE_PATH_DELIMITER;

import com.google.common.collect.ImmutableSet;
import com.linkedin.common.urn.CorpuserUrn;
import com.linkedin.common.urn.Urn;
import com.linkedin.common.urn.UrnUtils;
import com.linkedin.data.template.StringArray;
import com.linkedin.datahub.graphql.QueryContext;
import com.linkedin.datahub.graphql.generated.*;
import com.linkedin.datahub.graphql.resolvers.ResolverUtils;
import com.linkedin.datahub.graphql.types.BrowsableEntityType;
import com.linkedin.datahub.graphql.types.MutableType;
import com.linkedin.datahub.graphql.types.SearchableEntityType;
import com.linkedin.datahub.graphql.types.distribution.mappers.DistributionMapper;
import com.linkedin.datahub.graphql.types.distribution.mappers.DistributionUpdateInputMapper;
import com.linkedin.datahub.graphql.types.mappers.AutoCompleteResultsMapper;
import com.linkedin.datahub.graphql.types.mappers.BrowsePathsMapper;
import com.linkedin.datahub.graphql.types.mappers.BrowseResultMapper;
import com.linkedin.datahub.graphql.types.mappers.UrnSearchResultsMapper;
import com.linkedin.entity.EntityResponse;
import com.linkedin.entity.client.EntityClient;
import com.linkedin.metadata.Constants;
import com.linkedin.metadata.browse.BrowseResult;
import com.linkedin.metadata.query.AutoCompleteResult;
import com.linkedin.metadata.query.filter.Filter;
import com.linkedin.metadata.search.SearchResult;
import com.linkedin.mxe.MetadataChangeProposal;
import com.linkedin.r2.RemoteInvocationException;
import graphql.execution.DataFetcherResult;
import java.net.URISyntaxException;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

public class DistributionType
    implements SearchableEntityType<Distribution, String>,
        BrowsableEntityType<Distribution, String>,
        MutableType<DistributionUpdateInput, Distribution> {

  private static final Set<String> ASPECTS_TO_FETCH =
      ImmutableSet.of(
          Constants.DISTRIBUTION_INFO_ASPECT_NAME,
          Constants.STRUCTURED_PROPERTIES_ASPECT_NAME,
          Constants.OWNERSHIP_ASPECT_NAME,
          Constants.BROWSE_PATHS_V2_ASPECT_NAME);

  private static final Set<String> FACET_FIELDS = ImmutableSet.of("origin", "platform");
  private static final String ENTITY_NAME = "distribution";
  private final EntityClient _entityClient;

  public DistributionType(final EntityClient entityClient) {
    _entityClient = entityClient;
  }

  @Override
  public Class<DistributionUpdateInput> inputClass() {
    return DistributionUpdateInput.class;
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

  @Override
  public SearchResults search(
      @Nonnull String query,
      @Nullable List<FacetFilterInput> filters,
      int start,
      @Nullable Integer count,
      @Nonnull QueryContext context)
      throws Exception {
    final Map<String, String> facetFilters = ResolverUtils.buildFacetFilters(filters, FACET_FIELDS);
    final SearchResult searchResult =
        _entityClient.search(
            context.getOperationContext().withSearchFlags(flags -> flags.setFulltext(true)),
            "distribution",
            query,
            facetFilters,
            start,
            count);
    return UrnSearchResultsMapper.map(context, searchResult);
  }

  @Override
  public AutoCompleteResults autoComplete(
      @Nonnull String query,
      @Nullable String field,
      @Nullable Filter filters,
      @Nullable Integer limit,
      @Nonnull QueryContext context)
      throws Exception {
    final AutoCompleteResult result =
        _entityClient.autoComplete(
            context.getOperationContext(), "distribution", query, filters, limit);
    return AutoCompleteResultsMapper.map(context, result);
  }

  @Override
  public BrowseResults browse(
      @Nonnull List<String> path,
      @Nullable List<FacetFilterInput> filters,
      int start,
      @Nullable Integer count,
      @Nonnull QueryContext context)
      throws Exception {
    final Map<String, String> facetFilters = ResolverUtils.buildFacetFilters(filters, FACET_FIELDS);
    final String pathStr =
        path.size() > 0 ? BROWSE_PATH_DELIMITER + String.join(BROWSE_PATH_DELIMITER, path) : "";
    final BrowseResult result =
        _entityClient.browse(
            context.getOperationContext().withSearchFlags(flags -> flags.setFulltext(false)),
            "distribution",
            pathStr,
            facetFilters,
            start,
            count);
    return BrowseResultMapper.map(context, result);
  }

  @Override
  public List<BrowsePath> browsePaths(@Nonnull String urn, @Nonnull QueryContext context)
      throws Exception {
    final StringArray result =
        _entityClient.getBrowsePaths(context.getOperationContext(), getUrn(urn));
    return BrowsePathsMapper.map(context, result);
  }

  public Distribution update(
      @Nonnull String urn, @Nonnull DistributionUpdateInput input, @Nonnull QueryContext context)
      throws Exception {

    final CorpuserUrn actor = CorpuserUrn.createFromString(context.getActorUrn());
    final Collection<MetadataChangeProposal> proposals =
        DistributionUpdateInputMapper.map(context, input, actor);
    proposals.forEach(proposal -> proposal.setEntityUrn(UrnUtils.getUrn(urn)));

    try {
      _entityClient.batchIngestProposals(context.getOperationContext(), proposals, false);
    } catch (RemoteInvocationException e) {
      throw new RuntimeException(String.format("Failed to write entity with urn %s", urn), e);
    }

    return load(urn, context).getData();
  }

  private Urn getUrn(final String urnStr) {
    try {
      return Urn.createFromString(urnStr);
    } catch (URISyntaxException e) {
      throw new RuntimeException(String.format("Failed to convert urn string %s into Urn", urnStr));
    }
  }
}
