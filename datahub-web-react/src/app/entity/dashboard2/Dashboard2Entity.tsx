import { DashboardFilled, DashboardOutlined } from '@ant-design/icons';
import * as React from 'react';

import { Entity, EntityCapabilityType, IconStyleType, PreviewType } from '@app/entity/Entity';
import { Dashboard2Preview } from '@app/entity/dashboard2/preview/Dashboard2Preview';
import { Dashboard2StatsSummarySubHeader } from '@app/entity/dashboard2/profile/Dashboard2StatsSummarySubHeader';
import { EntityMenuItems } from '@app/entity/shared/EntityDropdown/EntityDropdown';
import { EntityProfile } from '@app/entity/shared/containers/profile/EntityProfile';
import { SidebarAboutSection } from '@app/entity/shared/containers/profile/sidebar/AboutSection/SidebarAboutSection';
import DataProductSection from '@app/entity/shared/containers/profile/sidebar/DataProduct/DataProductSection';
import { SidebarDomainSection } from '@app/entity/shared/containers/profile/sidebar/Domain/SidebarDomainSection';
import { SidebarOwnerSection } from '@app/entity/shared/containers/profile/sidebar/Ownership/sidebar/SidebarOwnerSection';
import { SidebarTagsSection } from '@app/entity/shared/containers/profile/sidebar/SidebarTagsSection';
import SidebarStructuredPropsSection from '@app/entity/shared/containers/profile/sidebar/StructuredProperties/SidebarStructuredPropsSection';
import { getDataForEntityType } from '@app/entity/shared/containers/profile/utils';
import EmbeddedProfile from '@app/entity/shared/embed/EmbeddedProfile';
import { DocumentationTab } from '@app/entity/shared/tabs/Documentation/DocumentationTab';
import { EmbedTab } from '@app/entity/shared/tabs/Embed/EmbedTab';
import { DashboardChartsTab } from '@app/entity/shared/tabs/Entity/DashboardChartsTab';
import { DashboardDatasetsTab } from '@app/entity/shared/tabs/Entity/DashboardDatasetsTab';
import { IncidentTab } from '@app/entity/shared/tabs/Incident/IncidentTab';
import { LineageTab } from '@app/entity/shared/tabs/Lineage/LineageTab';
import { PropertiesTab } from '@app/entity/shared/tabs/Properties/PropertiesTab';
import { GenericEntityProperties } from '@app/entity/shared/types';
import { getDataProduct } from '@app/entity/shared/utils';
import { LOOKER_URN } from '@app/ingest/source/builder/constants';
import { MatchedFieldList } from '@app/search/matches/MatchedFieldList';
import { matchedInputFieldRenderer } from '@app/search/matches/matchedInputFieldRenderer';
import { capitalizeFirstLetterOnly } from '@app/shared/textUtil';

import { GetDashboardQuery, useGetDashboardQuery, useUpdateDashboardMutation } from '@graphql/dashboard.generated';
import {Dashboard, Dashboard2, EntityType, LineageDirection, OwnershipType, SearchResult} from '@types';



/**
 * Definition of the DataHub Dashboard2 entity.
 */
export class Dashboard2Entity implements Entity<Dashboard2> {
    type: EntityType = EntityType.Dashboard2;

    icon = (fontSize: number, styleType: IconStyleType, color?: string) => {
        if (styleType === IconStyleType.TAB_VIEW) {
            return <DashboardOutlined style={{ fontSize, color }} />;
        }

        if (styleType === IconStyleType.HIGHLIGHT) {
            return <DashboardFilled style={{ fontSize, color: color || 'rgb(144 163 236)' }} />;
        }

        if (styleType === IconStyleType.SVG) {
            return (
                <path d="M924.8 385.6a446.7 446.7 0 00-96-142.4 446.7 446.7 0 00-142.4-96C631.1 123.8 572.5 112 512 112s-119.1 11.8-174.4 35.2a446.7 446.7 0 00-142.4 96 446.7 446.7 0 00-96 142.4C75.8 440.9 64 499.5 64 560c0 132.7 58.3 257.7 159.9 343.1l1.7 1.4c5.8 4.8 13.1 7.5 20.6 7.5h531.7c7.5 0 14.8-2.7 20.6-7.5l1.7-1.4C901.7 817.7 960 692.7 960 560c0-60.5-11.9-119.1-35.2-174.4zM761.4 836H262.6A371.12 371.12 0 01140 560c0-99.4 38.7-192.8 109-263 70.3-70.3 163.7-109 263-109 99.4 0 192.8 38.7 263 109 70.3 70.3 109 163.7 109 263 0 105.6-44.5 205.5-122.6 276zM623.5 421.5a8.03 8.03 0 00-11.3 0L527.7 506c-18.7-5-39.4-.2-54.1 14.5a55.95 55.95 0 000 79.2 55.95 55.95 0 0079.2 0 55.87 55.87 0 0014.5-54.1l84.5-84.5c3.1-3.1 3.1-8.2 0-11.3l-28.3-28.3zM490 320h44c4.4 0 8-3.6 8-8v-80c0-4.4-3.6-8-8-8h-44c-4.4 0-8 3.6-8 8v80c0 4.4 3.6 8 8 8zm260 218v44c0 4.4 3.6 8 8 8h80c4.4 0 8-3.6 8-8v-44c0-4.4-3.6-8-8-8h-80c-4.4 0-8 3.6-8 8zm12.7-197.2l-31.1-31.1a8.03 8.03 0 00-11.3 0l-56.6 56.6a8.03 8.03 0 000 11.3l31.1 31.1c3.1 3.1 8.2 3.1 11.3 0l56.6-56.6c3.1-3.1 3.1-8.2 0-11.3zm-458.6-31.1a8.03 8.03 0 00-11.3 0l-31.1 31.1a8.03 8.03 0 000 11.3l56.6 56.6c3.1 3.1 8.2 3.1 11.3 0l31.1-31.1c3.1-3.1 3.1-8.2 0-11.3l-56.6-56.6zM262 530h-80c-4.4 0-8 3.6-8 8v44c0 4.4 3.6 8 8 8h80c4.4 0 8-3.6 8-8v-44c0-4.4-3.6-8-8-8z" />
            );
        }

        return (
            <DashboardOutlined
                style={{
                    fontSize,
                    color: color || '#BFBFBF',
                }}
            />
        );
    };

