'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Button, Input, message, Switch } from 'antd';
import { CheckOutlined, CloseOutlined, CopyOutlined, EditOutlined } from '@ant-design/icons';
import TopSection from '@/components/top-section';
import { useTranslation } from '@/utils/i18n';
import { useSettingsApi } from '@/app/system-manager/api/settings';
import PortalConsolePreview from '@/app/system-manager/components/settings/PortalConsolePreview';
import { emitPortalBrandingUpdated, portalBrandingDefaults } from '@/hooks/usePortalBranding';

const DEFAULT_PORTAL_NAME = 'BlueKing Lite';
const DEFAULT_WATERMARK_TEXT = 'BlueKing Lite · ${username} · ${date}';
const MAX_UPLOAD_SIZE = 512 * 1024;
const LOGO_ACCEPT = '.png,.jpg,.jpeg,.webp,.svg';
const FAVICON_ACCEPT = '.png,.jpg,.jpeg,.webp,.svg,.ico';
const SUPPORTED_IMAGE_TYPES = new Set([
  'image/png',
  'image/jpeg',
  'image/webp',
  'image/svg+xml',
  'image/x-icon',
  'image/vnd.microsoft.icon',
]);

const toPortalBrandingState = (portalName: string, portalLogoUrl: string, portalFaviconUrl: string) => ({
  portalName,
  logoUrl: portalLogoUrl,
  faviconUrl: portalFaviconUrl,
});

const toWatermarkState = (watermarkEnabled: boolean, watermarkText: string) => ({
  watermarkEnabled,
  watermarkText,
});

const readFileAsDataUrl = (file: File) => new Promise<string>((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => {
    if (typeof reader.result === 'string') {
      resolve(reader.result);
      return;
    }

    reject(new Error('Invalid file result'));
  };
  reader.onerror = () => reject(reader.error || new Error('Failed to read file'));
  reader.readAsDataURL(file);
});

const PortalSettingsHeaderIcon = () => (
  <div className="flex h-13 w-13 items-center justify-center rounded-lg bg-[linear-gradient(180deg,#5f95ff_0%,#3f79ee_100%)] shadow-[0_12px_24px_rgba(53,110,230,0.22)]">
    <svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path
        d="M15 5.5C16.1508 10.1774 18.8226 12.8492 23.5 14C18.8226 15.1508 16.1508 17.8226 15 22.5C13.8492 17.8226 11.1774 15.1508 6.5 14C11.1774 12.8492 13.8492 10.1774 15 5.5Z"
        fill="white"
      />
      <path
        d="M21.7 8.4C22.1915 10.3977 23.3023 11.5085 25.3 12C23.3023 12.4915 22.1915 13.6023 21.7 15.6C21.2085 13.6023 20.0977 12.4915 18.1 12C20.0977 11.5085 21.2085 10.3977 21.7 8.4Z"
        fill="white"
        fillOpacity="0.82"
      />
    </svg>
  </div>
);

const PortalSettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const { getPortalSettings, updatePortalSettings } = useSettingsApi();
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [portalName, setPortalName] = useState(DEFAULT_PORTAL_NAME);
  const [portalNameDraft, setPortalNameDraft] = useState(DEFAULT_PORTAL_NAME);
  const [portalLogoUrl, setPortalLogoUrl] = useState(portalBrandingDefaults.logoUrl);
  const [portalFaviconUrl, setPortalFaviconUrl] = useState(portalBrandingDefaults.faviconUrl);
  const [watermarkText, setWatermarkText] = useState(DEFAULT_WATERMARK_TEXT);
  const [watermarkTextDraft, setWatermarkTextDraft] = useState(DEFAULT_WATERMARK_TEXT);
  const [watermarkEnabled, setWatermarkEnabled] = useState(false);
  const [editingField, setEditingField] = useState<'portalName' | 'watermarkText' | null>(null);
  const hasInitializedSettings = useRef(false);
  const logoInputRef = useRef<HTMLInputElement | null>(null);
  const faviconInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (hasInitializedSettings.current) {
      return;
    }

    const fetchSettings = async () => {
      try {
        const settings = await getPortalSettings();
        const nextPortalName = settings.portal_name || DEFAULT_PORTAL_NAME;
        const nextPortalLogoUrl = settings.portal_logo_url?.trim() || portalBrandingDefaults.logoUrl;
        const nextPortalFaviconUrl = settings.portal_favicon_url?.trim() || portalBrandingDefaults.faviconUrl;
        const nextWatermarkText = settings.watermark_text || DEFAULT_WATERMARK_TEXT;
        const nextWatermarkEnabled = settings.watermark_enabled === '1';

        setPortalName(nextPortalName);
        setPortalNameDraft(nextPortalName);
        setPortalLogoUrl(nextPortalLogoUrl);
        setPortalFaviconUrl(nextPortalFaviconUrl);
        setWatermarkText(nextWatermarkText);
        setWatermarkTextDraft(nextWatermarkText);
        setWatermarkEnabled(nextWatermarkEnabled);
        hasInitializedSettings.current = true;
      } catch {
        message.error(t('common.fetchFailed'));
      }
    };

    fetchSettings();
  }, [getPortalSettings, t]);

  const syncPortalBranding = (nextPortalName: string, nextPortalLogoUrl: string, nextPortalFaviconUrl: string) => {
    emitPortalBrandingUpdated(toPortalBrandingState(nextPortalName, nextPortalLogoUrl, nextPortalFaviconUrl));
  };

  const handleFieldSave = async (key: 'portal_name' | 'watermark_text', value: string) => {
    const normalizedValue = value.trim();
    if (!normalizedValue) {
      message.error(key === 'portal_name' ? t('system.settings.portal.placeholderName') : t('system.settings.portal.placeholderWatermark'));
      return;
    }

    try {
      setSavingKey(key);
      await updatePortalSettings({ [key]: normalizedValue });
      if (key === 'portal_name') {
        setPortalName(normalizedValue);
        setPortalNameDraft(normalizedValue);
        syncPortalBranding(normalizedValue, portalLogoUrl, portalFaviconUrl);
      } else {
        setWatermarkText(normalizedValue);
        setWatermarkTextDraft(normalizedValue);
        emitPortalBrandingUpdated(toWatermarkState(watermarkEnabled, normalizedValue));
      }
      setEditingField(null);
      message.success(t('system.settings.portal.saveSuccess'));
    } catch {
      message.error(t('common.saveFailed'));
    } finally {
      setSavingKey(null);
    }
  };

  const handleWatermarkToggle = async (checked: boolean) => {
    const previousValue = watermarkEnabled;
    setWatermarkEnabled(checked);

    try {
      setSavingKey('watermark_enabled');
      await updatePortalSettings({ watermark_enabled: checked ? '1' : '0' });
      emitPortalBrandingUpdated(toWatermarkState(checked, watermarkText));
      message.success(t('system.settings.portal.saveSuccess'));
    } catch {
      setWatermarkEnabled(previousValue);
      message.error(t('common.saveFailed'));
    } finally {
      setSavingKey(null);
    }
  };

  const handleCopy = async (value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      message.success(t('common.copySuccess'));
    } catch {
      message.error(t('common.copyFailed'));
    }
  };

  const validateImageFile = (file: File, allowIco: boolean) => {
    const isSupportedType = SUPPORTED_IMAGE_TYPES.has(file.type) || (!file.type && /\.(png|jpe?g|webp|svg|ico)$/i.test(file.name));
    const isIcoAllowed = allowIco || !/\.ico$/i.test(file.name);

    if (!isSupportedType || !isIcoAllowed) {
      message.error(t('system.settings.portal.invalidImageType'));
      return false;
    }

    if (file.size > MAX_UPLOAD_SIZE) {
      message.error(t('system.settings.portal.uploadTooLarge'));
      return false;
    }

    return true;
  };

  const handleAssetUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
    key: 'portal_logo_url' | 'portal_favicon_url'
  ) => {
    const file = event.target.files?.[0];
    event.target.value = '';

    if (!file) {
      return;
    }

    const allowIco = key === 'portal_favicon_url';
    if (!validateImageFile(file, allowIco)) {
      return;
    }

    try {
      setSavingKey(key);
      const dataUrl = await readFileAsDataUrl(file);
      await updatePortalSettings({ [key]: dataUrl });

      if (key === 'portal_logo_url') {
        setPortalLogoUrl(dataUrl);
        syncPortalBranding(portalName, dataUrl, portalFaviconUrl);
      } else {
        setPortalFaviconUrl(dataUrl);
        syncPortalBranding(portalName, portalLogoUrl, dataUrl);
      }

      message.success(t('system.settings.portal.uploadSuccess'));
    } catch {
      message.error(t('common.saveFailed'));
    } finally {
      setSavingKey(null);
    }
  };

  const handleRestoreDefault = async (key: 'portal_logo_url' | 'portal_favicon_url') => {
    const nextLogoUrl = key === 'portal_logo_url' ? portalBrandingDefaults.logoUrl : portalLogoUrl;
    const nextFaviconUrl = key === 'portal_favicon_url' ? portalBrandingDefaults.faviconUrl : portalFaviconUrl;

    try {
      setSavingKey(key);
      await updatePortalSettings({ [key]: '' });

      if (key === 'portal_logo_url') {
        setPortalLogoUrl(portalBrandingDefaults.logoUrl);
      } else {
        setPortalFaviconUrl(portalBrandingDefaults.faviconUrl);
      }

      syncPortalBranding(portalName, nextLogoUrl, nextFaviconUrl);
      message.success(t('system.settings.portal.restoreSuccess'));
    } catch {
      message.error(t('common.saveFailed'));
    } finally {
      setSavingKey(null);
    }
  };

  const variableRows = useMemo(() => ([
    { label: t('system.user.form.username'), value: '${username}' },
    { label: t('system.settings.portal.variableChineseName'), value: '${chname}' },
    { label: t('system.user.form.email'), value: '${email}' },
    { label: t('system.settings.portal.variablePhone'), value: '${phone}' },
    { label: t('system.settings.portal.variableDate'), value: '${date}' },
  ]), [t]);

  return (
    <div>
      <div className="mb-4">
        <TopSection
          title={t('system.settings.portal.title')}
          content={t('system.settings.portal.content')}
          icon={<PortalSettingsHeaderIcon />}
        />
      </div>

      <div className="grid grid-cols-[minmax(0,1fr)_520px] gap-4 max-[1280px]:grid-cols-1">
        <div>
          <section className="mb-4 rounded-[14px] border border-(--color-border-1) bg-(--color-bg) p-4 shadow-[0_10px_28px_var(--color-portal-card-shadow)]">
            <div className="mb-4 text-base font-semibold text-(--color-text-1)">{t('system.settings.portal.basic')}</div>

            <div className="mb-4 grid grid-cols-1 gap-2">
              <div className="text-[13px] font-semibold text-(--color-text-1)">{t('system.settings.portal.portalName')}</div>
              <div className="flex items-center gap-2 max-[900px]:flex-wrap">
                <Input
                  value={portalNameDraft}
                  readOnly={editingField !== 'portalName'}
                  onChange={(event) => setPortalNameDraft(event.target.value)}
                  placeholder={t('system.settings.portal.placeholderName')}
                  className="h-10 rounded-[10px]"
                />
                {editingField === 'portalName' ? (
                  <div className="flex items-center gap-2">
                    <Button
                      type="primary"
                      icon={<CheckOutlined />}
                      loading={savingKey === 'portal_name'}
                      onClick={() => handleFieldSave('portal_name', portalNameDraft)}
                    >
                      {t('common.confirm')}
                    </Button>
                    <Button
                      icon={<CloseOutlined />}
                      onClick={() => {
                        setPortalNameDraft(portalName);
                        setEditingField(null);
                      }}
                    >
                      {t('common.cancel')}
                    </Button>
                  </div>
                ) : (
                  <Button type="text" icon={<EditOutlined className="text-(--color-primary)" />} onClick={() => setEditingField('portalName')} />
                )}
              </div>
              <div className="text-xs text-(--color-text-3)">{t('system.settings.portal.portalNameHint')}</div>
            </div>

            <div className="my-6 h-px bg-(--color-border-1)" />

            <div>
              <div className="mb-3 text-[14px] font-semibold text-(--color-text-1)">{t('system.settings.portal.logo')}</div>
              <div className="grid grid-cols-2 gap-3 max-[900px]:grid-cols-1">
                <div className="overflow-hidden rounded-xl border border-(--color-border-1) bg-(--color-bg-1)">
                  <div className="flex min-h-36 items-center justify-center border-b border-(--color-border-1) bg-[linear-gradient(135deg,var(--color-portal-surface-soft)_0%,var(--color-portal-surface-soft-2)_100%)] p-4">
                    <div className="flex min-h-20 w-full items-center justify-center gap-3 rounded-[14px] border border-dashed border-(--color-border-3) bg-(--color-portal-surface-overlay)">
                      <img src={portalLogoUrl} alt={t('system.settings.portal.portalLogo')} className="max-h-16 w-auto object-contain" />
                    </div>
                  </div>
                  <div className="p-4">
                    <div className="mb-1 text-[15px] font-semibold text-(--color-text-1)">{t('system.settings.portal.portalLogo')}</div>
                    <div className="mb-3 text-xs text-(--color-text-3)">{t('system.settings.portal.portalLogoHint')}</div>
                    <div className="flex gap-2">
                      <input
                        ref={logoInputRef}
                        type="file"
                        accept={LOGO_ACCEPT}
                        className="hidden"
                        onChange={(event) => void handleAssetUpload(event, 'portal_logo_url')}
                      />
                      <Button loading={savingKey === 'portal_logo_url'} onClick={() => logoInputRef.current?.click()}>{t('system.settings.portal.uploadLogo')}</Button>
                      <Button loading={savingKey === 'portal_logo_url'} onClick={() => void handleRestoreDefault('portal_logo_url')}>{t('system.settings.portal.restoreDefault')}</Button>
                    </div>
                  </div>
                </div>

                <div className="overflow-hidden rounded-xl border border-(--color-border-1) bg-(--color-bg-1)">
                  <div className="flex min-h-36 items-center justify-center border-b border-(--color-border-1) bg-[linear-gradient(135deg,var(--color-portal-surface-soft)_0%,var(--color-portal-surface-soft-2)_100%)] p-4">
                    <div className="flex w-full flex-col items-center gap-3.5">
                      <img src={portalFaviconUrl} alt={t('system.settings.portal.browserFavicon')} className="h-16 w-16 rounded-[18px] object-contain" />
                      <div className="w-full max-w-55 overflow-hidden rounded-xl border border-(--color-border-1) bg-(--color-bg-1)">
                        <div className="flex h-7.5 items-center gap-2 bg-(--color-portal-preview-tab-bg) px-2.5 text-[12px] text-(--color-text-2)">
                          <img src={portalFaviconUrl} alt={t('system.settings.portal.browserFavicon')} className="h-3.5 w-3.5 rounded-[5px] object-contain" />
                          <span className="truncate">{portalName}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="p-4">
                    <div className="mb-1 text-[15px] font-semibold text-(--color-text-1)">{t('system.settings.portal.browserFavicon')}</div>
                    <div className="mb-3 text-xs text-(--color-text-3)">{t('system.settings.portal.browserFaviconHint')}</div>
                    <div className="flex gap-2">
                      <input
                        ref={faviconInputRef}
                        type="file"
                        accept={FAVICON_ACCEPT}
                        className="hidden"
                        onChange={(event) => void handleAssetUpload(event, 'portal_favicon_url')}
                      />
                      <Button loading={savingKey === 'portal_favicon_url'} onClick={() => faviconInputRef.current?.click()}>{t('system.settings.portal.uploadFavicon')}</Button>
                      <Button loading={savingKey === 'portal_favicon_url'} onClick={() => void handleRestoreDefault('portal_favicon_url')}>{t('system.settings.portal.restoreDefault')}</Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className="rounded-[14px] border border-(--color-border-1) bg-(--color-bg) p-4 shadow-[0_10px_28px_var(--color-portal-card-shadow)]">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="text-base font-semibold text-(--color-text-1)">{t('system.settings.portal.watermark')}</div>
              <div className={`inline-flex h-7.5 items-center gap-2 rounded-full border px-2.5 pl-1.5 text-[12px] ${watermarkEnabled ? 'border-(--color-border-3) bg-(--color-primary-bg-active) text-(--color-primary)' : 'border-(--color-border-1) bg-(--color-fill-1) text-(--color-text-2)'}`}>
                <Switch checked={watermarkEnabled} loading={savingKey === 'watermark_enabled'} size="small" onChange={handleWatermarkToggle} />
                <span>{watermarkEnabled ? t('system.settings.portal.enabled') : t('system.settings.portal.disabled')}</span>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-2">
              <div className="text-[13px] font-semibold text-(--color-text-1)">{t('system.settings.portal.watermarkText')}</div>
              <div className="flex items-center gap-2 max-[900px]:flex-wrap">
                <Input
                  value={watermarkTextDraft}
                  readOnly={editingField !== 'watermarkText'}
                  onChange={(event) => setWatermarkTextDraft(event.target.value)}
                  placeholder={t('system.settings.portal.placeholderWatermark')}
                  className="h-10 rounded-[10px]"
                />
                {editingField === 'watermarkText' ? (
                  <div className="flex items-center gap-2">
                    <Button
                      type="primary"
                      icon={<CheckOutlined />}
                      loading={savingKey === 'watermark_text'}
                      onClick={() => handleFieldSave('watermark_text', watermarkTextDraft)}
                    >
                      {t('common.confirm')}
                    </Button>
                    <Button
                      icon={<CloseOutlined />}
                      onClick={() => {
                        setWatermarkTextDraft(watermarkText);
                        setEditingField(null);
                      }}
                    >
                      {t('common.cancel')}
                    </Button>
                  </div>
                ) : (
                  <Button type="text" icon={<EditOutlined className="text-(--color-primary)" />} onClick={() => setEditingField('watermarkText')} />
                )}
              </div>
              <div className="text-xs text-(--color-text-3)">{t('system.settings.portal.watermarkTextHint')}</div>
            </div>

            <div className="mt-5 text-[13px] font-semibold text-(--color-text-1)">{t('system.settings.portal.availableVariables')}</div>
            <div className="mt-3 overflow-hidden rounded-[10px] border border-(--color-border-1) bg-(--color-bg-1)">
              {variableRows.map((row, index) => (
                <div key={row.value} className={`grid grid-cols-[1fr_auto] items-center gap-4 px-4 py-3 ${index !== variableRows.length - 1 ? 'border-b border-(--color-border-1)' : ''}`}>
                  <span className="text-[13px] text-(--color-text-2)">{row.label}</span>
                  <button
                    type="button"
                    onClick={() => handleCopy(row.value)}
                    className="inline-flex items-center gap-2 text-[13px] text-(--color-text-2) transition-colors hover:text-(--color-primary)"
                  >
                    <span>{row.value}</span>
                    <CopyOutlined />
                  </button>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="sticky top-3 self-start max-[1280px]:static">
          <PortalConsolePreview
            portalName={portalName}
            portalFaviconUrl={portalFaviconUrl}
            watermarkEnabled={watermarkEnabled}
            watermarkText={watermarkText}
          />
        </div>
      </div>
    </div>
  );
};

export default PortalSettingsPage;
