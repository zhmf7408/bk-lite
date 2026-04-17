'use client';

import React, { useEffect, useState } from 'react';
import { Button, Empty, Modal, Spin, message } from 'antd';
import { useSearchParams } from 'next/navigation';
import CodeEditor from '@/app/monitor/components/codeEditor';
import useIntegrationApi from '@/app/monitor/api/integration';
import { useTranslation } from '@/utils/i18n';

const CollectPage = () => {
  const { t } = useTranslation();
  const searchParams = useSearchParams();
  const {
    getSnmpCollectTemplate,
    updateSnmpCollectTemplate
  } = useIntegrationApi();
  const pluginId = searchParams.get('plugin_id') || '';
  const templateType = searchParams.get('template_type') || '';

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loadError, setLoadError] = useState('');
  const [content, setContent] = useState('');
  const [initialContent, setInitialContent] = useState('');

  useEffect(() => {
    if (!pluginId || templateType !== 'snmp') {
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      setLoadError('');
      try {
        const data = await getSnmpCollectTemplate(pluginId);
        setContent(data.content || '');
        setInitialContent(data.content || '');
      } catch (error: any) {
        const errorMessage = error?.message || t('common.operationFailed');
        setLoadError(errorMessage);
        message.error(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [pluginId, templateType]);

  const handleSave = () => {
    Modal.confirm({
      title: '保存采集片段',
      content: '保存后会立即同步到所有已下发该模板的采集实例，是否继续？',
      centered: true,
      okText: t('common.confirm'),
      cancelText: t('common.cancel'),
      onOk: async () => {
        setSaving(true);
        try {
          const data = await updateSnmpCollectTemplate(pluginId, { content });
          setContent(data.content || '');
          setInitialContent(data.content || '');
          message.success('采集片段已保存，并已尝试同步到已下发实例');
        } catch (error: any) {
          message.error(error?.message || t('common.operationFailed'));
        } finally {
          setSaving(false);
        }
      }
    });
  };

  if (templateType !== 'snmp') {
    return <Empty description="当前模板不支持采集片段编辑" />;
  }

  return (
    <Spin spinning={loading}>
      <div className="px-[10px] h-[calc(100vh-270px)] overflow-y-auto">
        <div className="mb-4">
          <div className="mb-2 text-[20px] font-semibold text-[var(--color-text-1)]">
            采集
          </div>
          <div className="text-[14px] text-[var(--color-text-2)]">
            直接填写 Telegraf SNMP Input 中的指标采集片段。请仅编辑 field/table 相关配置，不要修改主配置与标签区块。
          </div>
          <div className="mt-2 text-[12px] text-[var(--color-text-3)]">
            下方内容仅为示例模板，未取消注释并补充有效 OID 前不会产生采集数据。保存前会校验 TOML 语法，并尝试同步到已下发该模板的 SNMP 实例。
          </div>
        </div>

        {!!loadError && (
          <div className="mb-4 rounded-md border border-[var(--color-warning)] bg-[var(--color-warning-bg)] px-4 py-3 text-[14px] text-[var(--color-warning-text)]">
            采集模板加载失败：{loadError}
          </div>
        )}

        <div className="mb-4 rounded-md border border-[var(--color-border)] bg-[var(--color-bg-1)] overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border)] bg-[var(--color-fill-1)]">
            <div className="text-sm font-medium text-[var(--color-text-1)]">
              采集配置指标片段
            </div>
            <div className="text-sm text-[var(--color-text-3)]">
              TOML / Telegraf SNMP Input
            </div>
          </div>
          <CodeEditor
            value={content}
            mode="toml"
            theme="monokai"
            width="100%"
            height="520px"
            onChange={(value: string) => setContent(value)}
            headerOptions={{ copy: true, fullscreen: true }}
            setOptions={{ showPrintMargin: false, useWorker: false }}
          />
        </div>

        <div className="my-4 flex justify-end">
          <Button
            type="primary"
            loading={saving}
            disabled={loading || !!loadError || content.trim() === initialContent.trim()}
            onClick={handleSave}
          >
            {t('common.save')}
          </Button>
        </div>
      </div>
    </Spin>
  );
};

export default CollectPage;
