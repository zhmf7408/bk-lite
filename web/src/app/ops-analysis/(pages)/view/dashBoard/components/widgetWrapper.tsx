import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Spin, Tooltip } from 'antd';
import { ExclamationCircleOutlined, WarningOutlined } from '@ant-design/icons';
import { useTranslation } from '@/utils/i18n';
import {
  BaseWidgetProps,
  FilterValue,
  UnifiedFilterDefinition,
  BindingValidationResult,
} from '@/app/ops-analysis/types/dashBoard';
import { DatasourceItem } from '@/app/ops-analysis/types/dataSource';
import { fetchWidgetData } from '../../../../utils/widgetDataTransform';
import { useDataSourceApi } from '@/app/ops-analysis/api/dataSource';
import { ChartDataTransformer } from '@/app/ops-analysis/utils/chartDataTransform';
import ComPie from '../widgets/comPie';
import ComLine from '../widgets/comLine';
import ComBar from '../widgets/comBar';
import ComTable from '../widgets/comTable';

const componentMap: Record<string, React.ComponentType<any>> = {
  line: ComLine,
  pie: ComPie,
  bar: ComBar,
  table: ComTable,
};

interface WidgetWrapperProps extends BaseWidgetProps {
  chartType?: string;
  dataSource?: DatasourceItem;
  unifiedFilterValues?: Record<string, FilterValue>;
  filterDefinitions?: UnifiedFilterDefinition[];
  searchKey?: number;
}

