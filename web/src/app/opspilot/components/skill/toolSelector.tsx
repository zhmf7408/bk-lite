import React, { useState, useEffect } from 'react';
import { Button, Tooltip, Form, Input, Empty, InputNumber, Switch, message } from 'antd';

const { TextArea } = Input;
import { DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { useTranslation } from '@/utils/i18n';
import SelectorOperateModal from './operateModal';
import Icon from '@/components/icon';
import styles from './index.module.scss';
import { SelectTool, ToolVariable } from '@/app/opspilot/types/tool';
import { useSkillApi } from '@/app/opspilot/api/skill';
import OperateModal from '@/components/operate-modal';
import EditablePasswordField from '@/components/dynamic-form/editPasswordField';
import RedisToolEditor, { RedisInstanceFormValue } from './redisToolEditor';

const REDIS_TOOL_NAME = 'redis';
const REDIS_INSTANCES_KEY = 'redis_instances';
const REDIS_DEFAULT_INSTANCE_ID_KEY = 'redis_default_instance_id';
const REDIS_AUTO_NAME_PREFIX = 'Redis - ';

const createRedisInstanceId = () => `redis-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

const getDefaultRedisInstance = (name: string): RedisInstanceFormValue => ({
  id: createRedisInstanceId(),
  name,
  url: '',
  username: '',
  password: '',
  ssl: false,
  ssl_ca_path: '',
  ssl_keyfile: '',
  ssl_certfile: '',
  ssl_cert_reqs: '',
  ssl_ca_certs: '',
  cluster_mode: false,
  testStatus: 'untested',
});

const getNextRedisInstanceName = (instances: RedisInstanceFormValue[]) => {
  const maxIndex = instances.reduce((max, instance) => {
    const match = instance.name.match(/^Redis - (\d+)$/);
    if (!match) {
      return max;
    }
    return Math.max(max, Number(match[1]));
  }, 0);
  return `${REDIS_AUTO_NAME_PREFIX}${maxIndex + 1}`;
};

const parseRedisInstancesValue = (value: unknown): Record<string, unknown>[] => {
  if (Array.isArray(value)) {
    return value as Record<string, unknown>[];
  }
  if (typeof value === 'string' && value.trim()) {
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }
  return [];
};

const parseRedisBoolean = (value: unknown) => {
  if (typeof value === 'boolean') {
    return value;
  }
  if (typeof value === 'string') {
    return ['1', 'true', 'yes', 'on'].includes(value.trim().toLowerCase());
  }
  return Boolean(value);
};

const parseRedisToolConfig = (kwargs: ToolVariable[] = []): RedisInstanceFormValue[] => {
  const kwargsMap = new Map(kwargs.filter((item) => item.key).map((item) => [item.key, item.value]));
  const instancesValue = kwargsMap.get(REDIS_INSTANCES_KEY);
  const parsedInstances = parseRedisInstancesValue(instancesValue);

  if (parsedInstances.length > 0) {
    return parsedInstances.map((item, index) => ({
      id: String(item.id || `redis-${index + 1}`),
      name: String(item.name || `${REDIS_AUTO_NAME_PREFIX}${index + 1}`),
      url: String(item.url || ''),
      username: String(item.username || ''),
      password: String(item.password || ''),
      ssl: parseRedisBoolean(item.ssl),
      ssl_ca_path: String(item.ssl_ca_path || ''),
      ssl_keyfile: String(item.ssl_keyfile || ''),
      ssl_certfile: String(item.ssl_certfile || ''),
      ssl_cert_reqs: String(item.ssl_cert_reqs || ''),
      ssl_ca_certs: String(item.ssl_ca_certs || ''),
      cluster_mode: parseRedisBoolean(item.cluster_mode),
      testStatus: 'untested',
    }));
  }

  const hasLegacyConfig = ['url', 'username', 'password', 'ssl', 'ssl_ca_path', 'ssl_keyfile', 'ssl_certfile', 'ssl_cert_reqs', 'ssl_ca_certs', 'cluster_mode']
    .some((key) => kwargsMap.has(key));

  if (hasLegacyConfig) {
    return [{
      id: 'redis-1',
      name: 'Redis - 1',
      url: String(kwargsMap.get('url') || ''),
      username: String(kwargsMap.get('username') || ''),
      password: String(kwargsMap.get('password') || ''),
      ssl: parseRedisBoolean(kwargsMap.get('ssl')),
      ssl_ca_path: String(kwargsMap.get('ssl_ca_path') || ''),
      ssl_keyfile: String(kwargsMap.get('ssl_keyfile') || ''),
      ssl_certfile: String(kwargsMap.get('ssl_certfile') || ''),
      ssl_cert_reqs: String(kwargsMap.get('ssl_cert_reqs') || ''),
      ssl_ca_certs: String(kwargsMap.get('ssl_ca_certs') || ''),
      cluster_mode: parseRedisBoolean(kwargsMap.get('cluster_mode')),
      testStatus: 'untested',
    }];
  }

  return [getDefaultRedisInstance('Redis - 1')];
};

const serializeRedisToolConfig = (instances: RedisInstanceFormValue[]): ToolVariable[] => {
  const normalizedInstances = instances.map((instance) => {
    const normalizedInstance = { ...instance };
    delete normalizedInstance.testStatus;
    return normalizedInstance;
  });
  return [
    { key: REDIS_INSTANCES_KEY, value: JSON.stringify(normalizedInstances) },
    { key: REDIS_DEFAULT_INSTANCE_ID_KEY, value: normalizedInstances[0]?.id || '' },
  ];
};

const isRedisTool = (tool?: SelectTool | null) => (tool?.rawName || tool?.name) === REDIS_TOOL_NAME;

interface ToolSelectorProps {
  defaultTools: SelectTool[];
  onChange: (selected: SelectTool[]) => void;
}

const ToolSelector: React.FC<ToolSelectorProps> = ({ defaultTools, onChange }) => {
  const { t } = useTranslation();
  const { fetchSkillTools, testRedisConnection } = useSkillApi();
  const [loading, setLoading] = useState<boolean>(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [tools, setTools] = useState<SelectTool[]>([]);
  const [selectedTools, setSelectedTools] = useState<SelectTool[]>([]);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingTool, setEditingTool] = useState<SelectTool | null>(null);
  const [redisInstances, setRedisInstances] = useState<RedisInstanceFormValue[]>([]);
  const [selectedRedisInstanceId, setSelectedRedisInstanceId] = useState<string | null>(null);
  const [testingRedisConnection, setTestingRedisConnection] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await fetchSkillTools();
      const defaultToolMap = new Map(defaultTools.map((tool) => [tool.id, tool]));
      const defaultRedisTool = defaultTools.find((tool) => isRedisTool(tool));
      const fetchedTools = data.map((tool: any) => {
        const defaultTool = defaultToolMap.get(tool.id);
        const kwargs = (tool.params.kwargs || [])
          .filter((kwarg: any) => kwarg.key)
          .map((kwarg: any) => ({
            ...kwarg,
            value: (defaultTool?.kwargs ?? []).find((dk: any) => dk.key === kwarg.key)?.value ?? kwarg.value,
          }));
        return {
          id: tool.id,
          name: tool.display_name || tool.name,
          rawName: tool.name,
          icon: tool.icon || 'gongjuji',
          description: tool.description_tr || tool.description || '',
          kwargs,
        };
      });
      setTools(fetchedTools);

      const initialSelectedTools = fetchedTools
        .filter((tool) => defaultToolMap.has(tool.id) || (isRedisTool(tool) && !!defaultRedisTool))
        .map((tool) => {
          const matchedDefaultTool = defaultToolMap.get(tool.id) || (isRedisTool(tool) ? defaultRedisTool : undefined);
          if (!matchedDefaultTool) {
            return tool;
          }
          return {
            ...tool,
            kwargs: matchedDefaultTool.kwargs?.length ? matchedDefaultTool.kwargs : tool.kwargs,
          };
        });
      setSelectedTools(initialSelectedTools);
      onChange(initialSelectedTools);
    } catch (error) {
      console.error(t('common.fetchFailed'), error);
    } finally {
      setLoading(false);
    }
  };

  const openModal = () => {
    setModalVisible(true);
  };

  const handleModalConfirm = (selectedIds: number[]) => {
    const updatedSelectedTools = tools.filter((tool) => selectedIds.includes(tool.id));
    setSelectedTools(updatedSelectedTools);
    onChange(updatedSelectedTools);
    setModalVisible(false);
  };

  const handleModalCancel = () => {
    setModalVisible(false);
  };

  const removeSelectedTool = (toolId: number) => {
    const updatedSelectedTools = selectedTools.filter((tool) => tool.id !== toolId);
    setSelectedTools(updatedSelectedTools);
    onChange(updatedSelectedTools);
  };

  const openEditModal = (tool: SelectTool) => {
    setEditingTool(tool);
    if (isRedisTool(tool)) {
      const instances = parseRedisToolConfig(tool.kwargs);
      setRedisInstances(instances);
      setSelectedRedisInstanceId(instances[0]?.id || null);
    } else {
      form.setFieldsValue({
        kwargs: tool.kwargs?.map((item: any) => ({ key: item.key, value: item.value, type: item.type, isRequired: item.isRequired })) || [],
      });
    }
    setEditModalVisible(true);
  };

  const handleEditModalOk = () => {
    if (isRedisTool(editingTool)) {
      const trimmedNames = redisInstances.map((instance) => instance.name.trim()).filter(Boolean);
      if (redisInstances.length === 0) {
        message.error(t('tool.redis.noInstances'));
        return;
      }
      if (trimmedNames.length !== redisInstances.length) {
        message.error(t('tool.redis.instanceNameRequired'));
        return;
      }
      if (new Set(trimmedNames).size !== trimmedNames.length) {
        message.error(t('tool.redis.duplicateInstanceName'));
        return;
      }
      if (redisInstances.some((instance) => !instance.url.trim())) {
        message.error(t('tool.redis.urlRequired'));
        return;
      }
      if (editingTool) {
        const updatedTool = {
          ...editingTool,
          kwargs: serializeRedisToolConfig(redisInstances.map((instance) => ({ ...instance, name: instance.name.trim(), url: instance.url.trim() }))),
        };
        const updatedSelectedTools = selectedTools.map((tool) => (tool.id === editingTool.id ? updatedTool : tool));
        setSelectedTools(updatedSelectedTools);
        onChange(updatedSelectedTools);
      }
      setEditModalVisible(false);
      setEditingTool(null);
      return;
    }

    form.validateFields().then((values) => {
      if (editingTool) {
        const updatedTool = {
          ...editingTool,
          kwargs: values.kwargs,
        };
        const updatedSelectedTools = selectedTools.map((tool) => (tool.id === editingTool.id ? updatedTool : tool));
        setSelectedTools(updatedSelectedTools);
        onChange(updatedSelectedTools);
      }
      setEditModalVisible(false);
      setEditingTool(null);
    });
  };

  const handleEditModalCancel = () => {
    setEditModalVisible(false);
    setEditingTool(null);
    setRedisInstances([]);
    setSelectedRedisInstanceId(null);
  };

  const handleAddRedisInstance = () => {
    const nextInstance = getDefaultRedisInstance(getNextRedisInstanceName(redisInstances));
    setRedisInstances((prev) => [...prev, nextInstance]);
    setSelectedRedisInstanceId(nextInstance.id);
  };

  const handleDeleteRedisInstance = (instanceId: string) => {
    setRedisInstances((prev) => {
      const nextInstances = prev.filter((instance) => instance.id !== instanceId);
      if (selectedRedisInstanceId === instanceId) {
        setSelectedRedisInstanceId(nextInstances[0]?.id || null);
      }
      return nextInstances;
    });
  };

  const handleRedisInstanceChange = <K extends keyof RedisInstanceFormValue>(
    instanceId: string,
    field: K,
    value: RedisInstanceFormValue[K],
  ) => {
    setRedisInstances((prev) => prev.map((instance) => (
      instance.id === instanceId ? { ...instance, [field]: value, testStatus: 'untested' } : instance
    )));
  };

  const handleTestRedisInstance = async () => {
    const currentInstance = redisInstances.find((instance) => instance.id === selectedRedisInstanceId);
    if (!currentInstance) {
      return;
    }
    setTestingRedisConnection(true);
    try {
      const payload = { ...currentInstance };
      delete payload.testStatus;
      await testRedisConnection(payload);
      message.success(t('tool.redis.status.success'));
      setRedisInstances((prev) => prev.map((instance) => (
        instance.id === currentInstance.id ? { ...instance, testStatus: 'success' } : instance
      )));
    } catch {
      setRedisInstances((prev) => prev.map((instance) => (
        instance.id === currentInstance.id ? { ...instance, testStatus: 'failed' } : instance
      )));
    } finally {
      setTestingRedisConnection(false);
    }
  };

  return (
    <div>
      <Button onClick={openModal}>+ {t('common.add')}</Button>
      <div className="grid grid-cols-2 gap-4 mt-2 pb-2">
        {selectedTools.map((tool) => (
          <div key={tool.id} className={`w-full rounded-md px-4 py-2 flex items-center justify-between ${styles.borderContainer}`}>
            <Tooltip title={tool.name}>
              <div className='flex items-center'>
                <Icon className='text-xl mr-1' type={tool.icon} />
                <span className="inline-block text-ellipsis overflow-hidden whitespace-nowrap">{tool.name}</span>
              </div>
            </Tooltip>
            <div className="flex items-center space-x-2 text-[var(--color-text-3)]">
              <EditOutlined
                className="hover:text-[var(--color-primary)] transition-colors duration-200"
                onClick={() => openEditModal(tool)}
              />
              <DeleteOutlined
                className="hover:text-[var(--color-primary)] transition-colors duration-200"
                onClick={() => removeSelectedTool(tool.id)}
              />
            </div>
          </div>
        ))}
      </div>

      <SelectorOperateModal
        title={t('skill.selecteTool')}
        visible={modalVisible}
        okText={t('common.confirm')}
        cancelText={t('common.cancel')}
        loading={loading}
        options={tools}
        isNeedGuide={false}
        showToolDetail={true}
        selectedOptions={selectedTools.map((tool) => tool.id)}
        onOk={handleModalConfirm}
        onCancel={handleModalCancel}
      />

      <OperateModal
        title={t('common.edit')}
        visible={editModalVisible}
        onOk={handleEditModalOk}
        onCancel={handleEditModalCancel}
        okText={t('common.save')}
        cancelText={t('common.cancel')}
        width={isRedisTool(editingTool) ? 800 : undefined}
      >
        <Form form={form} layout="vertical">
          {isRedisTool(editingTool) ? (
            <RedisToolEditor
              instances={redisInstances}
              selectedInstanceId={selectedRedisInstanceId}
              testing={testingRedisConnection}
              onSelect={setSelectedRedisInstanceId}
              onAdd={handleAddRedisInstance}
              onDelete={handleDeleteRedisInstance}
              onChange={handleRedisInstanceChange}
              onTest={handleTestRedisInstance}
            />
          ) : (
            <Form.List name="kwargs">
              {(fields) => (
                <>
                  {fields.length === 0 && (
                    <Empty description={t('common.noData')} />
                  )}
                  {fields.map(({ key, name, fieldKey, ...restField }) => {
                    const fieldType = form.getFieldValue(['kwargs', name, 'type']);
                    const fieldLabel = form.getFieldValue(['kwargs', name, 'key']);
                    const isRequired = form.getFieldValue(['kwargs', name, 'isRequired']);

                    const renderInput = () => {
                      switch (fieldType) {
                        case 'text':
                          return <Input />;
                        case 'textarea':
                          return <TextArea rows={4} />;
                        case 'password':
                          return <EditablePasswordField />;
                        case 'number':
                          return <InputNumber style={{ width: '100%' }} />;
                        case 'checkbox':
                          return <Switch />;
                        default:
                          return <Input />;
                      }
                    };

                    return (
                      <Form.Item
                        key={key}
                        {...restField}
                        name={[name, 'value']}
                        fieldKey={[fieldKey ?? '', 'value']}
                        label={fieldLabel}
                        rules={[{ required: isRequired, message: `${t('common.inputMsg')}${fieldLabel}` }]}
                        valuePropName={fieldType === 'checkbox' ? 'checked' : 'value'}
                      >
                        {renderInput()}
                      </Form.Item>
                    );
                  })}
                </>
              )}
            </Form.List>
          )}
        </Form>
      </OperateModal>
    </div>
  );
};

export default ToolSelector;
