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

export const DistributionPreview = ({
    urn,
    id,
    name,
    description,
    owners,
}: {
    urn: string;
    id: string;
    name?: string;
    description?: string | null;
    owners?: Array<Owner> | null;
}): JSX.Element => {
    const entityRegistry = useEntityRegistry();

    return (
        <DefaultPreviewCard
            url={entityRegistry.getEntityUrl(EntityType.Dashboard, urn)}
            name={name || ''}
            urn={urn}
            description={description || ''}
            type={capitalizeFirstLetterOnly(subtype) || 'Distribution'}
            id={id}
            owners={owners}
        />
    );
};
