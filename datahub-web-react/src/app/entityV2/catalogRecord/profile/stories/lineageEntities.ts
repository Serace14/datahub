import { EntityType, FabricType, PlatformNativeType } from '@types';

export const sampleUpstreamEntities = [
    {
        name: 'Upstream HiveCatalogRecord',
        type: EntityType.CatalogRecord,
        urn: 'abc',
        platform: {
            urn: 'urn:li:dataPlatform:hive',
            name: 'Hive',
            type: EntityType.DataPlatform,
        },
        origin: FabricType.Prod,
        description: 'this is a CatalogRecord',
        platformNativeType: PlatformNativeType.Table,
        tags: [],
        created: {
            time: 0,
        },
        lastModified: {
            time: 0,
        },
    },
    {
        name: 'Upstream KafkaCatalogRecord',
        type: EntityType.CatalogRecord,
        urn: 'abc',
        platform: {
            urn: 'urn:li:dataPlatform:hive',
            name: 'Hive',
            type: EntityType.DataPlatform,
        },
        origin: FabricType.Prod,
        description: 'this is a CatalogRecord',
        platformNativeType: PlatformNativeType.Table,
        tags: [],
        created: {
            time: 0,
        },
        lastModified: {
            time: 0,
        },
    },
];

export const sampleDownstreamEntities = [
    {
        name: 'Downstream HiveCatalogRecord',
        type: EntityType.CatalogRecord,
        urn: 'abc',
        platform: {
            urn: 'urn:li:dataPlatform:hive',
            name: 'Hive',
            type: EntityType.DataPlatform,
        },
        origin: FabricType.Prod,
        description: 'this is a CatalogRecord',
        platformNativeType: PlatformNativeType.Table,
        tags: [],
        created: {
            time: 0,
        },
        lastModified: {
            time: 0,
        },
    },
    {
        name: 'Downstream KafkaCatalogRecord',
        type: EntityType.CatalogRecord,
        urn: 'abc',
        platform: {
            urn: 'urn:li:dataPlatform:hive',
            name: 'Hive',
            type: EntityType.DataPlatform,
        },
        origin: FabricType.Prod,
        description: 'this is a CatalogRecord',
        platformNativeType: PlatformNativeType.Table,
        tags: [],
        created: {
            time: 0,
        },
        lastModified: {
            time: 0,
        },
    },
];

export const sampleRelationship = {
    entities: sampleUpstreamEntities.map((entity) => ({
        entity,
        created: { time: 0 },
    })),
};

export const sampleDownstreamRelationship = {
    entities: sampleDownstreamEntities.map((entity) => ({
        entity,
        created: { time: 0 },
    })),
};
