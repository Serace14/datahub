import React from 'react';

import { IconStyleType } from '@app/entity/Entity';
import { DashboardStatsSummary as DashboardStatsSummaryView } from '@app/entity/dashboard/shared/DashboardStatsSummary';
import DefaultPreviewCard from '@app/preview/DefaultPreviewCard';
import { capitalizeFirstLetterOnly } from '@app/shared/textUtil';
import { useEntityRegistry } from '@app/useEntityRegistry';

import {
    AccessLevel,
    Container,
    DashboardStatsSummary,
    DataProduct,
    Deprecation,
    Domain,
    EntityPath,
    EntityType,
    GlobalTags,
    GlossaryTerms,
    Health,
    Owner,
    ParentContainersResult,
    SearchInsight,
} from '@types';

export const Dashboard2Preview = ({
    urn,
    platformInstanceId,
    name,
    description,
    dataProduct,
}: {
    urn: string;
    platformInstanceId?: string;
    name?: string;
    description?: string | null;
    dataProduct?: DataProduct | null;
}): JSX.Element => {
    const entityRegistry = useEntityRegistry();

    return (
        <DefaultPreviewCard
            url={entityRegistry.getEntityUrl(EntityType.Dashboard2, urn)}
            urn={urn}
            name={name || ''}
            description={description || ''}
            type={'Dashboard2'}
            typeIcon={entityRegistry.getIcon(EntityType.Dashboard2, 14, IconStyleType.ACCENT)}
            platformInstanceId={platformInstanceId}
            dataProduct={dataProduct}
        />
    );
};
