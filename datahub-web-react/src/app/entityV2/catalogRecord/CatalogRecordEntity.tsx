import {
    CheckCircleOutlined,
    CodeOutlined,
    ConsoleSqlOutlined,
    EyeOutlined,
    FileOutlined,
    FundOutlined,
    LayoutOutlined,
    PartitionOutlined,
    UnlockOutlined,
    UnorderedListOutlined,
    WarningOutlined,
} from '@ant-design/icons';
import ViewComfyOutlinedIcon from '@mui/icons-material/ViewComfyOutlined';
import { Columns, ListBullets, TreeStructure } from '@phosphor-icons/react';
import * as React from 'react';

import { GenericEntityProperties } from '@app/entity/shared/types';
import { Entity, EntityCapabilityType, IconStyleType, PreviewType } from '@app/entityV2/Entity';
import { Preview } from '@app/entityV2/catalogRecord/preview/Preview';
import { OperationsTab } from '@app/entityV2/catalogRecord/profile/OperationsTab';
import { CatalogRecordStatsSummarySubHeader } from '@app/entityV2/catalogRecord/profile/stats/stats/CatalogRecordStatsSummarySubHeader';
import { EntityMenuItems } from '@app/entityV2/shared/EntityDropdown/EntityMenuActions';
import { SubType, TYPE_ICON_CLASS_NAME } from '@app/entityV2/shared/components/subtypes';
import { EntityProfile } from '@app/entityV2/shared/containers/profile/EntityProfile';
import { SidebarAboutSection } from '@app/entityV2/shared/containers/profile/sidebar/AboutSection/SidebarAboutSection';
import { SidebarApplicationSection } from '@app/entityV2/shared/containers/profile/sidebar/Applications/SidebarApplicationSection';
import DataProductSection from '@app/entityV2/shared/containers/profile/sidebar/DataProduct/DataProductSection';
import SidebarDatasetHeaderSection from '@app/entityV2/shared/containers/profile/sidebar/Dataset/Header/SidebarDatasetHeaderSection';
import { SidebarDomainSection } from '@app/entityV2/shared/containers/profile/sidebar/Domain/SidebarDomainSection';
import SidebarLineageSection from '@app/entityV2/shared/containers/profile/sidebar/Lineage/SidebarLineageSection';
import { SidebarOwnerSection } from '@app/entityV2/shared/containers/profile/sidebar/Ownership/sidebar/SidebarOwnerSection';
import SidebarQueryOperationsSection from '@app/entityV2/shared/containers/profile/sidebar/Query/SidebarQueryOperationsSection';
import SidebarEntityHeader from '@app/entityV2/shared/containers/profile/sidebar/SidebarEntityHeader';
import { SidebarGlossaryTermsSection } from '@app/entityV2/shared/containers/profile/sidebar/SidebarGlossaryTermsSection';
import { SidebarDatasetViewDefinitionSection } from '@app/entityV2/shared/containers/profile/sidebar/SidebarLogicSection';
import { SidebarSiblingsSection } from '@app/entityV2/shared/containers/profile/sidebar/SidebarSiblingsSection';
import { SidebarTagsSection } from '@app/entityV2/shared/containers/profile/sidebar/SidebarTagsSection';
import StatusSection from '@app/entityV2/shared/containers/profile/sidebar/shared/StatusSection';
import { getDataForEntityType } from '@app/entityV2/shared/containers/profile/utils';
import EmbeddedProfile from '@app/entityV2/shared/embed/EmbeddedProfile';
import SidebarNotesSection from '@app/entityV2/shared/sidebarSection/SidebarNotesSection';
import SidebarStructuredProperties from '@app/entityV2/shared/sidebarSection/SidebarStructuredProperties';
import AccessManagement from '@app/entityV2/shared/tabs/Dataset/AccessManagement/AccessManagement';
import QueriesTab from '@app/entityV2/shared/tabs/Dataset/Queries/QueriesTab';
import { SchemaTab } from '@app/entityV2/shared/tabs/Dataset/Schema/SchemaTab';
import StatsTab from '@app/entityV2/shared/tabs/Dataset/Stats/StatsTab';
import { AcrylValidationsTab } from '@app/entityV2/shared/tabs/Dataset/Validations/AcrylValidationsTab';
import ViewDefinitionTab from '@app/entityV2/shared/tabs/Dataset/View/ViewDefinitionTab';
import { DocumentationTab } from '@app/entityV2/shared/tabs/Documentation/DocumentationTab';
import { EmbedTab } from '@app/entityV2/shared/tabs/Embed/EmbedTab';
import ColumnTabNameHeader from '@app/entityV2/shared/tabs/Entity/ColumnTabNameHeader';
import TabNameWithCount from '@app/entityV2/shared/tabs/Entity/TabNameWithCount';
import { IncidentTab } from '@app/entityV2/shared/tabs/Incident/IncidentTab';
import { LineageTab } from '@app/entityV2/shared/tabs/Lineage/LineageTab';
import { PropertiesTab } from '@app/entityV2/shared/tabs/Properties/PropertiesTab';
import {
    SidebarTitleActionType,
    getDataProduct,
    getDatasetLastUpdatedMs,
    isOutputPort,
} from '@app/entityV2/shared/utils';
import { DBT_URN } from '@app/ingest/source/builder/constants';
import { MatchedFieldList } from '@app/searchV2/matches/MatchedFieldList';
import { matchedFieldPathsRenderer } from '@app/searchV2/matches/matchedFieldPathsRenderer';
import { capitalizeFirstLetterOnly } from '@app/shared/textUtil';
import { useAppConfig } from '@app/useAppConfig';
import { GovernanceTab } from '@src/app/entity/shared/tabs/Dataset/Governance/GovernanceTab';

