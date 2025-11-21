import React from 'react';

import { useBaseEntity } from '@app/entity/shared/EntityContext';
import { DistributionStatsSummary } from '@app/entityV2/distribution/shared/DistributionStatsSummary';

import { GetDistributionQuery } from '@graphql/distribution.generated';
import { DistributionStatsSummary as DistributionStatsSummaryObj } from '@types';

export const DistributionStatsSummarySubHeader = () => {
    const result = useBaseEntity<GetDistributionQuery>();
    const distribution = result?.distribution;
    const maybeStatsSummary = distribution?.statsSummary as DistributionStatsSummaryObj;
    const viewCount = maybeStatsSummary?.viewCount;
    const viewCountLast30Days = maybeStatsSummary?.viewCountLast30Days;
    const uniqueUserCountLast30Days = maybeStatsSummary?.uniqueUserCountLast30Days;

    return (
        <DistributionStatsSummary
            viewCount={viewCount}
            viewCountLast30Days={viewCountLast30Days}
            uniqueUserCountLast30Days={uniqueUserCountLast30Days}
        />
    );
};
