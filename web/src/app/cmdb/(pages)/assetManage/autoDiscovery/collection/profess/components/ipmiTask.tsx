'use client';

import React, { useEffect, useRef } from 'react';
import BaseTaskForm, { BaseTaskRef } from './baseTask';
import styles from '../index.module.scss';
import { CaretRightOutlined, QuestionCircleOutlined } from '@ant-design/icons';
import { useLocale } from '@/context/locale';
import { useTranslation } from '@/utils/i18n';
import { useTaskForm } from '../hooks/useTaskForm';
import { getCleanupFormValues } from '../hooks/useTaskForm';
import { TreeNode, ModelItem } from '@/app/cmdb/types/autoDiscovery';
import {
  HOST_FORM_INITIAL_VALUES,
  PASSWORD_PLACEHOLDER,
} from '@/app/cmdb/constants/professCollection';
import { formatTaskValues, buildCredential } from '../hooks/formatTaskValues';
import { Form, Spin, Input, Collapse, InputNumber, Select, Tooltip } from 'antd';
import useAssetManageStore from '@/app/cmdb/store/useAssetManage';

interface IPMITaskFormProps {
  onClose: () => void;
  onSuccess?: () => void;
  selectedNode: TreeNode;
  modelItem: ModelItem;
  editId?: number | null;
}

const IPMI_FORM_INITIAL_VALUES = {
  ...HOST_FORM_INITIAL_VALUES,
  port: '623',
  // 默认按管理员级别发起会话，减少不同厂商 BMC 下因为权限过低导致 inventory 不完整的概率。
  privilege: 'administrator',
};

const PRIVILEGE_OPTIONS = [
  { label: 'callback', value: 'callback' },
  { label: 'user', value: 'user' },
  { label: 'operator', value: 'operator' },
  { label: 'administrator', value: 'administrator' },
];

const IPMITask: React.FC<IPMITaskFormProps> = ({
  onClose,
  onSuccess,
  selectedNode,
  modelItem,
  editId,
}) => {
  const { t } = useTranslation();
  const baseRef = useRef<BaseTaskRef>(null as any);
  const localeContext = useLocale();
  const { copyTaskData } = useAssetManageStore();
  const { model_id: modelId } = modelItem;

  const {
    form,
    loading,
    submitLoading,
    fetchTaskDetail,
    formatCycleValue,
    onFinish,
  } = useTaskForm({
    modelId,
    editId,
    initialValues: IPMI_FORM_INITIAL_VALUES,
    onSuccess,
    onClose,
    formatValues: (values) => {
      const baseData = formatTaskValues({
        values,
        baseRef,
        selectedNode,
        modelItem,
        modelId,
        formatCycleValue,
      });

      const collectType = baseRef.current?.collectionType;
      const ipRange = values.ipRange?.length ? values.ipRange : undefined;
      const selectedData = baseRef.current?.selectedData;
      // IPMI 与 SSH 物理机任务共享 BaseTask 的目标选择交互：既支持 IP 段，也支持从现有资产实例中选择。
      const instanceData = collectType === 'ip'
        ? {
          ip_range: ipRange.join('-'),
          instances: [],
        }
        : {
          ip_range: '',
          instances: selectedData || [],
        };

      return {
        ...baseData,
        ...instanceData,
        credential: buildCredential(
          {
            // 注意：这里仍然写回现有 physcial_server 模型，但凭据语义已经变成 IPMI/BMC 登录信息。
            username: 'username',
            password: 'password',
            port: 'port',
            privilege: 'privilege',
          },
          values
        ),
      };
    },
  });

  const buildFormValues = (values: any, isCopy: boolean, ipRange?: string[]) => ({
    ipRange,
    ...getCleanupFormValues(values),
    ...values,
    taskName: isCopy ? '' : values.name,
    organization: values.team || [],
    username: values.credential?.username || values.credential?.user,
    password: isCopy ? '' : PASSWORD_PLACEHOLDER,
    port: values.credential?.port || 623,
    privilege: values.credential?.privilege || 'administrator',
    accessPointId: values.access_point?.[0]?.id,
  });

  useEffect(() => {
    const initForm = async () => {
      if (copyTaskData) {
        const values = copyTaskData;
        const ipRange = values.ip_range?.split('-');
        if (values.ip_range?.length) {
          baseRef.current?.initCollectionType(ipRange, 'ip');
        } else {
          baseRef.current?.initCollectionType(values.instances, 'asset');
        }
        form.setFieldsValue(buildFormValues(values, true, ipRange));
      } else if (editId) {
        const values = await fetchTaskDetail(editId);
        const ipRange = values.ip_range?.split('-');
        if (values.ip_range?.length) {
          baseRef.current?.initCollectionType(ipRange, 'ip');
        } else {
          baseRef.current?.initCollectionType(values.instances, 'asset');
        }
        form.setFieldsValue(buildFormValues(values, false, ipRange));
      } else {
        form.setFieldsValue(IPMI_FORM_INITIAL_VALUES);
      }
    };
    initForm();
  }, [copyTaskData, editId, fetchTaskDetail, form]);

  return (
    <Spin spinning={loading}>
      <Form
        form={form}
        layout="horizontal"
        labelCol={{ span: localeContext.locale === 'en' ? 6 : 5 }}
        onFinish={onFinish}
        initialValues={IPMI_FORM_INITIAL_VALUES}
      >
        <BaseTaskForm
          ref={baseRef}
          nodeId={selectedNode.id}
          modelItem={modelItem}
          onClose={onClose}
          submitLoading={submitLoading}
          instPlaceholder={`${t('Collection.chooseAsset')}`}
          timeoutProps={{
            min: 0,
            defaultValue: 10,
            addonAfter: t('Collection.k8sTask.second'),
          }}
        >
          <Collapse
            ghost
            defaultActiveKey={['credential']}
            expandIcon={({ isActive }) => (
              <CaretRightOutlined rotate={isActive ? 90 : 0} className="text-base" />
            )}
          >
            <Collapse.Panel
              header={<div className={styles.panelHeader}>{t('Collection.credential')}</div>}
              key="credential"
            >
              <Form.Item label={t('user')} name="username">
                <Input placeholder={t('common.inputTip')} />
              </Form.Item>

              <Form.Item label={t('password')} name="password">
                <Input.Password
                  placeholder={t('common.inputTip')}
                  onFocus={(e) => {
                    if (!editId) return;
                    const value = e.target.value;
                    if (value === PASSWORD_PLACEHOLDER) {
                      form.setFieldValue('password', '');
                    }
                  }}
                  onBlur={(e) => {
                    if (!editId) return;
                    const value = e.target.value;
                    if (!value || value.trim() === '') {
                      form.setFieldValue('password', PASSWORD_PLACEHOLDER);
                    }
                  }}
                />
              </Form.Item>

              <Form.Item label={t('Collection.port')} name="port">
                <InputNumber min={1} max={65535} className="w-32" placeholder="623" />
              </Form.Item>

              <Form.Item
                label={
                  <span>
                    {t('Collection.IPMITask.privilege')}
                    <Tooltip title={t('Collection.IPMITask.privilegeTooltip')}>
                      <QuestionCircleOutlined className="ml-1 text-gray-400" />
                    </Tooltip>
                  </span>
                }
                name="privilege"
              >
                <Select options={PRIVILEGE_OPTIONS} placeholder={t('common.selectTip')} />
              </Form.Item>
            </Collapse.Panel>
          </Collapse>
        </BaseTaskForm>
      </Form>
    </Spin>
  );
};

export default IPMITask;