import { GetCatalogRecordQuery, useGetCatalogRecordQuery, useUpdateCatalogRecordMutation } from '@graphql/catalogRecord.generated';
import { CatalogRecord, DatasetProperties, EntityType, FeatureFlagsConfig, SearchResult } from '@types';

import GovernMenuIcon from '@images/governMenuIcon.svg?react';

const SUBTYPES = {
    VIEW: 'view',
};

const headerDropdownItems = new Set([
    EntityMenuItems.EXTERNAL_URL,
    EntityMenuItems.SHARE,
    EntityMenuItems.UPDATE_DEPRECATION,
    EntityMenuItems.RAISE_INCIDENT,
    EntityMenuItems.ANNOUNCE,
    EntityMenuItems.LINK_VERSION,
]);

/**
 * Definition of the DataHub CatalogRecord entity.
 */
export class CatalogRecordEntity implements Entity<CatalogRecord> {
    type: EntityType = EntityType.CatalogRecord;

    icon = (fontSize?: number, styleType?: IconStyleType, color?: string) => {
        if (styleType === IconStyleType.TAB_VIEW) {
            return <ViewComfyOutlinedIcon className={TYPE_ICON_CLASS_NAME} style={{ fontSize, color }} />;
        }

        if (styleType === IconStyleType.HIGHLIGHT) {
            return (
                <ViewComfyOutlinedIcon
                    className={TYPE_ICON_CLASS_NAME}
                    style={{ fontSize, color: color || '#B37FEB' }}
                />
            );
        }

        if (styleType === IconStyleType.SVG) {
            return <path d="M2 4v16h20V4zm2 2h16v5H4zm0 12v-5h4v5zm6 0v-5h10v5z" />;
        }

        return (
            <ViewComfyOutlinedIcon
                className={TYPE_ICON_CLASS_NAME}
                style={{
                    fontSize,
                    color: color || '#BFBFBF',
                }}
            />
        );
    };

    isSearchEnabled = () => true;

    appconfig = useAppConfig;

    isBrowseEnabled = () => true;

    isLineageEnabled = () => true;

    getAutoCompleteFieldName = () => 'name';

    getGraphName = () => 'catalogRecord';

    getPathName = () => this.getGraphName();

    getEntityName = () => 'CatalogRecord';

    getCollectionName = () => 'CatalogRecords';

    useEntityQuery = useGetCatalogRecordQuery;

