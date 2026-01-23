import React from 'react';

import { useBaseEntity } from '@app/entity/shared/EntityContext';
import { CatalogRecordStatsSummary } from '@app/entityV2/catalogRecord/shared/CatalogRecordStatsSummary';
import { useEntityRegistry } from '@app/useEntityRegistry';

import { GetCatalogRecordQuery } from '@graphql/catalogRecord.generated';
import { DatasetStatsSummary as CatalogRecordStatsSummaryObj, EntityType } from '@types';

export const CatalogRecordStatsSummarySubHeader = () => {
    const result = useBaseEntity<GetCatalogRecordQuery>();
    const catalogRecord = result?.catalogRecord;

    const maybeStatsSummary = catalogRecord?.statsSummary as CatalogRecordStatsSummaryObj;

    const latestFullTableProfile = catalogRecord?.latestFullTableProfile?.[0];
    const latestPartitionProfile = catalogRecord?.latestPartitionProfile?.[0];

    const maybeLastProfile = latestFullTableProfile || latestPartitionProfile || undefined;

    const maybeLastOperation = catalogRecord?.operations && catalogRecord.operations.length ? catalogRecord.operations[0] : undefined;

    const rowCount = maybeLastProfile?.rowCount;
    const columnCount = maybeLastProfile?.columnCount;
    const sizeInBytes = maybeLastProfile?.sizeInBytes;
    const totalSqlQueries = catalogRecord?.usageStats?.aggregations?.totalSqlQueries;
    const queryCountLast30Days = maybeStatsSummary?.queryCountLast30Days;
    const uniqueUserCountLast30Days = maybeStatsSummary?.uniqueUserCountLast30Days;

    const lastUpdatedMs = maybeLastOperation?.lastUpdatedTimestamp;

    const entityRegistry = useEntityRegistry();
    const platformName = catalogRecord?.platform && entityRegistry.getDisplayName(EntityType.DataPlatform, catalogRecord?.platform);
    const platformLogoUrl = catalogRecord?.platform?.properties?.logoUrl;

    return (
        <CatalogRecordStatsSummary
            rowCount={rowCount}
            columnCount={columnCount}
            sizeInBytes={sizeInBytes}
            totalSqlQueries={totalSqlQueries}
            queryCountLast30Days={queryCountLast30Days}
            uniqueUserCountLast30Days={uniqueUserCountLast30Days}
            lastUpdatedMs={lastUpdatedMs}
            platformName={platformName}
            platformLogoUrl={platformLogoUrl}
            subTypes={catalogRecord?.subTypes?.typeNames || undefined}
        />
    );
};
