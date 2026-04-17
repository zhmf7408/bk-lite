import React from 'react';
import {
  Button,
  Form,
  Input,
  InputNumber,
  ColorPicker,
  Tree,
  Spin,
} from 'antd';
import {
  PlusCircleOutlined,
  MinusCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { ThresholdColorConfig } from '@/app/ops-analysis/utils/thresholdUtils';

interface SingleValueSettingsSectionProps {
  t: (key: string) => string;
  selectedDataSource: any;
  singleValueTreeData: any[];
  selectedFields: string[];
  loadingSingleValueData: boolean;
  thresholdColors: ThresholdColorConfig[];
  onFetchSingleValueDataFields: () => void;
  onSingleValueFieldChange: (checkedKeys: any) => void;
  onThresholdChange: (
    index: number,
    field: 'value' | 'color',
    value: string | number,
  ) => void;
  onThresholdBlur: (index: number, value: number | null) => void;
  onAddThreshold: (afterIndex?: number) => void;
  onRemoveThreshold: (index: number) => void;
}

export const SingleValueSettingsSection: React.FC<
  SingleValueSettingsSectionProps
> = ({
  t,
  selectedDataSource,
  singleValueTreeData,
  selectedFields,
  loadingSingleValueData,
  thresholdColors,
  onFetchSingleValueDataFields,
  onSingleValueFieldChange,
  onThresholdChange,
  onThresholdBlur,
  onAddThreshold,
  onRemoveThreshold,
}) => {
  return (
    <div className="mb-6">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div className="font-medium">
            {t('topology.nodeConfig.dataSettings')}
          </div>
          <Button
            type="text"
            icon={<ReloadOutlined />}
            onClick={onFetchSingleValueDataFields}
            loading={loadingSingleValueData}
            disabled={!selectedDataSource}
            size="small"
            title={t('topology.nodeConfig.refreshDataFields')}
          />
        </div>

        <Form.Item
          name="selectedFields"
          rules={[
            {
              required: true,
              validator: (_, value) => {
                if (!value || value.length === 0) {
                  return Promise.reject(
                    new Error(t('topology.nodeConfig.selectAtLeastOneField')),
                  );
                }
                return Promise.resolve();
              },
            },
          ]}
        >
          <div>
            {singleValueTreeData.length > 0 ? (
              <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                <div className="text-sm text-gray-600 mb-3">
                  {t('topology.nodeConfig.selectDataFields')}
                </div>
                <Tree
                  checkable
                  checkStrictly
                  defaultExpandAll
                  checkedKeys={selectedFields}
                  onCheck={onSingleValueFieldChange}
                  treeData={singleValueTreeData}
                  height={300}
                  className="bg-white border border-gray-200 rounded p-2"
                />
              </div>
            ) : selectedDataSource ? (
              <div className="text-center py-4 text-gray-500">
                {loadingSingleValueData ? (
                  <div className="flex items-center justify-center">
                    <Spin size="small" className="mr-2" />
                    <span>{t('topology.nodeConfig.fetchingDataFields')}</span>
                  </div>
                ) : (
                  <span>{t('topology.nodeConfig.clickRefreshToGetFields')}</span>
                )}
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500">
                {t('topology.nodeConfig.selectDataSourceFirst')}
              </div>
            )}
          </div>
        </Form.Item>
      </div>

      <Form.Item label={t('topology.nodeConfig.unit')} name="unit">
        <Input placeholder={t('common.inputMsg')} style={{ width: '200px' }} />
      </Form.Item>

      <Form.Item
        label={t('topology.nodeConfig.conversionFactor')}
        name="conversionFactor"
      >
        <InputNumber
          min={0}
          max={100000}
          step={0.01}
          placeholder={t('common.inputMsg')}
          style={{ width: '120px' }}
        />
      </Form.Item>

      <Form.Item
        label={t('topology.nodeConfig.decimalPlaces')}
        name="decimalPlaces"
      >
        <InputNumber
          min={0}
          max={10}
          step={1}
          placeholder={t('common.inputMsg')}
          style={{ width: '120px' }}
        />
      </Form.Item>

      <Form.Item label={t('topology.nodeConfig.thresholdColors')}>
        <div className="space-y-3">
          {thresholdColors.map((threshold, index) => {
            const isBaseThreshold = index === thresholdColors.length - 1;
            return (
              <div
                key={index}
                className="flex items-center gap-2 p-2 border border-gray-200 rounded-md bg-gray-50"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-600 whitespace-nowrap">
                    {t('topology.nodeConfig.thresholdWhenValueGte')}
                  </span>
                  <InputNumber
                    value={parseFloat(threshold.value)}
                    onChange={(value) =>
                      onThresholdChange(index, 'value', value || 0)
                    }
                    onBlur={(e) => {
                      if (!isBaseThreshold) {
                        const value = parseFloat(e.target.value);
                        onThresholdBlur(index, isNaN(value) ? 0 : value);
                      }
                    }}
                    placeholder={t('common.inputMsg')}
                    disabled={isBaseThreshold}
                    style={{ width: '100px' }}
                    size="small"
                    min={0}
                  />
                  <span className="text-sm text-gray-600">
                    {t('topology.nodeConfig.thresholdShow')}
                  </span>
                </div>
                <ColorPicker
                  value={threshold.color}
                  onChange={(color) =>
                    onThresholdChange(index, 'color', color.toHexString())
                  }
                  size="small"
                  showText
                />
                <div className="flex items-center gap-3 pl-4">
                  <span
                    onClick={() => onAddThreshold(index)}
                    className="cursor-pointer text-gray-400 hover:text-gray-600 transition-colors duration-200"
                    style={{ fontSize: '16px' }}
                    title={t('topology.nodeConfig.addThresholdBelow')}
                  >
                    <PlusCircleOutlined />
                  </span>
                  <span
                    onClick={
                      isBaseThreshold ? undefined : () => onRemoveThreshold(index)
                    }
                    className={`transition-colors duration-200 ${
                      isBaseThreshold
                        ? 'text-gray-200 cursor-not-allowed'
                        : 'cursor-pointer text-gray-400 hover:text-gray-600'
                    }`}
                    style={{ fontSize: '16px' }}
                    title={
                      isBaseThreshold
                        ? t('topology.nodeConfig.baseThresholdNotRemovable')
                        : t('topology.nodeConfig.removeThreshold')
                    }
                  >
                    <MinusCircleOutlined />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </Form.Item>
    </div>
  );
};