    renderProfile = (urn: string) => (
        <EntityProfile
            urn={urn}
            entityType={EntityType.CatalogRecord}
            useEntityQuery={useGetCatalogRecordQuery}
            useUpdateQuery={useUpdateCatalogRecordMutation}
            getOverrideProperties={this.getOverridePropertiesFromEntity}
            headerDropdownItems={headerDropdownItems}
            subHeader={{
                component: CatalogRecordStatsSummarySubHeader,
            }}
            tabs={[
                {
                    name: 'Columns',
                    component: SchemaTab,
                    icon: LayoutOutlined,
                    getDynamicName: ColumnTabNameHeader,
                },
                {
                    name: 'View Definition',
                    component: ViewDefinitionTab,
                    icon: CodeOutlined,
                    display: {
                        visible: (_, catalogRecord: GetCatalogRecordQuery) =>
                            !!catalogRecord?.catalogRecord?.viewProperties?.logic ||
                            !!catalogRecord?.catalogRecord?.subTypes?.typeNames
                                ?.map((t) => t.toLocaleLowerCase())
                                .includes(SUBTYPES.VIEW.toLocaleLowerCase()),
                        enabled: (_, catalogRecord: GetCatalogRecordQuery) => !!catalogRecord?.catalogRecord?.viewProperties?.logic,
                    },
                },
                {
                    name: 'Documentation',
                    component: DocumentationTab,
                    icon: FileOutlined,
                },
                {
                    name: 'Preview',
                    component: EmbedTab,
                    icon: EyeOutlined,
                    display: {
                        visible: (_, catalogRecord: GetCatalogRecordQuery) => !!catalogRecord?.catalogRecord?.embed?.renderUrl,
                        enabled: (_, catalogRecord: GetCatalogRecordQuery) => !!catalogRecord?.catalogRecord?.embed?.renderUrl,
                    },
                },
                {
                    name: 'Lineage',
                    component: LineageTab,
                    icon: PartitionOutlined,
                },
                {
                    name: 'Access',
                    component: AccessManagement,
                    icon: UnlockOutlined,
                    display: {
                        visible: (_, _1) => this.appconfig().config.featureFlags.showAccessManagement,
                        enabled: (_, _2) => true,
                    },
                },
                {
                    name: 'Properties',
                    component: PropertiesTab,
                    icon: UnorderedListOutlined,
                    getDynamicName: (_, catalogRecord: GetCatalogRecordQuery, loading) => {
                        const customPropertiesCount = catalogRecord?.catalogRecord?.properties?.customProperties?.length || 0;
                        const structuredPropertiesCount =
                            catalogRecord?.catalogRecord?.structuredProperties?.properties?.length || 0;
                        const propertiesCount = customPropertiesCount + structuredPropertiesCount;
                        return <TabNameWithCount name="Properties" count={propertiesCount} loading={loading} />;
                    },
                },
                {
                    name: 'Queries',
                    component: QueriesTab,
                    icon: ConsoleSqlOutlined,
                    display: {
                        visible: (_, _1) => true,
                        enabled: (_, _2) => true,
                    },
                },
                {
                    name: 'Stats',
                    component: StatsTab,
                    icon: FundOutlined,
                    display: {
                        visible: (_, _1) => true,
                        enabled: (_, catalogRecord: GetCatalogRecordQuery) =>
                            (catalogRecord?.catalogRecord?.latestFullTableProfile?.length || 0) > 0 ||
                            (catalogRecord?.catalogRecord?.latestPartitionProfile?.length || 0) > 0 ||
                            (catalogRecord?.catalogRecord?.usageStats?.buckets?.length || 0) > 0 ||
                            (catalogRecord?.catalogRecord?.operations?.length || 0) > 0,
                    },
                },
                {
                    name: 'Quality',
                    component: AcrylValidationsTab, // Use SaaS specific Validations Tab.
                    icon: CheckCircleOutlined,
                },
                {
                    name: 'Governance',
                    icon: () => (
                        <span
                            style={{
                                marginRight: 6,
                                verticalAlign: '-0.2em',
                            }}
                        >
                            <GovernMenuIcon width={16} height={16} fill="currentColor" />
                        </span>
                    ),
                    component: GovernanceTab,
                },
                {
                    name: 'Runs', // TODO: Rename this to DatasetRunsTab.
                    component: OperationsTab,
                    display: {
                        visible: (_, catalogRecord: GetCatalogRecordQuery) => {
                            return (catalogRecord?.catalogRecord?.runs?.total || 0) > 0;
                        },
                        enabled: (_, catalogRecord: GetCatalogRecordQuery) => {
                            return (catalogRecord?.catalogRecord?.runs?.total || 0) > 0;
                        },
                    },
                },
                {
                    name: 'Incidents',
                    icon: WarningOutlined,
                    component: IncidentTab,
                    getDynamicName: (_, catalogRecord, loading) => {
                        const activeIncidentCount = catalogRecord?.catalogRecord?.activeIncidents?.total;
                        return <TabNameWithCount name="Incidents" count={activeIncidentCount} loading={loading} />;
                    },
                },
            ]}
            sidebarSections={this.getSidebarSections()}
            sidebarTabs={this.getSidebarTabs()}
        />
    );

