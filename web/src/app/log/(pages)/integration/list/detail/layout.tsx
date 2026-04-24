'use client';

import React, { useMemo } from 'react';
import { Tooltip } from 'antd';
import WithSideMenuLayout from '@/components/sub-layout';
import { useRouter, useSearchParams } from 'next/navigation';
import { useTranslation } from '@/utils/i18n';
import { MenuItem } from '@/types/index';

const IntegrationDetailLayout = ({
  children
}: {
  children: React.ReactNode;
}) => {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { t } = useTranslation();
  const pluginDisplayName = searchParams.get('display_name');
  const desc = searchParams.get('description');
  const icon = searchParams.get('icon');
  const pluginName = searchParams.get('name');
  const isK8s = useMemo(() => pluginName === 'kubernetes', [pluginName]);

  const handleBackButtonClick = () => {
    // const params = new URLSearchParams({ id });
    // const targetUrl = `/log/integration/list?${params.toString()}`;
    router.push('/log/integration/list');
  };

  const TopSection = () => (
    <div className="p-4 rounded-md w-full h-[80px] flex items-center bg-[var(--color-bg-1)]">
      <img
        src={`/assets/icons/${icon}.svg`}
        alt={pluginDisplayName || ''}
        className="w-[60px] h-[60px] mr-[10px] min-w-[60px]"
        onError={(e) => {
          (e.target as HTMLImageElement).src =
            '/assets/icons/cc-default_默认.svg';
        }}
      />
      <div className="w-full">
        <h2 className="text-lg font-semibold mb-2">{pluginDisplayName}</h2>
        <Tooltip title={desc}>
          <p className="truncate w-[95%] text-sm hide-text">{desc}</p>
        </Tooltip>
      </div>
    </div>
  );

  const customMenuItems: MenuItem[] | undefined = useMemo(() => {
    if (!isK8s) return undefined;
    return [
      {
        title: t('log.integration.configuration'),
        icon: 'settings-fill',
        url: '/log/integration/list/detail/configure',
        name: 'integration_configure',
        operation: []
      }
    ];
  }, [isK8s, t]);

  return (
    <WithSideMenuLayout
      topSection={<TopSection />}
      showBackButton={true}
      onBackButtonClick={handleBackButtonClick}
      layoutType={'sideMenu'}
      customMenuItems={customMenuItems}
    >
      {children}
    </WithSideMenuLayout>
  );
};

export default IntegrationDetailLayout;
