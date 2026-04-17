import { useCollectTypeConfig } from '@/app/log/hooks/integration/index';

export const useCollectTypeInfo = () => {
  const collectTypeConfigs = useCollectTypeConfig();
  const getIcon = (type: string, collector: string) => {
    return (
      collectTypeConfigs.getCollectTypeConfig({
        mode: 'auto',
        type,
        collector
      }).icon || 'cc-default_默认'
    );
  };
  return {
    getIcon
  };
};
