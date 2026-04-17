'use client';

import React from 'react';
import { Tooltip } from 'antd';
import WithSideMenuLayout from '@/components/sub-layout';
import { useRouter, useSearchParams } from 'next/navigation';

const IntegrationDetailLayout = ({
  children
}: {
  children: React.ReactNode;
}) => {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pluginDisplayName = searchParams.get('display_name');
  const desc = searchParams.get('description');
  const icon = searchParams.get('icon');

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

  return (
    <WithSideMenuLayout
      topSection={<TopSection />}
      showBackButton={true}
      onBackButtonClick={handleBackButtonClick}
      layoutType={'sideMenu'}
    >
      {children}
    </WithSideMenuLayout>
  );
};

export default IntegrationDetailLayout;
