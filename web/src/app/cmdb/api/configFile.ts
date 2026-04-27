import { useCallback, useMemo } from 'react';
import useApiClient from '@/utils/request';

export const useConfigFileApi = () => {
  const { get, del } = useApiClient();

  const getConfigFileList = useCallback(
    (instance_id: string) =>
      get('/cmdb/api/config_file_versions/file_list/', { params: { instance_id } }),
    [get]
  );

  const getConfigFileVersions = useCallback(
    (instance_id: string, file_path: string) =>
      get('/cmdb/api/config_file_versions/', { params: { instance_id, file_path, page_size: -1 } }),
    [get]
  );

  const getConfigFileContent = useCallback(
    (versionId: number, encoding = 'utf-8') =>
      get(`/cmdb/api/config_file_versions/${versionId}/content/`, { params: { encoding } }),
    [get]
  );

  const deleteConfigFileVersion = useCallback(
    (versionId: number) => del(`/cmdb/api/config_file_versions/${versionId}/`),
    [del]
  );

  const getConfigFileDiff = useCallback(
    (version_id_1: number, version_id_2: number) =>
      get('/cmdb/api/config_file_versions/diff/', {
        params: { version_id_1, version_id_2 },
      }),
    [get]
  );

  return useMemo(
    () => ({
      getConfigFileList,
      getConfigFileVersions,
      getConfigFileContent,
      getConfigFileDiff,
      deleteConfigFileVersion,
    }),
    [deleteConfigFileVersion, getConfigFileContent, getConfigFileDiff, getConfigFileList, getConfigFileVersions]
  );
};
