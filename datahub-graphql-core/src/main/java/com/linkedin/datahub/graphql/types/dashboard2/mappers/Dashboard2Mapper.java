package com.linkedin.datahub.graphql.types.dashboard2.mappers;

import static com.linkedin.datahub.graphql.authorization.AuthorizationUtils.canView;
import static com.linkedin.metadata.Constants.*;

import com.linkedin.common.DataPlatformInstance;
import com.linkedin.common.urn.Urn;
import com.linkedin.data.DataMap;
import com.linkedin.datahub.graphql.QueryContext;
import com.linkedin.datahub.graphql.authorization.AuthorizationUtils;
import com.linkedin.datahub.graphql.generated.Chart;
import com.linkedin.datahub.graphql.generated.Dashboard2;
import com.linkedin.datahub.graphql.generated.Dashboard2Info;
import com.linkedin.datahub.graphql.generated.EntityType;
import com.linkedin.datahub.graphql.types.common.mappers.DataPlatformInstanceAspectMapper;
import com.linkedin.datahub.graphql.types.common.mappers.util.MappingHelper;
import com.linkedin.datahub.graphql.types.common.mappers.util.SystemMetadataUtils;
import com.linkedin.datahub.graphql.types.mappers.ModelMapper;
import com.linkedin.entity.EntityResponse;
import com.linkedin.entity.EnvelopedAspectMap;
import com.linkedin.metadata.key.Dashboard2Key;
import java.util.stream.Collectors;
import javax.annotation.Nonnull;
import javax.annotation.Nullable;

public class Dashboard2Mapper implements ModelMapper<EntityResponse, Dashboard2> {

  public static final Dashboard2Mapper INSTANCE = new Dashboard2Mapper();

  public static Dashboard2 map(
      @Nullable final QueryContext context, @Nonnull final EntityResponse entityResponse) {
    return INSTANCE.apply(context, entityResponse);
  }

  @Override
  public Dashboard2 apply(
      @Nullable final QueryContext context, @Nonnull final EntityResponse entityResponse) {
    final Dashboard2 result = new Dashboard2();
    Urn entityUrn = entityResponse.getUrn();

    result.setUrn(entityUrn.toString());
    result.setType(EntityType.DASHBOARD2);

    EnvelopedAspectMap aspectMap = entityResponse.getAspects();
    Long lastIngested = SystemMetadataUtils.getLastIngestedTime(aspectMap);

    MappingHelper<Dashboard2> mappingHelper = new MappingHelper<>(aspectMap, result);

    mappingHelper.mapToResult(DASHBOARD2_KEY_ASPECT_NAME, this::mapDashboard2Key);
    mappingHelper.mapToResult(
        DASHBOARD2_INFO_ASPECT_NAME,
        (dashboard, dataMap) -> this.mapDashboard2Info(context, dashboard, dataMap, entityUrn));
    mappingHelper.mapToResult(
        DATA_PLATFORM_INSTANCE_ASPECT_NAME,
        (dashboard, dataMap) ->
            dashboard.setDataPlatformInstance(
                DataPlatformInstanceAspectMapper.map(context, new DataPlatformInstance(dataMap))));

    if (context != null && !canView(context.getOperationContext(), entityUrn)) {
      return AuthorizationUtils.restrictEntity(mappingHelper.getResult(), Dashboard2.class);
    } else {
      return mappingHelper.getResult();
    }
  }

  private void mapDashboard2Key(@Nonnull Dashboard2 dashboard, @Nonnull DataMap dataMap) {
    final Dashboard2Key gmsKey = new Dashboard2Key(dataMap);
    dashboard.setDashboardId(gmsKey.getDashboardId());
    dashboard.setTool(gmsKey.getDashboardTool());
  }

  private void mapDashboard2Info(
      @Nonnull QueryContext context,
      @Nonnull Dashboard2 dashboard2,
      @Nonnull DataMap dataMap,
      Urn entityUrn) {
    final com.linkedin.dashboard2.Dashboard2Info gmsDashboardInfo =
        new com.linkedin.dashboard2.Dashboard2Info(dataMap);
    dashboard2.setInfo(mapInfo(context, gmsDashboardInfo, entityUrn));
  }

  private static Dashboard2Info mapInfo(
      @Nullable final QueryContext context,
      final com.linkedin.dashboard2.Dashboard2Info info,
      Urn entityUrn) {
    final Dashboard2Info result = new Dashboard2Info();
    result.setDescription(info.getDescription());
    result.setName(info.getTitle());
    result.setCharts(
        info.getCharts().stream()
            .map(
                urn -> {
                  final Chart chart = new Chart();
                  chart.setUrn(urn.toString());
                  return chart;
                })
            .collect(Collectors.toList()));

    return result;
  }
}
