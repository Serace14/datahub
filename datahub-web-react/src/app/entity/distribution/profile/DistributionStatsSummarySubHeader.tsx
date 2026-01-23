import React from 'react';

import { DistributionStatsSummary } from '@app/entity/distribution/shared/DistributionStatsSummary';
import { useBaseEntity } from '@app/entity/shared/EntityContext';

import { GetDistributionQuery } from '@graphql/distribution.generated';
import { DistributionStatsSummary as DistributionStatsSummaryObj } from '@types';

export const DistributionStatsSummarySubHeader = () => {
    const result = useBaseEntity<GetDistributionQuery>();
    const distribution = result?.distribution;
    const maybeStatsSummary = distribution?.statsSummary as DistributionStatsSummaryObj;
    const chartCount = distribution?.charts?.total;
    const viewCount = maybeStatsSummary?.viewCount;
    const uniqueUserCountLast30Days = maybeStatsSummary?.uniqueUserCountLast30Days;
    const lastUpdatedMs = distribution?.properties?.lastModified?.time;
    const createdMs = distribution?.properties?.created?.time;

    return (
        <DistributionStatsSummary
            chartCount={chartCount}
            viewCount={viewCount}
            uniqueUserCountLast30Days={uniqueUserCountLast30Days}
            lastUpdatedMs={lastUpdatedMs}
            createdMs={createdMs}
        />
    );
};