    getSidebarSections = () => [
        { component: SidebarEntityHeader },
        { component: SidebarDatasetHeaderSection },
        { component: SidebarAboutSection },
        { component: SidebarNotesSection },
        { component: SidebarLineageSection },
        { component: SidebarOwnerSection },
        { component: SidebarDomainSection },
        { component: SidebarApplicationSection },
        { component: DataProductSection },
        { component: SidebarTagsSection },
        { component: SidebarGlossaryTermsSection },
        {
            component: SidebarSiblingsSection,
            display: {
                visible: (_, catalogRecord: GetCatalogRecordQuery) => !!catalogRecord?.catalogRecord?.siblingsSearch?.total,
            },
        },
        { component: SidebarDatasetViewDefinitionSection },
        { component: SidebarQueryOperationsSection },
        { component: SidebarStructuredProperties },
        { component: StatusSection },
        // {
        //    component: SidebarRecommendationsSection,
        // },
    ];

    getSidebarTabs = () => [
        {
            name: 'Lineage',
            component: LineageTab,
            description: "View this data asset's upstream and downstream dependencies",
            icon: TreeStructure,
            properties: {
                actionType: SidebarTitleActionType.LineageExplore,
            },
        },
        {
            name: 'Columns',
            component: SchemaTab,
            description: "View this data asset's columns",
            icon: Columns,
            properties: {
                fullHeight: true,
            },
        },
        {
            name: 'Properties',
            component: PropertiesTab,
            description: 'View additional properties about this asset',
            icon: ListBullets,
        },
    ];