    isSearchEnabled = () => true;

    isBrowseEnabled = () => true;

    isLineageEnabled = () => true;

    getAutoCompleteFieldName = () => 'title';

    getPathName = () => 'dashboard2';

    getEntityName = () => 'Dashboard2';

    getCollectionName = () => 'Dashboards2';

    useEntityQuery = useGetDashboardQuery;

    getSidebarSections = () => [
        {
            component: SidebarAboutSection,
        },
        {
            component: SidebarOwnerSection,
            properties: {
                defaultOwnerType: OwnershipType.TechnicalOwner,
            },
        },
        {
            component: SidebarTagsSection,
            properties: {
                hasTags: true,
                hasTerms: true,
            },
        },
        {
            component: SidebarDomainSection,
        },
        {
            component: DataProductSection,
        },
        {
            component: SidebarStructuredPropsSection,
        },
    ];

    renderProfile = (urn: string) => (
        <EntityProfile
            urn={urn}
            entityType={EntityType.Dashboard2}
            useEntityQuery={this.useEntityQuery}
            useUpdateQuery={useUpdateDashboardMutation}
            getOverrideProperties={this.getOverridePropertiesFromEntity}
            headerDropdownItems={new Set([EntityMenuItems.UPDATE_DEPRECATION, EntityMenuItems.RAISE_INCIDENT])}
            subHeader={{
                component: Dashboard2StatsSummarySubHeader,
            }}
            tabs={[
                {
                    name: 'Lineage',
                    component: LineageTab,
                    properties: {
                        defaultDirection: LineageDirection.Upstream,
                    },
                }
            ]}
            sidebarSections={this.getSidebarSections()}
        />
    );

    getOverridePropertiesFromEntity = (dashboard2?: Dashboard2 | null): GenericEntityProperties => {
        // TODO: Get rid of this once we have correctly formed platform coming back.
        const name = dashboard2?.info?.name;
        return {
            name
        };
    };

    renderPreview = (_: PreviewType, data: Dashboard2) => {
        const genericProperties = this.getGenericEntityProperties(data);
        return (
            <Dashboard2Preview
                urn={data.urn}
                name={data.info?.name}
                description={data.info?.description}
                dataProduct={getDataProduct(genericProperties?.dataProduct)}
            />
        );
    };

    renderSearch = (result: SearchResult) => {
        const data = result.entity as Dashboard2;
        const genericProperties = this.getGenericEntityProperties(data);

        return (
            <Dashboard2Preview
                urn={data.urn}
                name={data.info?.name}
                platformInstanceId={data.dataPlatformInstance?.instanceId}
                description={data.info?.description}
                dataProduct={getDataProduct(genericProperties?.dataProduct)}
            />
        );
    };

    getLineageVizConfig = (entity: Dashboard2) => {
        return {
            urn: entity.urn,
            name: entity.info?.name || entity.urn,
            type: EntityType.Dashboard2,
        };
    };

    displayName = (data: Dashboard2) => {
        return data.info?.name || data.urn;
    };

    getGenericEntityProperties = (data: Dashboard2) => {
        return getDataForEntityType({
            data,
            entityType: this.type,
            getOverrideProperties: this.getOverridePropertiesFromEntity,
        });
    };

    supportedCapabilities = () => {
        return new Set([
            EntityCapabilityType.DATA_PRODUCTS,
        ]);
    };

    getGraphName = () => this.getPathName();

    renderEmbeddedProfile = (urn: string) => (
        <EmbeddedProfile
            urn={urn}
            entityType={EntityType.Dashboard2}
            useEntityQuery={this.useEntityQuery}
            getOverrideProperties={this.getOverridePropertiesFromEntity}
        />
    );
}

