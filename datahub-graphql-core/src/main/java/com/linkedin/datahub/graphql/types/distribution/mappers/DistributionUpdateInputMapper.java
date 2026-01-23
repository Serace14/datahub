package com.linkedin.datahub.graphql.types.distribution.mappers;

import static com.linkedin.metadata.Constants.*;

import com.linkedin.common.AuditStamp;
import com.linkedin.common.urn.Urn;
import com.linkedin.data.template.SetMode;
import com.linkedin.datahub.graphql.QueryContext;
import com.linkedin.datahub.graphql.generated.DistributionUpdateInput;
import com.linkedin.datahub.graphql.types.common.mappers.util.UpdateMappingHelper;
import com.linkedin.datahub.graphql.types.mappers.InputModelMapper;
import com.linkedin.mxe.MetadataChangeProposal;
import java.util.ArrayList;
import java.util.Collection;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

public class DistributionUpdateInputMapper
    implements InputModelMapper<DistributionUpdateInput, Collection<MetadataChangeProposal>, Urn> {
  public static final DistributionUpdateInputMapper INSTANCE = new DistributionUpdateInputMapper();

  public static Collection<MetadataChangeProposal> map(
      @Nullable final QueryContext context,
      @Nonnull final DistributionUpdateInput distributionUpdateInput,
      @Nonnull final Urn actor) {
    return INSTANCE.apply(context, distributionUpdateInput, actor);
  }

  @Override
  public Collection<MetadataChangeProposal> apply(
      @Nullable final QueryContext context,
      @Nonnull final DistributionUpdateInput distributionUpdateInput,
      @Nonnull final Urn actor) {

    final Collection<MetadataChangeProposal> proposals = new ArrayList<>(3);
    final UpdateMappingHelper updateMappingHelper =
        new UpdateMappingHelper(DISTRIBUTION_ENTITY_NAME);
    final AuditStamp auditStamp = new AuditStamp();
    auditStamp.setActor(actor, SetMode.IGNORE_NULL);
    auditStamp.setTime(System.currentTimeMillis());

    return proposals;
  }
}
