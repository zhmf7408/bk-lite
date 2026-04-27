import { useTranslation } from '@/utils/i18n';
import { v4 as uuidv4 } from 'uuid';

export const useFileIntegrityDashboard = () => {
  const { t } = useTranslation();

  return {
    name: t('log.analysis.fileIntegrity.dashboardName'),
    desc: '',
    id: '5',
    category: 'security',
    categoryName: t('log.analysis.category.security'),
    collectTypeName: 'file_integrity',
    filters: {},
    other: {},
    view_sets: [
      {
        h: 3,
        w: 9,
        x: 0,
        y: 0,
        i: uuidv4(),
        name: t('log.analysis.fileIntegrity.changeEventTrend'),
        moved: false,
        static: false,
        description: t('log.analysis.fileIntegrity.changeEventTrendDesc'),
        valueConfig: {
          chartType: 'line',
          dataSource: 1,
          displayMaps: {
            type: 'single',
            key: 'eventcount',
            value: 'eventcount',
            tooltipField: 'eventcount'
          },
          dataSourceParams: {
            query:
              'collect_type:"file_integrity" | stats by (_time:${_time}) count() as eventcount'
          }
        }
      },
      {
        h: 3,
        w: 3,
        x: 9,
        y: 0,
        i: uuidv4(),
        name: t('log.analysis.fileIntegrity.totalChangeEvents'),
        moved: false,
        static: false,
        description: t('log.analysis.fileIntegrity.totalChangeEventsDesc'),
        valueConfig: {
          chartType: 'single',
          dataSource: 1,
          displayMaps: {
            type: 'single',
            key: 'eventcount',
            value: 'eventcount',
            tooltipField: 'eventcount'
          },
          dataSourceParams: {
            query: 'collect_type:"file_integrity" | stats count() as eventcount'
          }
        }
      },
      {
        h: 3,
        w: 6,
        x: 0,
        y: 3,
        i: uuidv4(),
        name: t('log.analysis.fileIntegrity.actionDistribution'),
        moved: false,
        static: false,
        description: t('log.analysis.fileIntegrity.actionDistributionDesc'),
        valueConfig: {
          chartType: 'pie',
          dataSource: 1,
          displayMaps: {
            type: 'single',
            key: 'event.action',
            value: 'eventcount',
            tooltipField: 'event.action'
          },
          dataSourceParams: {
            query:
              'collect_type:"file_integrity" | stats by (event.action) count() as eventcount | sort by (eventcount desc)'
          }
        }
      },
      {
        h: 3,
        w: 6,
        x: 6,
        y: 3,
        i: uuidv4(),
        name: t('log.analysis.fileIntegrity.hostDistribution'),
        moved: false,
        static: false,
        description: t('log.analysis.fileIntegrity.hostDistributionDesc'),
        valueConfig: {
          chartType: 'pie',
          dataSource: 1,
          displayMaps: {
            type: 'single',
            key: 'host.name',
            value: 'eventcount',
            tooltipField: 'host.name'
          },
          dataSourceParams: {
            query:
              'collect_type:"file_integrity" | stats by (host.name) count() as eventcount | sort by (eventcount desc) | limit 10'
          }
        }
      },
      {
        h: 4,
        w: 12,
        x: 0,
        y: 6,
        i: uuidv4(),
        name: t('log.analysis.fileIntegrity.topChangedFiles'),
        moved: false,
        static: false,
        description: t('log.analysis.fileIntegrity.topChangedFilesDesc'),
        valueConfig: {
          chartType: 'table',
          dataSource: 1,
          columns: [
            {
              title: t('log.analysis.fileIntegrity.filePath'),
              dataIndex: 'file.path',
              key: 'file.path'
            },
            {
              title: t('log.analysis.fileIntegrity.hostName'),
              dataIndex: 'host.name',
              key: 'host.name'
            },
            {
              title: t('log.analysis.fileIntegrity.changeCount'),
              dataIndex: 'eventcount',
              key: 'eventcount'
            }
          ],
          dataSourceParams: {
            query:
              'collect_type:"file_integrity" | stats by (file.path, host.name) count() as eventcount | sort by (eventcount desc) | limit 20'
          }
        }
      },
      {
        h: 4,
        w: 12,
        x: 0,
        y: 10,
        i: uuidv4(),
        name: t('log.analysis.fileIntegrity.recentEvents'),
        moved: false,
        static: false,
        description: t('log.analysis.fileIntegrity.recentEventsDesc'),
        valueConfig: {
          chartType: 'table',
          dataSource: 1,
          columns: [
            {
              title: t('log.analysis.fileIntegrity.timestamp'),
              dataIndex: '@timestamp',
              key: '@timestamp'
            },
            {
              title: t('log.analysis.fileIntegrity.eventAction'),
              dataIndex: 'event.action',
              key: 'event.action'
            },
            {
              title: t('log.analysis.fileIntegrity.filePath'),
              dataIndex: 'file.path',
              key: 'file.path'
            },
            {
              title: t('log.analysis.fileIntegrity.fileOwner'),
              dataIndex: 'file.owner',
              key: 'file.owner'
            },
            {
              title: t('log.analysis.fileIntegrity.fileHash'),
              dataIndex: 'file.hash.sha256',
              key: 'file.hash.sha256'
            },
            {
              title: t('log.analysis.fileIntegrity.hostName'),
              dataIndex: 'host.name',
              key: 'host.name'
            }
          ],
          dataSourceParams: {
            query:
              'collect_type:"file_integrity" | sort by (@timestamp desc) | limit 50'
          }
        }
      }
    ]
  };
};
