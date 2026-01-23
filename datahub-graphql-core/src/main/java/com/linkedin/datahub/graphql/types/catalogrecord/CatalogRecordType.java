package com.linkedin.datahub.graphql.types.catalogrecord;

import static com.linkedin.datahub.graphql.Constants.BROWSE_PATH_DELIMITER;
import static com.linkedin.metadata.Constants.*;

import com.datahub.authorization.ConjunctivePrivilegeGroup;
import com.datahub.authorization.DisjunctivePrivilegeGroup;
import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableSet;
import com.linkedin.common.urn.CorpuserUrn;
import com.linkedin.common.urn.Urn;
import com.linkedin.common.urn.UrnUtils;
import com.linkedin.data.template.StringArray;
import com.linkedin.datahub.graphql.QueryContext;
import com.linkedin.datahub.graphql.authorization.AuthorizationUtils;
import com.linkedin.datahub.graphql.exception.AuthorizationException;
import com.linkedin.datahub.graphql.generated.*;
import com.linkedin.datahub.graphql.resolvers.ResolverUtils;
import com.linkedin.datahub.graphql.types.BatchMutableType;
import com.linkedin.datahub.graphql.types.BrowsableEntityType;
import com.linkedin.datahub.graphql.types.SearchableEntityType;
import com.linkedin.datahub.graphql.types.catalogrecord.mappers.CatalogRecordMapper;
import com.linkedin.datahub.graphql.types.catalogrecord.mappers.CatalogRecordUpdateInputMapper;
import com.linkedin.datahub.graphql.types.mappers.AutoCompleteResultsMapper;
import com.linkedin.datahub.graphql.types.mappers.BrowsePathsMapper;
import com.linkedin.datahub.graphql.types.mappers.BrowseResultMapper;
import com.linkedin.datahub.graphql.types.mappers.UrnSearchResultsMapper;
import com.linkedin.entity.EntityResponse;
import com.linkedin.entity.client.EntityClient;
import com.linkedin.metadata.Constants;
import com.linkedin.metadata.authorization.PoliciesConfig;
import com.linkedin.metadata.browse.BrowseResult;
import com.linkedin.metadata.query.AutoCompleteResult;
import com.linkedin.metadata.query.filter.Filter;
import com.linkedin.metadata.search.SearchResult;
import com.linkedin.mxe.MetadataChangeProposal;
import com.linkedin.r2.RemoteInvocationException;
import graphql.execution.DataFetcherResult;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

