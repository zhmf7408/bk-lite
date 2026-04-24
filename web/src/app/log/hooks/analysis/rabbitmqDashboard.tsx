import { useTranslation } from '@/utils/i18n';
import { v4 as uuidv4 } from 'uuid';

export const useRabbitmqDashboard = () => {
  const { t } = useTranslation();

  return {
    name: t('log.analysis.rabbitmq.dashboardName'),
    desc: '',
    id: '3',
    category: 'middleware',
    categoryName: t('log.analysis.category.middleware'),
    collectTypeName: 'rabbitmq',
    filters: {},
    other: {},
    view_sets: [
      {
        h: 3,
        w: 9,
        x: 0,
        y: 0,
        i: uuidv4(),
        name: t('log.analysis.rabbitmq.logVolumeTrend'),
        moved: false,
        static: false,
        description: t('log.analysis.rabbitmq.logVolumeTrendDesc'),
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
              'collect_type:"rabbitmq" | stats by (_time:${_time}) count() as logcount'
          }
        }
      },
      {
        h: 3,
        w: 3,
        x: 9,
        y: 0,
        i: uuidv4(),
        name: t('log.analysis.rabbitmq.totalLogCount'),
        moved: false,
        static: false,
        description: t('log.analysis.rabbitmq.totalLogCountDesc'),
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
            query: 'collect_type:"rabbitmq" | stats count() as logcount'
          }
        }
      },
      {
        h: 3,
        w: 6,
        x: 0,
        y: 3,
        i: uuidv4(),
        name: t('log.analysis.rabbitmq.logLevelDistribution'),
        moved: false,
        static: false,
        description: t('log.analysis.rabbitmq.logLevelDistributionDesc'),
        valueConfig: {
          chartType: 'pie',
          dataSource: 1,
          displayMaps: {
            type: 'single',
            key: 'log.level',
            value: 'logcount',
            tooltipField: 'log.level'
          },
          dataSourceParams: {
            query:
              'collect_type:"rabbitmq" | stats by (log.level) count() as logcount | sort by (logcount desc)'
          }
        }
      },
      {
        h: 3,
        w: 6,
        x: 6,
        y: 3,
        i: uuidv4(),
        name: t('log.analysis.rabbitmq.hostDistribution'),
        moved: false,
        static: false,
        description: t('log.analysis.rabbitmq.hostDistributionDesc'),
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
              'collect_type:"rabbitmq" | stats by (host.name) count() as logcount | sort by (logcount desc) | limit 10'
          }
        }
      },
      {
        h: 4,
        w: 12,
        x: 0,
        y: 6,
        i: uuidv4(),
        name: t('log.analysis.rabbitmq.recentEvents'),
        moved: false,
        static: false,
        description: t('log.analysis.rabbitmq.recentEventsDesc'),
        valueConfig: {
          chartType: 'table',
          dataSource: 1,
          columns: [
            {
              title: t('log.analysis.rabbitmq.timestamp'),
              dataIndex: '@timestamp',
              key: '@timestamp'
            },
            {
              title: t('log.analysis.rabbitmq.logLevel'),
              dataIndex: 'log.level',
              key: 'log.level'
            },
            {
              title: t('log.analysis.rabbitmq.message'),
              dataIndex: 'message',
              key: 'message'
            },
            {
              title: t('log.analysis.rabbitmq.hostName'),
              dataIndex: 'host.name',
              key: 'host.name'
            }
          ],
          dataSourceParams: {
            query:
              'collect_type:"rabbitmq" | sort by (@timestamp desc) | limit 50'
          }
        }
      }
    ]
  };
};
