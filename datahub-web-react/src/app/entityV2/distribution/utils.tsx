import { Distribution, Entity, EntityType } from '@types';

/**
 * Type guard for Distribution
 */
export function isDistribution(entity?: Entity | null | undefined): entity is Distribution {
    return !!entity && entity.type === EntityType.Distribution;
}
