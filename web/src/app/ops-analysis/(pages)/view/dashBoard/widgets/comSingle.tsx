import React, { useEffect, useState } from 'react';
import { Spin, Empty } from 'antd';
import {
  getColorByThreshold,
  formatDisplayValue,
  ThresholdColorConfig,
} from '@/app/ops-analysis/utils/thresholdUtils';
import { DEFAULT_THRESHOLD_COLORS } from '@/app/ops-analysis/constants/threshold';
import { ValueConfig } from '@/app/ops-analysis/types/dashBoard';

interface ComSingleProps {
  rawData: unknown;
  loading?: boolean;
  config?: ValueConfig;
  onReady?: (ready: boolean) => void;
}

const getValueByPathForSingle = (obj: unknown, path: string): unknown => {
  if (!obj || !path) return undefined;

  if (Array.isArray(obj) && obj.length > 0) {
    const firstItem = obj[0] as Record<string, unknown>;

    if (firstItem && typeof firstItem === 'object' && firstItem.namespace_id && firstItem.data) {
      if (path === 'namespace_id') {
        return firstItem.namespace_id;
      }

      if (path.startsWith('data.')) {
        const fieldPath = path.substring(5);

        if (Array.isArray(firstItem.data) && firstItem.data.length > 0) {
          return getValueByPathForSingle(firstItem.data[0], fieldPath);
        } else if (typeof firstItem.data === 'object' && firstItem.data !== null) {
          return getValueByPathForSingle(firstItem.data, fieldPath);
        }
      }
    }
  }

  return path.split('.').reduce((current, key) => {
    if (current === null || current === undefined) return undefined;

    if (Array.isArray(current)) {
      const index = parseInt(key, 10);
      if (!isNaN(index) && index >= 0 && index < current.length) {
        return current[index];
      }
      return current.length > 0 && current[0] && typeof current[0] === 'object'
        ? (current[0] as Record<string, unknown>)[key]
        : undefined;
    }

    return (current as Record<string, unknown>)[key];
  }, obj);
};

const ComSingle: React.FC<ComSingleProps> = ({
  rawData,
  loading = false,
  config,
  onReady,
}) => {
  const [isDataReady, setIsDataReady] = useState(false);

  const extractValue = (data: unknown): number | string | null => {
    if (data === null || data === undefined) {
      return null;
    }

    const selectedField = config?.selectedFields?.[0];

    if (selectedField) {
      const extracted = getValueByPathForSingle(data, selectedField);
      if (extracted !== undefined && extracted !== null) {
        return typeof extracted === 'number' || typeof extracted === 'string'
          ? extracted
          : null;
      }
    }

    if (typeof data === 'number' || typeof data === 'string') {
      return data;
    }

    if (Array.isArray(data) && data.length > 0) {
      const firstItem = data[0];
      if (firstItem && typeof firstItem === 'object') {
        const dataField = (firstItem as Record<string, unknown>).data;
        if (dataField !== undefined) {
          if (typeof dataField === 'number' || typeof dataField === 'string') {
            return dataField;
          }
          if (Array.isArray(dataField) && dataField.length > 0) {
            const firstDataItem = dataField[0];
            if (typeof firstDataItem === 'number' || typeof firstDataItem === 'string') {
              return firstDataItem;
            }
            if (firstDataItem && typeof firstDataItem === 'object') {
              const values = Object.values(firstDataItem as Record<string, unknown>);
              for (const val of values) {
                if (typeof val === 'number') return val;
              }
              for (const val of values) {
                if (typeof val === 'string' && !isNaN(parseFloat(val))) return val;
              }
            }
          }
        }
        const values = Object.values(firstItem as Record<string, unknown>);
        for (const val of values) {
          if (typeof val === 'number') return val;
        }
      }
    }

    if (typeof data === 'object' && data !== null) {
      const values = Object.values(data as Record<string, unknown>);
      for (const val of values) {
        if (typeof val === 'number') return val;
      }
    }

    return null;
  };

  const rawValue = extractValue(rawData);
  const numericValue = rawValue !== null
    ? (typeof rawValue === 'string' ? parseFloat(rawValue) : rawValue)
    : null;

  const thresholds: ThresholdColorConfig[] = config?.thresholdColors ?? DEFAULT_THRESHOLD_COLORS;
  const color = getColorByThreshold(numericValue, thresholds, '#000000');
  const displayValue = formatDisplayValue(
    numericValue,
    config?.unit,
    config?.decimalPlaces,
    config?.conversionFactor
  );

  useEffect(() => {
    if (!loading) {
      const hasData = rawValue !== null;
      setIsDataReady(hasData);
      onReady?.(hasData);
    }
  }, [rawValue, loading, onReady]);

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <Spin size="small" />
      </div>
    );
  }

  if (!isDataReady || rawValue === null) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col items-center justify-center">
      <div
        className="text-4xl font-bold transition-colors duration-300"
        style={{ color }}
      >
        {displayValue}
      </div>
    </div>
  );
};

export default ComSingle;
