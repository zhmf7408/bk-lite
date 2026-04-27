import { useTranslation } from '@/utils/i18n';
import { v4 as uuidv4 } from 'uuid';

export const useFileDashboard = () => {
  const { t } = useTranslation();

  return {
    name: t('log.analysis.file.dashboardName'),
    desc: '',
    id: '2',
    category: 'general',
    categoryName: t('log.analysis.category.general'),
    collectTypeName: 'file',
    filters: {},
    other: {},
    view_sets: [
      {
        h: 3,
        w: 9,
        x: 0,
        y: 0,
        i: uuidv4(),
        name: t('log.analysis.file.logVolumeTrend'),
        moved: false,
        static: false,
        description: t('log.analysis.file.logVolumeTrendDesc'),
        valueConfig: {
          chartType: 'line',
          dataSource: 1,
          displayMaps: {
            type: 'single',
            key: 'logcount',
            value: 'logcount',
            tooltipField: 'logcount'
          },
          dataSourceParams: {
            query:
              'collect_type:"file" | stats by (_time:${_time}) count() as logcount'
          }
        }
      },
      {
        h: 3,
        w: 3,
        x: 9,
        y: 0,
        i: uuidv4(),
        name: t('log.analysis.file.totalLogCount'),
        moved: false,
        static: false,
        description: t('log.analysis.file.totalLogCountDesc'),
        valueConfig: {
          chartType: 'single',
          dataSource: 1,
          displayMaps: {
            type: 'single',
            key: 'logcount',
            value: 'logcount',
            tooltipField: 'logcount'
          },
          dataSourceParams: {
            query: 'collect_type:"file" | stats count() as logcount'
          }
        }
      },
      {
        h: 3,
        w: 6,
        x: 0,
        y: 3,
        i: uuidv4(),
        name: t('log.analysis.file.hostDistribution'),
        moved: false,
        static: false,
        description: t('log.analysis.file.hostDistributionDesc'),
        valueConfig: {
          chartType: 'pie',
          dataSource: 1,
          displayMaps: {
            type: 'single',
            key: 'host.name',
            value: 'logcount',
            tooltipField: 'host.name'
          },
          dataSourceParams: {
            query:
              'collect_type:"file" | stats by (host.name) count() as logcount | sort by (logcount desc) | limit 10'
          }
        }
      },
      {
        h: 4,
        w: 12,
        x: 0,
        y: 6,
        i: uuidv4(),
        name: t('log.analysis.file.topLogFiles'),
        moved: false,
        static: false,
        description: t('log.analysis.file.topLogFilesDesc'),
        valueConfig: {
          chartType: 'table',
          dataSource: 1,
          columns: [
            {
              title: t('log.analysis.file.logFilePath'),
              dataIndex: 'log.file.path',
              key: 'log.file.path'
            },
            {
              title: t('log.analysis.file.hostName'),
              dataIndex: 'host.name',
              key: 'host.name'
            },
            {
              title: t('log.analysis.file.logCount'),
              dataIndex: 'logcount',
              key: 'logcount'
            }
          ],
          dataSourceParams: {
            query:
              'collect_type:"file" | stats by (log.file.path, host.name) count() as logcount | sort by (logcount desc) | limit 20'
          }
        }
      }
    ]
  };
};