const WidgetWrapper: React.FC<WidgetWrapperProps> = ({
  chartType,
  config,
  refreshKey,
  onReady,
  dataSource,
  unifiedFilterValues,
  filterDefinitions,
  searchKey,
}) => {
  const { t } = useTranslation();
  const [rawData, setRawData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(false);
  const [tableQueryReady, setTableQueryReady] = useState(false);
  const [dataValidation, setDataValidation] = useState<{
    isValid: boolean;
    message?: string;
  } | null>(null);
  const [tableQueryParams, setTableQueryParams] = useState<Record<string, any>>(
    {},
  );
  const { getSourceDataByApiId } = useDataSourceApi();

  const unifiedFilterValuesRef = useRef(unifiedFilterValues);
  unifiedFilterValuesRef.current = unifiedFilterValues;

  const invalidBindings = useMemo((): BindingValidationResult[] => {
    const bindings = config?.filterBindings;
    if (!bindings || !filterDefinitions || !dataSource?.params) {
      return [];
    }

    const results: BindingValidationResult[] = [];
    const enabledBindingIds = Object.entries(bindings)
      .filter(([, enabled]) => enabled)
      .map(([filterId]) => filterId);

    for (const filterId of enabledBindingIds) {
      const definition = filterDefinitions.find((d) => d.id === filterId);
      if (!definition) {
        results.push({
          filterId,
          isValid: false,
          reason: 'filter_not_found',
        });
        continue;
      }

      const matchingParams = dataSource.params.filter(
        (p) => p.name === definition.key && p.filterType === 'filter',
      );

      if (matchingParams.length === 0) {
        results.push({
          filterId,
          isValid: false,
          reason: 'param_not_found',
        });
        continue;
      }

      const exactMatch = matchingParams.find((p) => p.type === definition.type);
      if (!exactMatch) {
        results.push({
          filterId,
          isValid: false,
          reason: 'type_mismatch',
        });
      }
    }

    return results;
  }, [config?.filterBindings, filterDefinitions, dataSource?.params]);

  const handleTableQueryChange = useCallback((params: Record<string, any>) => {
    setTableQueryReady(true);
    setTableQueryParams((prev) => {
      if (JSON.stringify(prev) === JSON.stringify(params || {})) {
        return prev;
      }
      return params || {};
    });
  }, []);

  const validateChartData = useCallback((data: unknown, type?: string) => {
    const isDataEmpty = () => !data || (Array.isArray(data) && data.length === 0);

    if (isDataEmpty()) {
      return { isValid: true };
    }

    const errorMessage = t('dashboard.dataFormatMismatch');
    switch (type) {
      case 'pie':
        return ChartDataTransformer.validatePieData(data, errorMessage);
      case 'line':
      case 'bar':
        return ChartDataTransformer.validateLineBarData(data, errorMessage);
      case 'table':
        return { isValid: true };
      default:
        return { isValid: true };
    }
  }, [t]);

  const fetchData = useCallback(async () => {
    if (!config?.dataSource) {
      setLoading(false);
      setTableLoading(false);
      setDataValidation(null);
      return;
    }

    const isTableChart = chartType === 'table';

    if (dataSource?.hasAuth === false) {
      setLoading(false);
      setTableLoading(false);
      setRawData(null);
      setDataValidation({
        isValid: false,
        message: t('common.noAuth'),
      });
      return;
    }

    try {
      if (isTableChart) {
        setTableLoading(true);
      } else {
        setLoading(true);
      }
      setDataValidation(null);

      const data = await fetchWidgetData({
        config,
        dataSource,
        extraParams: chartType === 'table' ? tableQueryParams : undefined,
        getSourceDataByApiId,
        unifiedFilterValues: unifiedFilterValuesRef.current,
        filterBindings: config?.filterBindings,
        filterDefinitions,
      });

      setRawData(data);

      const validation = validateChartData(data, chartType);
      setDataValidation(validation);
    } catch (err) {
      console.error('获取数据失败:', err);
      setRawData(null);
      setDataValidation({
        isValid: false,
        message: t('dashboard.dataFetchFailed'),
      });
    } finally {
      if (isTableChart) {
        setTableLoading(false);
      } else {
        setLoading(false);
      }
    }
  }, [
    config,
    chartType,
    dataSource,
    tableQueryParams,
    getSourceDataByApiId,
    filterDefinitions,
    validateChartData,
    t,
  ]);

  const dataSourceId = config?.dataSource;
  const [initialFetchDone, setInitialFetchDone] = useState(false);

  useEffect(() => {
    if (!dataSourceId) {
      setInitialFetchDone(false);
      return;
    }

    if (chartType === 'table' && !tableQueryReady) {
      return;
    }

    if (!initialFetchDone) {
      fetchData();
      setInitialFetchDone(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataSourceId, chartType, tableQueryReady, initialFetchDone]);

  useEffect(() => {
    if (!dataSourceId || !initialFetchDone) {
      return;
    }

    if (chartType === 'table' && !tableQueryReady) {
      return;
    }

    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey, searchKey, dataSource?.hasAuth]);

  useEffect(() => {
    if (!dataSourceId || !initialFetchDone || chartType !== 'table' || !tableQueryReady) {
      return;
    }

    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tableQueryParams]);

  useEffect(() => {
    if (chartType !== 'table') {
      return;
    }
    setTableQueryReady(false);
    setTableQueryParams({});
    setTableLoading(false);
    setLoading(false);
  }, [chartType, config?.dataSource]);

  useEffect(() => {
    setDataValidation(null);
    if (chartType !== 'table') {
      setLoading(true);
    }
  }, [chartType]);

  const getInvalidBindingReasonText = (
    reason: BindingValidationResult['reason'],
  ): string => {
    switch (reason) {
      case 'filter_not_found':
        return t('dashboard.bindingInvalidFilterNotFound');
      case 'param_not_found':
        return t('dashboard.bindingInvalidParamNotFound');
      case 'type_mismatch':
        return t('dashboard.bindingInvalidTypeMismatch');
      default:
        return t('dashboard.bindingInvalidUnknown');
    }
  };

  const renderBindingWarning = () => {
    if (invalidBindings.length === 0) {
      return null;
    }

    const tooltipContent = (
      <div>
        <div style={{ fontWeight: 500, marginBottom: 4 }}>
          {t('dashboard.bindingInvalidTitle')}
        </div>
        {invalidBindings.map((binding) => {
          const definition = filterDefinitions?.find(
            (d) => d.id === binding.filterId,
          );
          const name = definition?.name || binding.filterId;
          return (
            <div key={binding.filterId} style={{ fontSize: 12 }}>
              • {name}: {getInvalidBindingReasonText(binding.reason)}
            </div>
          );
        })}
      </div>
    );

    return (
      <Tooltip title={tooltipContent} placement="topRight">
        <div
          style={{
            position: 'absolute',
            top: 4,
            right: 4,
            zIndex: 10,
            cursor: 'pointer',
          }}
        >
          <WarningOutlined style={{ color: '#faad14', fontSize: 16 }} />
        </div>
      </Tooltip>
    );
  };

  const renderError = (message: string) => (
    <div className="h-full flex flex-col items-center justify-center">
      <ExclamationCircleOutlined
        style={{ color: '#faad14', fontSize: '24px', marginBottom: '12px' }}
      />
      <span style={{ fontSize: '14px', color: '#666' }}>{message}</span>
    </div>
  );

  if (loading && chartType !== 'table') {
    return (
      <div className="h-full flex items-center justify-center">
        <Spin spinning={loading} />
      </div>
    );
  }

  const Component = chartType ? componentMap[chartType] : null;
  if (!Component) {
    return renderError(`${t('dashboard.unknownComponentType')}: ${chartType}`);
  }

  // 如果数据校验失败，显示错误提示
  if (dataValidation && !dataValidation.isValid) {
    return renderError(
      dataValidation.message || t('dashboard.dataCannotRenderAsChart'),
    );
  }

  return (
    <div style={{ position: 'relative', height: '100%' }}>
      {renderBindingWarning()}
      <Component
        rawData={rawData}
        loading={chartType === 'table' ? tableLoading : loading}
        config={config}
        dataSource={dataSource}
        refreshKey={refreshKey}
        onReady={onReady}
        onQueryChange={chartType === 'table' ? handleTableQueryChange : undefined}
      />
    </div>
  );
};

export default WidgetWrapper;
