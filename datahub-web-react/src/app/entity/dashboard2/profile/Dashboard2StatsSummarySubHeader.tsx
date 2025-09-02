import React from 'react';

import { Dashboard2StatsSummary } from '@app/entity/dashboard2/shared/Dashboard2StatsSummary';
import { useBaseEntity } from '@app/entity/shared/EntityContext';

import { GetDashboard2Query } from '@graphql/dashboard2.generated';
import { DashboardStatsSummary as DashboardStatsSummaryObj } from '@types';

export const Dashboard2StatsSummarySubHeader = () => {
    const result = useBaseEntity<GetDashboard2Query>();
    const dashboard = result?.dashboard2;

    return (
        <Dashboard2StatsSummary
        />
    );
};
