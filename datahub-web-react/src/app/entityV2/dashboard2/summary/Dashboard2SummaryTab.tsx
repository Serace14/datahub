import { Divider } from 'antd';
import React from 'react';
import styled from 'styled-components';

import { useEntityData } from '@app/entity/shared/EntityContext';
import EmbedPreview from '@app/entityV2/chart/summary/EmbedPreview';
import Dashboard2SummaryOverview from '@app/entityV2/dashboard2/summary/Dashboard2SummaryOverview';
import { SummaryTabWrapper } from '@app/entityV2/shared/summary/HeaderComponents';
import SummaryAboutSection from '@app/entityV2/shared/summary/SummaryAboutSection';

const StyledDivider = styled(Divider)`
    width: 100%;
    border-top-width: 2px;
    margin: 10px 0;
`;

export default function Dashboard2SummaryTab(): JSX.Element | null {
    const { entityData } = useEntityData();

    return (
        <SummaryTabWrapper>
            <Dashboard2SummaryOverview />
            <StyledDivider />
            <SummaryAboutSection />

            {entityData?.embed?.renderUrl && (
                <>
                    <StyledDivider />
                    <EmbedPreview embedUrl={entityData?.embed?.renderUrl} />
                </>
            )}
        </SummaryTabWrapper>
    );
}
