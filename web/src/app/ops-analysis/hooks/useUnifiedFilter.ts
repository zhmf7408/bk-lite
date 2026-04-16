import { useState, useCallback, useMemo } from 'react';
import {
  DashboardFilters,
  DashboardFiltersState,
  UnifiedFilterDefinition,
  FilterValue,
} from '@/app/ops-analysis/types/dashBoard';

export interface UseUnifiedFilterReturn {
  definitions: UnifiedFilterDefinition[];
  filterValues: Record<string, FilterValue>;
  setFilterValues: (values: Record<string, FilterValue>) => void;
  updateDefinitions: (definitions: UnifiedFilterDefinition[]) => void;
  setDefinitions: (definitions: DashboardFilters) => void;
}

export const useUnifiedFilter = (
  initialDefinitions?: DashboardFilters,
): UseUnifiedFilterReturn => {
  const [state, setState] = useState<DashboardFiltersState>(() => ({
    definitions: initialDefinitions || [],
    values: {},
  }));

  const filterValues = useMemo(() => state.values || {}, [state.values]);

  const setFilterValues = useCallback(
    (values: Record<string, FilterValue>) => {
      setState((prev) => ({
        ...prev,
        values: { ...values },
      }));
    },
    [],
  );

  const updateDefinitions = useCallback(
    (definitions: UnifiedFilterDefinition[]) => {
      setState((prev) => ({
        ...prev,
        definitions,
      }));
    },
    [],
  );

  const setDefinitions = useCallback((newDefinitions: DashboardFilters) => {
    setState((prev) => ({
      ...prev,
      definitions: newDefinitions || [],
    }));
  }, []);

  return {
    definitions: state.definitions,
    filterValues,
    setFilterValues,
    updateDefinitions,
    setDefinitions,
  };
};
