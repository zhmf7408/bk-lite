'use client';

import React, { useState } from 'react';
import { Steps } from 'antd';
import { useTranslation } from '@/utils/i18n';
import AccessConfig from './accessConfig';
import CollectorInstall from './collectorInstall';
import AccessComplete from './accessComplete';

export interface K8sCommandData {
  command?: string;
  cloud_region_id?: React.Key;
  instance_id?: string;
  runtime_profile?: 'standard' | 'docker' | 'custom';
  host_log_path?: string;
  docker_container_log_path?: string;
}

const K8sConfiguration: React.FC = () => {
  const { t } = useTranslation();
  const [currentStep, setCurrentStep] = useState(0);
  const [commandData, setCommandData] = useState<K8sCommandData | null>(null);

  const handleNext = (data?: K8sCommandData) => {
    if (data) {
      setCommandData(data);
    }
    setCurrentStep((prev) => prev + 1);
  };

  const handlePrev = () => {
    setCurrentStep((prev) => prev - 1);
  };

  const handleReset = () => {
    setCurrentStep(0);
    setCommandData(null);
  };

  const steps = [
    {
      title: t('log.integration.k8s.accessConfig'),
      component: <AccessConfig onNext={handleNext} commandData={commandData} />,
    },
    {
      title: t('log.integration.k8s.collectorInstall'),
      component: (
        <CollectorInstall
          onNext={handleNext}
          onPrev={handlePrev}
          commandData={commandData}
        />
      ),
    },
    {
      title: t('log.integration.k8s.accessComplete'),
      component: <AccessComplete onReset={handleReset} />,
    },
  ];

  return (
    <div className="w-full">
      <div className="p-[10px]">
        <div className="mb-8 px-[20px]">
          <Steps current={currentStep} size="default">
            {steps.map((step, index) => (
              <Steps.Step key={index} title={step.title} />
            ))}
          </Steps>
        </div>
        <div>{steps[currentStep].component}</div>
      </div>
    </div>
  );
};

export default K8sConfiguration;