    #shouldMergeInLineage(catalogRecord?: CatalogRecord | null, flags?: FeatureFlagsConfig): boolean {
        // Lineage query must include platform and typeNames on catalogRecord and its sibling
        return (
            !!flags?.hideDbtSourceInLineage &&
            catalogRecord?.platform?.urn === DBT_URN &&
            !!catalogRecord?.subTypes?.typeNames?.includes(SubType.DbtSource)
        );
    }

    getOverridePropertiesFromEntity = (
        catalogRecord?: CatalogRecord | null,
        flags?: FeatureFlagsConfig,
    ): GenericEntityProperties => {
        // if catalogRecord has subTypes filled out, pick the most specific subtype and return it
        const subTypes = catalogRecord?.subTypes;

        const extendedProperties: DatasetProperties | undefined | null = catalogRecord?.properties && {
            ...catalogRecord?.properties,
            qualifiedName: catalogRecord?.properties?.qualifiedName || this.displayName(catalogRecord),
        };

        const firstSibling = catalogRecord?.siblingsSearch?.searchResults?.[0]?.entity as CatalogRecord | undefined;
        const isReplacedBySibling = this.#shouldMergeInLineage(catalogRecord, flags);
        const isSiblingHidden = this.#shouldMergeInLineage(firstSibling, flags);

        const lineageUrn = isReplacedBySibling ? firstSibling?.urn : undefined;
        let lineageSiblingIcon: string | undefined;
        if (isReplacedBySibling) {
            // Swap lineage urn and show as merged with sibling, extra icon is the original entity icon
            lineageSiblingIcon = catalogRecord?.platform?.properties?.logoUrl ?? undefined;
        } else if (isSiblingHidden) {
            // Same lineage urn but show as merged with sibling, extra icon is the sibling's icon
            lineageSiblingIcon = firstSibling?.platform?.properties?.logoUrl ?? undefined;
        }
        return {
            name: catalogRecord && this.displayName(catalogRecord),
            externalUrl: catalogRecord?.properties?.externalUrl,
            entityTypeOverride: subTypes ? capitalizeFirstLetterOnly(subTypes.typeNames?.[0]) : '',
            properties: extendedProperties,
            lineageUrn,
            lineageSiblingIcon,
        };
    };

    renderPreview = (previewType: PreviewType, data: CatalogRecord) => {
        const genericProperties = this.getGenericEntityProperties(data);
        const platformNames = genericProperties?.siblingPlatforms?.map(
            (platform) => platform.properties?.displayName || capitalizeFirstLetterOnly(platform.name),
        );
        return (
            <Preview
                urn={data.urn}
                data={genericProperties}
                name={data.properties?.name || data.name}
                origin={data.origin}
                subtype={data.subTypes?.typeNames?.[0]}
                description={data.editableProperties?.description || data.properties?.description}
                platformName={
                    data?.platform?.properties?.displayName || capitalizeFirstLetterOnly(data?.platform?.name)
                }
                platformNames={platformNames}
                platformLogo={data.platform.properties?.logoUrl}
                platformLogos={genericProperties?.siblingPlatforms?.map((platform) => platform.properties?.logoUrl)}
                platformInstanceId={data.dataPlatformInstance?.instanceId}
                owners={data.ownership?.owners}
                globalTags={data.globalTags}
                glossaryTerms={data.glossaryTerms}
                domain={data.domain?.domain}
                dataProduct={getDataProduct(genericProperties?.dataProduct)}
                container={data.container}
                externalUrl={data.properties?.externalUrl}
                health={data.health}
                headerDropdownItems={headerDropdownItems}
                previewType={previewType}
                browsePaths={data.browsePathV2 || undefined}
            />
        );
    };

    renderSearch = (result: SearchResult) => {
        const data = result.entity as CatalogRecord;
        const genericProperties = this.getGenericEntityProperties(data);
        const platformNames = genericProperties?.siblingPlatforms?.map(
            (platform) => platform.properties?.displayName || capitalizeFirstLetterOnly(platform.name),
        );

        return (
            <Preview
                urn={data.urn}
                data={genericProperties}
                name={data.properties?.name || data.name}
                origin={data.origin}
                description={data.editableProperties?.description || data.properties?.description}
                platformName={
                    platformNames?.[0] ||
                    data?.platform?.properties?.displayName ||
                    capitalizeFirstLetterOnly(data?.platform?.name)
                }
                platformLogo={data.platform.properties?.logoUrl}
                platformInstanceId={data.dataPlatformInstance?.instanceId}
                platformNames={platformNames}
                platformLogos={genericProperties?.siblingPlatforms?.map((platform) => platform.properties?.logoUrl)}
                owners={data.ownership?.owners}
                globalTags={data.globalTags}
                domain={data.domain?.domain}
                dataProduct={getDataProduct(genericProperties?.dataProduct)}
                deprecation={data.deprecation}
                glossaryTerms={data.glossaryTerms}
                subtype={data.subTypes?.typeNames?.[0]}
                container={data.container}
                parentContainers={data.parentContainers}
                snippet={<MatchedFieldList customFieldRenderer={matchedFieldPathsRenderer} />}
                insights={result.insights}
                externalUrl={data.properties?.externalUrl}
                statsSummary={data.statsSummary}
                rowCount={(data as any).lastProfile?.length && (data as any).lastProfile[0].rowCount}
                columnCount={(data as any).lastProfile?.length && (data as any).lastProfile[0].columnCount}
                lastUpdatedMs={getDatasetLastUpdatedMs(
                    (data as any).properties,
                    (data as any).lastOperation?.length && (data as any).lastOperation[0],
                )}
                health={data.health}
                degree={(result as any).degree}
                paths={(result as any).paths}
                isOutputPort={isOutputPort(result)}
                headerDropdownItems={headerDropdownItems}
                browsePaths={data.browsePathV2 || undefined}
            />
        );
    };

    renderSearchMatches = (_: SearchResult) => {
        return (
            <>
                <MatchedFieldList customFieldRenderer={matchedFieldPathsRenderer} />
            </>
        );
    };

    getLineageVizConfig = (entity: CatalogRecord) => {
        return {
            urn: entity?.urn,
            name: entity?.properties?.name || entity.name,
            expandedName: entity?.properties?.qualifiedName || entity?.properties?.name || entity.name,
            type: EntityType.CatalogRecord,
            subtype: entity?.subTypes?.typeNames?.[0] || undefined,
            icon: entity?.platform?.properties?.logoUrl || undefined,
            platform: entity?.platform,
            health: entity?.health || undefined,
            deprecation: entity?.deprecation,
        };
    };

    displayName = (data: CatalogRecord) => {
        return data?.properties?.name || data.name || data.urn;
    };

    platformLogoUrl = (data: CatalogRecord) => {
        return data.platform.properties?.logoUrl || undefined;
    };

    getGenericEntityProperties = (data: CatalogRecord, flags?: FeatureFlagsConfig) => {
        return getDataForEntityType({
            data,
            entityType: this.type,
            getOverrideProperties: this.getOverridePropertiesFromEntity,
            flags,
        });
    };

    supportedCapabilities = () => {
        return new Set([
            EntityCapabilityType.OWNERS,
            EntityCapabilityType.GLOSSARY_TERMS,
            EntityCapabilityType.TAGS,
            EntityCapabilityType.DOMAINS,
            EntityCapabilityType.DEPRECATION,
            EntityCapabilityType.SOFT_DELETE,
            EntityCapabilityType.DATA_PRODUCTS,
            EntityCapabilityType.TEST,
            EntityCapabilityType.LINEAGE,
            EntityCapabilityType.HEALTH,
            EntityCapabilityType.APPLICATIONS,
        ]);
    };

    renderEmbeddedProfile = (urn: string) => (
        <EmbeddedProfile
            urn={urn}
            entityType={EntityType.CatalogRecord}
            useEntityQuery={useGetCatalogRecordQuery}
            getOverrideProperties={this.getOverridePropertiesFromEntity}
        />
    );
}
