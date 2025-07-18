import React from 'react';
import { Form, Input, InputNumber, Select } from 'antd';
import { useTranslation } from '@/utils/i18n';
import { TIMEOUT_UNITS } from '@/app/monitor/constants/monitor';
import Password from '@/app/monitor/components/password';

const { Option } = Select;
const useSnmpCommonFormItems = () => {
  const { t } = useTranslation();

  return {
    getCommonFormItems: (disabledFormItems: Record<string, boolean> = {}) => {
      return (
        <>
          <Form.Item required label={t('monitor.intergrations.port')}>
            <Form.Item
              noStyle
              name="port"
              rules={[
                {
                  required: true,
                  message: t('common.required'),
                },
              ]}
            >
              <InputNumber
                disabled={disabledFormItems.port}
                className="w-[300px] mr-[10px]"
                min={1}
                precision={0}
              />
            </Form.Item>
            <span className="text-[12px] text-[var(--color-text-3)]">
              {t('monitor.intergrations.portDes')}
            </span>
          </Form.Item>
          <Form.Item required label={t('monitor.intergrations.version')}>
            <Form.Item
              noStyle
              name="version"
              rules={[
                {
                  required: true,
                  message: t('common.required'),
                },
              ]}
            >
              <Select
                disabled={disabledFormItems.version}
                showSearch
                className="mr-[10px]"
                style={{ width: '300px' }}
              >
                <Option value={2}>v2c</Option>
                <Option value={3}>v3</Option>
              </Select>
            </Form.Item>
            <span className="text-[12px] text-[var(--color-text-3)]">
              {t('monitor.intergrations.versionDes')}
            </span>
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.version !== currentValues.version
            }
          >
            {({ getFieldValue }) =>
              getFieldValue('version') === 2 ? (
                <Form.Item
                  required
                  label={t('monitor.intergrations.community')}
                >
                  <Form.Item
                    noStyle
                    name="community"
                    rules={[
                      {
                        required: true,
                        message: t('common.required'),
                      },
                    ]}
                  >
                    <Input className="w-[300px] mr-[10px]" />
                  </Form.Item>
                  <span className="text-[12px] text-[var(--color-text-3)]">
                    {t('monitor.intergrations.communityDes')}
                  </span>
                </Form.Item>
              ) : (
                <>
                  <Form.Item required label={t('common.name')}>
                    <Form.Item
                      noStyle
                      name="sec_name"
                      rules={[
                        {
                          required: true,
                          message: t('common.required'),
                        },
                      ]}
                    >
                      <Input className="w-[300px] mr-[10px]" />
                    </Form.Item>
                    <span className="text-[12px] text-[var(--color-text-3)]">
                      {t('monitor.intergrations.nameDes')}
                    </span>
                  </Form.Item>
                  <Form.Item required label={t('monitor.events.level')}>
                    <Form.Item
                      noStyle
                      name="sec_level"
                      rules={[
                        {
                          required: true,
                          message: t('common.required'),
                        },
                      ]}
                    >
                      <Select
                        showSearch
                        className="mr-[10px]"
                        style={{ width: '300px' }}
                      >
                        <Option value="noAuthNoPriv">noAuthNoPriv</Option>
                        <Option value="authNoPriv">authNoPriv</Option>
                        <Option value="authPriv">authPriv</Option>
                      </Select>
                    </Form.Item>
                    <span className="text-[12px] text-[var(--color-text-3)]">
                      {t('monitor.intergrations.levelDes')}
                    </span>
                  </Form.Item>
                  <Form.Item
                    required
                    label={t('monitor.intergrations.authProtocol')}
                  >
                    <Form.Item
                      noStyle
                      name="auth_protocol"
                      rules={[
                        {
                          required: true,
                          message: t('common.required'),
                        },
                      ]}
                    >
                      <Input className="w-[300px] mr-[10px]" />
                    </Form.Item>
                    <span className="text-[12px] text-[var(--color-text-3)]">
                      {t('monitor.intergrations.authProtocolDes')}
                    </span>
                  </Form.Item>
                  <Form.Item
                    required
                    label={t('monitor.intergrations.authPassword')}
                  >
                    <Form.Item
                      noStyle
                      name="auth_password"
                      rules={[
                        {
                          required: true,
                          message: t('common.required'),
                        },
                      ]}
                    >
                      <Password
                        disabled={disabledFormItems.auth_password}
                        className="w-[300px] mr-[10px]"
                      />
                    </Form.Item>
                    <span className="text-[12px] text-[var(--color-text-3)]">
                      {t('monitor.intergrations.authPasswordDes')}
                    </span>
                  </Form.Item>
                  <Form.Item
                    required
                    label={t('monitor.intergrations.privProtocol')}
                  >
                    <Form.Item
                      noStyle
                      name="priv_protocol"
                      rules={[
                        {
                          required: true,
                          message: t('common.required'),
                        },
                      ]}
                    >
                      <Input className="w-[300px] mr-[10px]" />
                    </Form.Item>
                    <span className="text-[12px] text-[var(--color-text-3)]">
                      {t('monitor.intergrations.privProtocolDes')}
                    </span>
                  </Form.Item>
                  <Form.Item
                    required
                    label={t('monitor.intergrations.privPassword')}
                  >
                    <Form.Item
                      noStyle
                      name="priv_password"
                      rules={[
                        {
                          required: true,
                          message: t('common.required'),
                        },
                      ]}
                    >
                      <Password
                        className="w-[300px] mr-[10px]"
                        disabled={disabledFormItems.priv_password}
                      />
                    </Form.Item>
                    <span className="text-[12px] text-[var(--color-text-3)]">
                      {t('monitor.intergrations.privPasswordDes')}
                    </span>
                  </Form.Item>
                </>
              )
            }
          </Form.Item>
          <Form.Item required label={t('monitor.intergrations.timeout')}>
            <Form.Item
              noStyle
              name="timeout"
              rules={[
                {
                  required: true,
                  message: t('common.required'),
                },
              ]}
            >
              <InputNumber
                className="mr-[10px]"
                min={1}
                precision={0}
                addonAfter={
                  <Select style={{ width: 116 }} defaultValue="s">
                    {TIMEOUT_UNITS.map((item: string) => (
                      <Option key={item} value={item}>
                        {item}
                      </Option>
                    ))}
                  </Select>
                }
              />
            </Form.Item>
            <span className="text-[12px] text-[var(--color-text-3)]">
              {t('monitor.intergrations.timeoutDes')}
            </span>
          </Form.Item>
        </>
      );
    },
  };
};
export { useSnmpCommonFormItems };
