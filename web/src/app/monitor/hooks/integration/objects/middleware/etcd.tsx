export const useEtcdBkpullConfig = () => {
  return {
    instance_type: 'etcd',
    dashboardDisplay: [
      '集群健康',
      '请求性能',
      '存储',
      '网络',
      '运行状态',
    ],
    tableDiaplay: [
      { type: 'enum', key: 'etcd_server_has_leader_gauge' },
      { type: 'enum', key: 'etcd_server_is_leader_gauge' },
      { type: 'value', key: 'etcd_backend_quota_usage_percent' },
      { type: 'value', key: 'etcd_mvcc_db_total_size_in_use_in_bytes_gauge' },
      { type: 'value', key: 'etcd_server_proposals_pending_gauge' },
      { type: 'value', key: 'etcd_server_slow_apply_total_counter_rate' },
    ],
    groupIds: {},
    collectTypes: {
      Etcd: 'bkpull',
    },
  };
};
