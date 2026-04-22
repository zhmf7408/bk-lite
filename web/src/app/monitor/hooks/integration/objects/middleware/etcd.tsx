export const useEtcdBkpullConfig = () => {
  return {
    instance_type: 'etcd',
    dashboardDisplay: [
      '集群状态',
      '存储与碎片',
      '磁盘时延',
      '提案与一致性',
      '请求与流量',
      '监听与压缩',
    ],
    tableDiaplay: [
      { type: 'enum', key: 'etcd_server_has_leader_gauge' },
      { type: 'value', key: 'etcd_backend_allocated_usage_percent' },
      { type: 'enum', key: 'etcd_backend_urgent_defrag' },
      { type: 'value', key: 'etcd_server_proposals_pending_gauge' },
      { type: 'value', key: 'etcd_server_proposals_apply_lag' },
      { type: 'value', key: 'etcd_disk_wal_fsync_p99_seconds' },
    ],
    groupIds: {},
    collectTypes: {
      Etcd: 'bkpull',
    },
  };
};
