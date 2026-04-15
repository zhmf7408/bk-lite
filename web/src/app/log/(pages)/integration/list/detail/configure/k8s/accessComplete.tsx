'use client';

import React from 'react';
import { Button } from 'antd';
import { useRouter } from 'next/navigation';
import { useTranslation } from '@/utils/i18n';
import Icon from '@/components/icon';

interface AccessCompleteProps {
  onReset: () => void;
}

const AccessComplete: React.FC<AccessCompleteProps> = ({ onReset }) => {
  const { t } = useTranslation();
  const router = useRouter();

  return (
    <div className="py-8 flex flex-col items-center text-center">
      <Icon type="duihaochenggong" className="text-[56px] text-[var(--color-success)] mb-4" />
      <h2 className="text-xl font-semibold mb-2">
        {t('log.integration.k8s.accessCompleteTitle')}
      </h2>
      <p className="text-[var(--color-text-2)] mb-2">
        {t('log.integration.k8s.accessCompleteDesc')}
      </p>
      <p className="text-[var(--color-text-3)] mb-8">
        {t('log.integration.k8s.accessCompleteSubDesc')}
      </p>
      <div className="flex gap-3">
        <Button type="primary" onClick={() => router.push('/log/integration/receive')}>
          {t('log.integration.k8s.viewClusterList')}
        </Button>
        <Button onClick={onReset}>{t('log.integration.k8s.addAnotherCluster')}</Button>
      </div>
    </div>
  );
};

export default AccessComplete;