public class CatalogRecordType
    implements SearchableEntityType<CatalogRecord, String>,
        BrowsableEntityType<CatalogRecord, String>,
        BatchMutableType<CatalogRecordUpdateInput, BatchCatalogRecordUpdateInput, CatalogRecord> {

  private static final Set<String> ASPECTS_TO_RESOLVE =
      ImmutableSet.of(
          CATALOGRECORD_KEY_ASPECT_NAME,
          CATALOGRECORD_PROPERTIES_ASPECT_NAME,
          EDITABLE_CATALOGRECORD_PROPERTIES_ASPECT_NAME,
          CATALOGRECORD_DEPRECATION_ASPECT_NAME, // This aspect is deprecated.
          DEPRECATION_ASPECT_NAME,
          CATALOGRECORD_UPSTREAM_LINEAGE_ASPECT_NAME,
          UPSTREAM_LINEAGE_ASPECT_NAME,
          EDITABLE_SCHEMA_METADATA_ASPECT_NAME,
          VIEW_PROPERTIES_ASPECT_NAME,
          OWNERSHIP_ASPECT_NAME,
          INSTITUTIONAL_MEMORY_ASPECT_NAME,
          GLOBAL_TAGS_ASPECT_NAME,
          GLOSSARY_TERMS_ASPECT_NAME,
          STATUS_ASPECT_NAME,
          CONTAINER_ASPECT_NAME,
          DOMAINS_ASPECT_NAME,
          SCHEMA_METADATA_ASPECT_NAME,
          DATA_PLATFORM_INSTANCE_ASPECT_NAME,
          SIBLINGS_ASPECT_NAME,
          EMBED_ASPECT_NAME,
          DATA_PRODUCTS_ASPECT_NAME,
          BROWSE_PATHS_V2_ASPECT_NAME,
          ACCESS_ASPECT_NAME,
          STRUCTURED_PROPERTIES_ASPECT_NAME,
          FORMS_ASPECT_NAME,
          SUB_TYPES_ASPECT_NAME,
          APPLICATION_MEMBERSHIP_ASPECT_NAME,
          VERSION_PROPERTIES_ASPECT_NAME,
          PLATFORM_RESOURCE_ASSOCIATION_ASPECT_NAME);

  private static final Set<String> FACET_FIELDS = ImmutableSet.of("origin", "platform");
  private static final String ENTITY_NAME = "catalogRecord";

  private final EntityClient entityClient;

  public CatalogRecordType(final EntityClient entityClient) {
    this.entityClient = entityClient;
  }

  @Override
  public Class<CatalogRecord> objectClass() {
    return CatalogRecord.class;
  }

  @Override
  public Class<CatalogRecordUpdateInput> inputClass() {
    return CatalogRecordUpdateInput.class;
  }

  @Override
  public Class<BatchCatalogRecordUpdateInput[]> batchInputClass() {
    return BatchCatalogRecordUpdateInput[].class;
  }

  @Override
  public EntityType type() {
    return EntityType.CATALOG_RECORD;
  }

  @Override
  public Function<Entity, String> getKeyProvider() {
    return Entity::getUrn;
  }

  @Override
  public List<DataFetcherResult<CatalogRecord>> batchLoad(
      @Nonnull final List<String> urnStrs, @Nonnull final QueryContext context) {
    try {
      final List<Urn> urns = urnStrs.stream().map(UrnUtils::getUrn).collect(Collectors.toList());

      final Map<Urn, EntityResponse> datasetMap =
          entityClient.batchGetV2(
              context.getOperationContext(),
              Constants.CATALOGRECORD_ENTITY_NAME,
              new HashSet<>(urns),
              ASPECTS_TO_RESOLVE);

      final List<EntityResponse> gmsResults = new ArrayList<>(urnStrs.size());
      for (Urn urn : urns) {
        gmsResults.add(datasetMap.getOrDefault(urn, null));
      }
      return gmsResults.stream()
          .map(
              gmsCatalogRecord ->
                  gmsCatalogRecord == null
                      ? null
                      : DataFetcherResult.<CatalogRecord>newResult()
                          .data(CatalogRecordMapper.map(context, gmsCatalogRecord))
                          .build())
          .collect(Collectors.toList());
    } catch (Exception e) {
      throw new RuntimeException("Failed to batch load CatalogRecords", e);
    }
  }

  @Override
  public SearchResults search(
      @Nonnull String query,
      @Nullable List<FacetFilterInput> filters,
      int start,
      @Nullable Integer count,
      @Nonnull final QueryContext context)
      throws Exception {
    final Map<String, String> facetFilters = ResolverUtils.buildFacetFilters(filters, FACET_FIELDS);
    final SearchResult searchResult =
        entityClient.search(
            context.getOperationContext().withSearchFlags(flags -> flags.setFulltext(true)),
            ENTITY_NAME,
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
      @Nonnull final QueryContext context)
      throws Exception {
    final AutoCompleteResult result =
        entityClient.autoComplete(
            context.getOperationContext(), ENTITY_NAME, query, filters, limit);
    return AutoCompleteResultsMapper.map(context, result);
  }

  @Override
  public BrowseResults browse(
      @Nonnull List<String> path,
      @Nullable List<FacetFilterInput> filters,
      int start,
      @Nullable Integer count,
      @Nonnull final QueryContext context)
      throws Exception {
    final Map<String, String> facetFilters = ResolverUtils.buildFacetFilters(filters, FACET_FIELDS);
    final String pathStr =
        path.size() > 0 ? BROWSE_PATH_DELIMITER + String.join(BROWSE_PATH_DELIMITER, path) : "";
    final BrowseResult result =
        entityClient.browse(
            context.getOperationContext().withSearchFlags(flags -> flags.setFulltext(false)),
            "catalogRecord",
            pathStr,
            facetFilters,
            start,
            count);
    return BrowseResultMapper.map(context, result);
  }

  @Override
  public List<BrowsePath> browsePaths(@Nonnull String urn, @Nonnull final QueryContext context)
      throws Exception {
    final StringArray result =
        entityClient.getBrowsePaths(
            context.getOperationContext(), CatalogRecordUtils.getCatalogRecordUrn(urn));
    return BrowsePathsMapper.map(context, result);
  }

  @Override
  public List<CatalogRecord> batchUpdate(
      @Nonnull BatchCatalogRecordUpdateInput[] input, @Nonnull QueryContext context)
      throws Exception {
    final Urn actor = Urn.createFromString(context.getActorUrn());

    final Collection<MetadataChangeProposal> proposals =
        Arrays.stream(input)
            .map(
                updateInput -> {
                  if (isAuthorized(updateInput.getUrn(), updateInput.getUpdate(), context)) {
                    Collection<MetadataChangeProposal> datasetProposals =
                        CatalogRecordUpdateInputMapper.map(context, updateInput.getUpdate(), actor);
                    datasetProposals.forEach(
                        proposal -> proposal.setEntityUrn(UrnUtils.getUrn(updateInput.getUrn())));
                    return datasetProposals;
                  }
                  throw new AuthorizationException(
                      "Unauthorized to perform this action. Please contact your DataHub administrator.");
                })
            .flatMap(Collection::stream)
            .collect(Collectors.toList());

    final List<String> urns =
        Arrays.stream(input)
            .map(BatchCatalogRecordUpdateInput::getUrn)
            .collect(Collectors.toList());

    try {
      entityClient.batchIngestProposals(context.getOperationContext(), proposals, false);
    } catch (RemoteInvocationException e) {
      throw new RuntimeException(String.format("Failed to write entity with urn %s", urns), e);
    }

    return batchLoad(urns, context).stream()
        .map(DataFetcherResult::getData)
        .collect(Collectors.toList());
  }

  @Override
  public CatalogRecord update(
      @Nonnull String urn, @Nonnull CatalogRecordUpdateInput input, @Nonnull QueryContext context)
      throws Exception {
    if (isAuthorized(urn, input, context)) {
      final CorpuserUrn actor = CorpuserUrn.createFromString(context.getActorUrn());
      final Collection<MetadataChangeProposal> proposals =
          CatalogRecordUpdateInputMapper.map(context, input, actor);
      proposals.forEach(proposal -> proposal.setEntityUrn(UrnUtils.getUrn(urn)));

      try {
        entityClient.batchIngestProposals(context.getOperationContext(), proposals, false);
      } catch (RemoteInvocationException e) {
        throw new RuntimeException(String.format("Failed to write entity with urn %s", urn), e);
      }

      return load(urn, context).getData();
    }
    throw new AuthorizationException(
        "Unauthorized to perform this action. Please contact your DataHub administrator.");
  }

  private boolean isAuthorized(
      @Nonnull String urn,
      @Nonnull CatalogRecordUpdateInput update,
      @Nonnull QueryContext context) {
    // Decide whether the current principal should be allowed to update the CatalogRecord.
    final DisjunctivePrivilegeGroup orPrivilegeGroups = getAuthorizedPrivileges(update);
    return AuthorizationUtils.isAuthorized(
        context, PoliciesConfig.DATASET_PRIVILEGES.getResourceType(), urn, orPrivilegeGroups);
  }

  private DisjunctivePrivilegeGroup getAuthorizedPrivileges(
      final CatalogRecordUpdateInput updateInput) {

    final ConjunctivePrivilegeGroup allPrivilegesGroup =
        new ConjunctivePrivilegeGroup(
            ImmutableList.of(PoliciesConfig.EDIT_ENTITY_PRIVILEGE.getType()));

    List<String> specificPrivileges = new ArrayList<>();
    if (updateInput.getInstitutionalMemory() != null) {
      specificPrivileges.add(PoliciesConfig.EDIT_ENTITY_DOC_LINKS_PRIVILEGE.getType());
    }
    if (updateInput.getOwnership() != null) {
      specificPrivileges.add(PoliciesConfig.EDIT_ENTITY_OWNERS_PRIVILEGE.getType());
    }
    if (updateInput.getDeprecation() != null) {
      specificPrivileges.add(PoliciesConfig.EDIT_ENTITY_STATUS_PRIVILEGE.getType());
    }
    if (updateInput.getEditableProperties() != null) {
      specificPrivileges.add(PoliciesConfig.EDIT_ENTITY_DOCS_PRIVILEGE.getType());
    }
    if (updateInput.getGlobalTags() != null) {
      specificPrivileges.add(PoliciesConfig.EDIT_ENTITY_TAGS_PRIVILEGE.getType());
    }
    if (updateInput.getEditableSchemaMetadata() != null) {
      specificPrivileges.add(PoliciesConfig.EDIT_DATASET_COL_TAGS_PRIVILEGE.getType());
      specificPrivileges.add(PoliciesConfig.EDIT_DATASET_COL_DESCRIPTION_PRIVILEGE.getType());
    }

    final ConjunctivePrivilegeGroup specificPrivilegeGroup =
        new ConjunctivePrivilegeGroup(specificPrivileges);

    // If you either have all entity privileges, or have the specific privileges required, you are
    // authorized.
    return new DisjunctivePrivilegeGroup(
        ImmutableList.of(allPrivilegesGroup, specificPrivilegeGroup));
  }
}
