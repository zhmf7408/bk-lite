'use client';

import React from 'react';
import { Tooltip } from 'antd';
import WithSideMenuLayout from '@/components/sub-layout';
import { useRouter, useSearchParams } from 'next/navigation';
import type { MenuItem } from '@/types';

const IntegrationDetailLayout = ({
  children
}: {
  children: React.ReactNode;
}) => {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pluginDisplayName = searchParams.get('plugin_display_name');
  const desc = searchParams.get('plugin_description');
  const objId = searchParams.get('id') || '';
  const icon = searchParams.get('icon');
  const templateType = searchParams.get('template_type') || '';

  const handleBackButtonClick = () => {
    const params = new URLSearchParams({ objId });
    const targetUrl = `/monitor/integration/list?${params.toString()}`;
    router.push(targetUrl);
  };

  const TopSection = () => (
    <div className="p-4 rounded-md w-full h-[95px] flex items-center bg-[var(--color-bg-2)]">
      <div className="w-[72px] h-[72px] mr-[10px] min-w-[72px] rounded-lg flex items-center justify-center bg-[var(--color-fill-1)]">
        <img
          src={`/assets/icons/${icon}.svg`}
          alt="icon"
          className="w-[60px] h-[60px]"
          onError={(e) => {
            (e.target as HTMLImageElement).src =
              '/assets/icons/cc-default_默认.svg';
          }}
        />
      </div>
      <div className="w-full">
        <h2 className="text-lg font-semibold mb-2">{pluginDisplayName}</h2>
        <Tooltip title={desc}>
          <p className="truncate w-[95%] text-sm hide-text">{desc}</p>
        </Tooltip>
      </div>
    </div>
  );

  const detailMenuItems: MenuItem[] = [
    {
      name: 'configure',
      title: '配置',
      url: '/monitor/integration/list/detail/configure',
      icon: '',
      operation: []
    },
    {
      name: 'metric',
      title: '指标',
      url: '/monitor/integration/list/detail/metric',
      icon: '',
      operation: []
    },
    ...(templateType === 'snmp'
      ? [
          {
            name: 'collect',
            title: '采集',
            url: '/monitor/integration/list/detail/collect',
            icon: '',
            operation: []
          }
        ]
      : [])
  ];

  return (
    <WithSideMenuLayout
      topSection={<TopSection />}
      showBackButton={true}
      onBackButtonClick={handleBackButtonClick}
      layoutType="sideMenu"
      customMenuItems={detailMenuItems}
    >
      {children}
    </WithSideMenuLayout>
  );
};

export default IntegrationDetailLayout;
