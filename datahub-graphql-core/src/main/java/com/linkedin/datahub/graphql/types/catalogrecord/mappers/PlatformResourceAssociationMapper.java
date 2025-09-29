package com.linkedin.datahub.graphql.types.catalogrecord.mappers;

import static com.linkedin.datahub.graphql.authorization.AuthorizationUtils.canView;

import com.linkedin.datahub.graphql.QueryContext;
import com.linkedin.datahub.graphql.generated.EntityType;
import com.linkedin.datahub.graphql.generated.PlatformResource;
import com.linkedin.datahub.graphql.generated.PlatformResourceAssociation;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

/**
 * Maps Pegasus {@link RecordTemplate} objects to objects conforming to the GQL schema.
 *
 * <p>To be replaced by auto-generated mappers implementations
 */
public class PlatformResourceAssociationMapper {

  public static final com.linkedin.datahub.graphql.types.catalogrecord.mappers
          .PlatformResourceAssociationMapper
      INSTANCE =
          new com.linkedin.datahub.graphql.types.catalogrecord.mappers
              .PlatformResourceAssociationMapper();

  public static PlatformResourceAssociation map(
      @Nullable final QueryContext context,
      @Nonnull final com.linkedin.catalogrecord.PlatformResources resources,
      @Nonnull final String entityUrn) {
    return INSTANCE.apply(context, resources, entityUrn);
  }

  public PlatformResourceAssociation apply(
      @Nullable final QueryContext context,
      @Nonnull final com.linkedin.catalogrecord.PlatformResources resources,
      @Nonnull final String entityUrn) {
    if (resources.getResources().size() > 0
        && (context == null
            || canView(context.getOperationContext(), resources.getResources().get(0)))) {
      PlatformResourceAssociation association = new PlatformResourceAssociation();
      association.setResource(
          PlatformResource.builder()
              .setType(EntityType.PLATFORM_RESOURCE)
              .setUrn(resources.getResources().get(0).toString())
              .build());
      association.setAssociatedUrn(entityUrn);
      return association;
    }
    return null;
  }
}
