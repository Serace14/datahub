import { Dashboard2, Entity, EntityType } from '@types';

/**
 * Type guard for dashboards
 */
export function isDashboard(entity?: Entity | null | undefined): entity is Dashboard2 {
    return !!entity && entity.type === EntityType.Dashboard2;
}
