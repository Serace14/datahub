import React from 'react';

import { GenericEntityProperties } from '@app/entity/shared/types';
import { IconStyleType, PreviewType } from '@app/entityV2/Entity';
import { DistributionStatsSummary as DistributionStatsSummaryView } from '@app/entityV2/distribution/shared/DistributionStatsSummary';
import DefaultPreviewCard from '@app/previewV2/DefaultPreviewCard';
import { useEntityRegistry } from '@app/useEntityRegistry';
import { summaryHasStats } from '@app/entityV2/shared/utils';

import {
    BrowsePathV2,
    DistributionStatsSummary,
    EntityPath,
    EntityType,
    Owner,
} from '@types';

export const DistributionPreview = ({
    urn,
    data,
    name,
    description,
    owners,
    statsSummary,
    degree,
    paths,
    isOutputPort,
    previewType,
    browsePaths,
}: {
    urn: string;
    data: GenericEntityProperties | null;
    name?: string;
    description?: string | null;
    owners?: Array<Owner> | null;
    statsSummary?: DistributionStatsSummary | null;
    degree?: number;
    paths?: EntityPath[];
    isOutputPort?: boolean;
    previewType?: PreviewType;
    browsePaths?: BrowsePathV2;
}): JSX.Element => {
    const entityRegistry = useEntityRegistry();
    const hasStats = summaryHasStats(statsSummary);

    return (
        <DefaultPreviewCard
            url={entityRegistry.getEntityUrl(EntityType.Distribution, urn)}
            name={name || ''}
            urn={urn}
            data={data}
            description={description || ''}
            entityType={EntityType.Distribution}
            typeIcon={entityRegistry.getIcon(EntityType.Distribution, 14, IconStyleType.ACCENT)}
            owners={owners}
            topUsers={statsSummary?.topUsersLast30Days}
            subHeader={
                hasStats && (
                    <DistributionStatsSummaryView
                        viewCount={statsSummary?.viewCount}
                        viewCountLast30Days={statsSummary?.viewCountLast30Days}
                        uniqueUserCountLast30Days={statsSummary?.uniqueUserCountLast30Days}
                    />
                )
            }
            degree={degree}
            paths={paths}
            isOutputPort={isOutputPort}
            statsSummary={statsSummary}
            previewType={previewType}
            browsePaths={browsePaths}
        />
    );
};
