import React from 'react';

import { Dashboard2StatsSummary } from '@app/entity/dashboard2/shared/Dashboard2StatsSummary';
import { useBaseEntity } from '@app/entity/shared/EntityContext';

import { GetDashboardQuery } from '@graphql/dashboard.generated';
import { DashboardStatsSummary as DashboardStatsSummaryObj } from '@types';

export const Dashboard2StatsSummarySubHeader = () => {
    const result = useBaseEntity<GetDashboardQuery>();
    const dashboard = result?.dashboard;

    return (
        <Dashboard2StatsSummary
        />
    );
};
