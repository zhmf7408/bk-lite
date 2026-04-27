import type { DatasourceItem } from '@/app/ops-analysis/types/dataSource';
import type { LayoutItem } from '@/app/ops-analysis/types/dashBoard';

export interface NamespaceOption {
  label: string;
  value: number;
}

export const collectNamespaceOptions = (
  layout: LayoutItem[],
  dataSources: DatasourceItem[],
  namespaceList: Array<{ id: number; name: string }>,
): NamespaceOption[] => {
  const namespaceIds = new Set<number>();

  layout.forEach((item) => {
    const dsId = item.valueConfig?.dataSource;
    const normalizedId = typeof dsId === 'string' ? parseInt(dsId, 10) : dsId;
    const ds = dataSources.find((d) => d.id === normalizedId);
    if (ds?.namespaces) {
      ds.namespaces.forEach((id) => namespaceIds.add(id));
    }
  });

  if (namespaceIds.size === 0) return [];

  return namespaceList
    .filter((ns) => namespaceIds.has(ns.id))
    .map((ns) => ({
      label: ns.name || String(ns.id),
      value: ns.id,
    }));
};

export const datasourceSupportsNamespace = (
  dataSource: DatasourceItem | undefined,
  namespaceId: number | undefined,
): boolean => {
  if (!dataSource || namespaceId === undefined) return true;
  if (!dataSource.namespaces || dataSource.namespaces.length === 0) return true;
  return dataSource.namespaces.includes(namespaceId);
};
