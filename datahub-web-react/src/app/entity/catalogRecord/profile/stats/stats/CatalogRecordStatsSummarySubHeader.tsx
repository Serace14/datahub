import React from 'react';

import { CatalogRecordStatsSummary } from '@app/entity/catalogRecord/shared/CatalogRecordStatsSummary';
import { getLastUpdatedMs } from '@app/entity/catalogRecord/shared/utils';
import { useBaseEntity } from '@app/entity/shared/EntityContext';

import { GetCatalogRecordQuery } from '@graphql/catalogRecord.generated';
import { DatasetStatsSummary as DatasetStatsSummaryObj } from '@types';

export const CatalogRecordStatsSummarySubHeader = ({ properties }: { properties?: any }) => {
    const result = useBaseEntity<GetCatalogRecordQuery>();
    const dataset = result?.catalogRecord;

    const maybeStatsSummary = dataset?.statsSummary as DatasetStatsSummaryObj;

    const maybeLastProfile =
        dataset?.datasetProfiles && dataset.datasetProfiles.length ? dataset.datasetProfiles[0] : undefined;

    const rowCount = maybeLastProfile?.rowCount;
    const columnCount = maybeLastProfile?.columnCount;
    const sizeInBytes = maybeLastProfile?.sizeInBytes;
    const totalSqlQueries = dataset?.usageStats?.aggregations?.totalSqlQueries;
    const queryCountLast30Days = maybeStatsSummary?.queryCountLast30Days;
    const uniqueUserCountLast30Days = maybeStatsSummary?.uniqueUserCountLast30Days;
    const lastUpdatedMs = getLastUpdatedMs(dataset?.properties, dataset?.operations);

    return (
        <CatalogRecordStatsSummary
            rowCount={rowCount}
            columnCount={columnCount}
            sizeInBytes={sizeInBytes}
            totalSqlQueries={totalSqlQueries}
            queryCountLast30Days={queryCountLast30Days}
            uniqueUserCountLast30Days={uniqueUserCountLast30Days}
            lastUpdatedMs={lastUpdatedMs}
            shouldWrap={properties?.shouldWrap}
        />
    );
};
