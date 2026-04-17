'use client';

import React, { useState, useEffect } from 'react';
import { Input, Space, Button } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import TimeSelector from '@/components/time-selector';
import type {
  UnifiedFilterDefinition,
  FilterValue,
  TimeRangeValue,
} from '@/app/ops-analysis/types/dashBoard';
import { useTranslation } from '@/utils/i18n';

interface UnifiedFilterBarProps {
  definitions: UnifiedFilterDefinition[];
  values: Record<string, FilterValue>;
  onChange: (values: Record<string, FilterValue>) => void;
}

const UnifiedFilterBar: React.FC<UnifiedFilterBarProps> = ({
  definitions,
  values,
  onChange,
}) => {
  const { t } = useTranslation();
  // 本地状态，用于暂存用户输入，点击搜索后才同步到父组件
  const [localValues, setLocalValues] =
    useState<Record<string, FilterValue>>(values);

  const enabledDefinitions = definitions
    .filter((d) => d.enabled)
    .sort((a, b) => a.order - b.order);

  // 当外部 values 变化时同步到本地
  useEffect(() => {
    setLocalValues(values);
  }, [values]);

  if (enabledDefinitions.length === 0) {
    return null;
  }

  const handleLocalValueChange = (filterId: string, value: FilterValue) => {
    setLocalValues((prev) => ({
      ...prev,
      [filterId]: value,
    }));
  };

  const handleTimeRangeChange = (
    filterId: string,
    range: number[],
    originValue: number | null,
  ) => {
    if (range.length === 2) {
      const timeRangeValue: TimeRangeValue = {
        start: dayjs(range[0]).toISOString(),
        end: dayjs(range[1]).toISOString(),
        selectValue: originValue ?? 0,
      };
      handleLocalValueChange(filterId, timeRangeValue);
    } else {
      handleLocalValueChange(filterId, null);
    }
  };

  const getTimeSelectorDefaultValue = (
    value: FilterValue,
  ): { selectValue: number; rangePickerVaule: [dayjs.Dayjs, dayjs.Dayjs] | null } => {
    const timeValue = value as TimeRangeValue | null | undefined;
    if (!timeValue || !timeValue.start || !timeValue.end) {
      return { selectValue: 15, rangePickerVaule: null };
    }
    const selectVal = timeValue.selectValue ?? 0;
    if (selectVal > 0) {
      return { selectValue: selectVal, rangePickerVaule: null };
    }
    return {
      selectValue: 0,
      rangePickerVaule: [dayjs(timeValue.start), dayjs(timeValue.end)],
    };
  };

  const handleSearch = () => {
    onChange(localValues);
  };

  const handleReset = () => {
    const emptyValues: Record<string, FilterValue> = {};
    enabledDefinitions.forEach((def) => {
      emptyValues[def.id] = def.defaultValue ?? null;
    });
    setLocalValues(emptyValues);
    onChange(emptyValues);
  };

  const renderFilterControl = (definition: UnifiedFilterDefinition) => {
    const value = localValues[definition.id];

    switch (definition.type) {
      case 'timeRange': {
        const defaultValue = getTimeSelectorDefaultValue(value);

        return (
          <TimeSelector
            key={`${definition.id}-${JSON.stringify(defaultValue)}`}
            onlyTimeSelect
            defaultValue={defaultValue}
            onChange={(range, originValue) =>
              handleTimeRangeChange(definition.id, range, originValue)
            }
          />
        );
      }

      case 'string':
      default:
        return (
          <Input
            value={(value as string) || ''}
            onChange={(e) =>
              handleLocalValueChange(definition.id, e.target.value)
            }
            onPressEnter={handleSearch}
            placeholder={definition.name}
            allowClear
            style={{ minWidth: 160 }}
          />
        );
    }
  };

  return (
    <div className="flex items-center gap-4 mx-3 mt-3 p-3 bg-(--color-bg-1) rounded-lg border border-(--color-border-2)">
      <Space wrap size="middle">
        {enabledDefinitions.map((definition) => (
          <div key={definition.id} className="flex items-center gap-2">
            <span className="text-sm text-(--color-text-2) whitespace-nowrap">
              {definition.name}:
            </span>
            {renderFilterControl(definition)}
          </div>
        ))}
        <Button
          type="primary"
          size="small"
          icon={<SearchOutlined />}
          onClick={handleSearch}
        >
          {t('common.search')}
        </Button>
        <Button size="small" icon={<ReloadOutlined />} onClick={handleReset}>
          {t('common.reset')}
        </Button>
      </Space>
    </div>
  );
};

export default UnifiedFilterBar;
