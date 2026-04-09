import {
  ControllerInstallProgressRow,
  InstallerProgressMetric,
  InstallerProgressSummary,
  InstallerStepCode,
  InstallerStepLabelMap,
  LogStep,
  OperationTaskResult
} from '@/app/node-manager/types/controller';

type TranslationFunction = (key: string) => string;

const VALID_INSTALLER_STATUSES = new Set([
  'success',
  'error',
  'timeout',
  'running',
  'waiting',
  'installing',
  'installed'
]);

const clampNumber = (value: number, min: number, max: number) => {
  return Math.min(max, Math.max(min, value));
};

const normalizeNumber = (value?: number) => {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
};

const normalizeText = (value?: string | null) => {
  if (typeof value !== 'string') {
    return null;
  }

  const normalized = value.trim();
  return normalized || null;
};

const normalizeProgress = (progress?: InstallerProgressMetric) => {
  if (!progress) {
    return null;
  }

  const percent = normalizeNumber(progress.percent);
  const current = normalizeNumber(progress.current);
  const total = normalizeNumber(progress.total);

  return {
    percent: percent === null ? null : clampNumber(Math.round(percent), 0, 100),
    current: current === null ? null : Math.max(current, 0),
    total: total === null ? null : Math.max(total, 0),
    unit: normalizeText(progress.unit)
  };
};

export const normalizeInstallerStatus = (status?: string | null) => {
  if (!status) {
    return 'waiting';
  }

  return VALID_INSTALLER_STATUSES.has(status) ? status : 'running';
};

export const normalizeInstallerLogs = (steps?: LogStep[] | null): LogStep[] => {
  if (!Array.isArray(steps)) {
    return [];
  }

  return steps.map((step, index) => ({
    action: normalizeText(step.action) || `Step ${index + 1}`,
    status: normalizeInstallerStatus(step.status),
    message:
      normalizeText(step.message) ||
      normalizeText(step.details?.installer_message) ||
      '--',
    timestamp: normalizeText(step.timestamp) || '',
    details: step.details
      ? {
        ...step.details,
        raw_step: step.details.raw_step,
        step_index:
          normalizeNumber(step.details.step_index) === null
            ? undefined
            : Math.max(Math.round(step.details.step_index as number), 0),
        step_total:
          normalizeNumber(step.details.step_total) === null
            ? undefined
            : Math.max(Math.round(step.details.step_total as number), 0),
        progress: normalizeProgress(step.details.progress) || undefined,
        error: normalizeText(step.details.error) || undefined,
        installer_message:
          normalizeText(step.details.installer_message) || undefined,
        timestamp: normalizeText(step.details.timestamp) || undefined
      }
      : undefined
  }));
};

export const normalizeInstallerResult = (
  result?: OperationTaskResult | null
): OperationTaskResult | null => {
  if (!result) {
    return null;
  }

  let installerProgress: InstallerProgressSummary | undefined;

  if (result.installer_progress) {
    installerProgress = {
      ...result.installer_progress,
      current_status: normalizeInstallerStatus(
        result.installer_progress.current_status
      ),
      current_message:
        normalizeText(result.installer_progress.current_message) || undefined,
      progress: normalizeProgress(result.installer_progress.progress) || undefined,
      step_index:
        normalizeNumber(result.installer_progress.step_index) === null
          ? undefined
          : Math.max(Math.round(result.installer_progress.step_index as number), 0),
      step_total:
        normalizeNumber(result.installer_progress.step_total) === null
          ? undefined
          : Math.max(Math.round(result.installer_progress.step_total as number), 0)
    };
  }

  return {
    steps: normalizeInstallerLogs(result.steps),
    installer_progress: installerProgress
  };
};

export const normalizeControllerInstallResult = normalizeInstallerResult;

export const normalizeControllerInstallRow = (
  row: ControllerInstallProgressRow
): ControllerInstallProgressRow => {
  return {
    ...row,
    status: normalizeInstallerStatus(row.status),
    result: normalizeInstallerResult(row.result)
  };
};

export const normalizeControllerInstallRows = (
  rows?: ControllerInstallProgressRow[] | null
): ControllerInstallProgressRow[] => {
  if (!Array.isArray(rows)) {
    return [];
  }

  return rows.map(normalizeControllerInstallRow);
};

export const INSTALLER_STEP_LABEL_KEYS: InstallerStepLabelMap = {
  credential_check: 'node-manager.cloudregion.node.stepCredentialCheck',
  run: 'node-manager.cloudregion.node.stepRunInstaller',
  connectivity_check: 'node-manager.cloudregion.node.stepWaitForNodeConnection',
  stop_run: 'node-manager.cloudregion.node.stepStopControllerService',
  delete_dir: 'node-manager.cloudregion.node.stepRemoveInstallationDirectory',
  delete_node: 'node-manager.cloudregion.node.stepRemoveNodeRecord',
  unzip: 'node-manager.cloudregion.node.stepExtractCollectorPackage',
  set_executable: 'node-manager.cloudregion.node.stepSetExecutablePermissions',
  prepare: 'node-manager.cloudregion.node.stepPreparePackage',
  dispatch_command: 'node-manager.cloudregion.node.stepSubmitCollectorAction',
  consume_ack: 'node-manager.cloudregion.node.stepWaitForSidecarAck',
  execute_command: 'node-manager.cloudregion.node.stepExecuteCollectorAction',
  callback_or_timeout: 'node-manager.cloudregion.node.stepAwaitCollectorResult',
  fetch_session: 'node-manager.cloudregion.node.installerStepFetchSession',
  prepare_dirs: 'node-manager.cloudregion.node.installerStepPrepareDirs',
  prepare_directories:
    'node-manager.cloudregion.node.installerStepPrepareDirs',
  download: 'node-manager.cloudregion.node.installerStepDownload',
  download_package: 'node-manager.cloudregion.node.installerStepDownload',
  extract: 'node-manager.cloudregion.node.installerStepExtract',
  extract_package: 'node-manager.cloudregion.node.installerStepExtract',
  write_config: 'node-manager.cloudregion.node.installerStepWriteConfig',
  configure_runtime:
    'node-manager.cloudregion.node.installerStepWriteConfig',
  install: 'node-manager.cloudregion.node.installerStepInstall',
  run_package_installer:
    'node-manager.cloudregion.node.installerStepInstall',
  install_complete: 'node-manager.cloudregion.node.installerStepComplete',
  complete: 'node-manager.cloudregion.node.installerStepComplete'
};

export const INSTALLER_STEP_SUGGESTION_KEYS: InstallerStepLabelMap = {
  fetch_session: 'node-manager.cloudregion.node.installerSuggestionFetchSession',
  prepare_dirs: 'node-manager.cloudregion.node.installerSuggestionPrepareDirs',
  prepare_directories:
    'node-manager.cloudregion.node.installerSuggestionPrepareDirs',
  download: 'node-manager.cloudregion.node.installerSuggestionDownload',
  download_package: 'node-manager.cloudregion.node.installerSuggestionDownload',
  extract: 'node-manager.cloudregion.node.installerSuggestionExtract',
  extract_package: 'node-manager.cloudregion.node.installerSuggestionExtract',
  write_config: 'node-manager.cloudregion.node.installerSuggestionWriteConfig',
  configure_runtime:
    'node-manager.cloudregion.node.installerSuggestionWriteConfig',
  install: 'node-manager.cloudregion.node.installerSuggestionInstall',
  run_package_installer:
    'node-manager.cloudregion.node.installerSuggestionInstall'
};

export const formatInstallerProgressValue = (value?: number, unit?: string) => {
  const normalizedValue = normalizeNumber(value);

  if (normalizedValue === null) {
    return null;
  }

  if (unit === 'bytes') {
    if (normalizedValue === 0) {
      return '0 B';
    }

    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const base = Math.min(
      Math.floor(Math.log(normalizedValue) / Math.log(1024)),
      units.length - 1
    );
    const formatted = normalizedValue / 1024 ** base;
    return `${formatted >= 10 ? formatted.toFixed(0) : formatted.toFixed(1)} ${units[base]}`;
  }

  return `${normalizedValue}`;
};

export const getInstallerProgressPercent = (
  progress?: InstallerProgressMetric
) => {
  const normalizedProgress = normalizeProgress(progress);

  if (normalizedProgress?.percent !== null && normalizedProgress?.percent !== undefined) {
    return normalizedProgress.percent;
  }

  if (
    normalizedProgress?.current !== null &&
    normalizedProgress?.current !== undefined &&
    normalizedProgress?.total !== null &&
    normalizedProgress?.total !== undefined &&
    normalizedProgress.total > 0
  ) {
    return clampNumber(
      Math.round((normalizedProgress.current / normalizedProgress.total) * 100),
      0,
      100
    );
  }

  return null;
};

export const getInstallerProgressText = (progress?: InstallerProgressMetric) => {
  const normalizedProgress = normalizeProgress(progress);

  if (!normalizedProgress) {
    return null;
  }

  if (
    normalizedProgress.current !== null &&
    normalizedProgress.current !== undefined &&
    normalizedProgress.total !== null &&
    normalizedProgress.total !== undefined
  ) {
    const current = formatInstallerProgressValue(
      normalizedProgress.current,
      normalizedProgress.unit || undefined
    );
    const total = formatInstallerProgressValue(
      normalizedProgress.total,
      normalizedProgress.unit || undefined
    );

    if (current && total) {
      return `${current} / ${total}`;
    }
  }

  const percent = getInstallerProgressPercent(progress);
  if (percent !== null) {
    return `${percent}%`;
  }

  if (
    normalizedProgress.current !== null &&
    normalizedProgress.current !== undefined
  ) {
    return formatInstallerProgressValue(
      normalizedProgress.current,
      normalizedProgress.unit || undefined
    );
  }

  return null;
};

export const getInstallerStepInfo = (
  stepIndex?: number,
  stepTotal?: number
) => {
  const normalizedStepIndex = normalizeNumber(stepIndex);
  const normalizedStepTotal = normalizeNumber(stepTotal);

  if (
    normalizedStepIndex !== null &&
    normalizedStepTotal !== null &&
    normalizedStepIndex > 0 &&
    normalizedStepTotal > 0
  ) {
    return `${Math.min(Math.round(normalizedStepIndex), Math.round(normalizedStepTotal))}/${Math.round(normalizedStepTotal)}`;
  }

  return null;
};

export const getInstallerStepLabel = (
  t: TranslationFunction,
  step?: InstallerStepCode,
  fallback?: string
) => {
  if (step && INSTALLER_STEP_LABEL_KEYS[step]) {
    return t(INSTALLER_STEP_LABEL_KEYS[step]);
  }

  return normalizeText(fallback) || normalizeText(step) || '--';
};

export const getInstallerFailureSuggestion = (
  t: TranslationFunction,
  step?: InstallerStepCode
) => {
  if (step && INSTALLER_STEP_SUGGESTION_KEYS[step]) {
    return t(INSTALLER_STEP_SUGGESTION_KEYS[step]);
  }

  return t('node-manager.cloudregion.node.installerSuggestionGeneric');
};

export const getFailedInstallerStep = (steps?: LogStep[]) => {
  if (!steps?.length) {
    return null;
  }

  return [...steps]
    .reverse()
    .find((step) => ['error', 'timeout'].includes(step.status));
};

export const getInstallerFailureGuidance = (
  t: TranslationFunction,
  result?: OperationTaskResult | null
) => {
  const failedStep = getFailedInstallerStep(result?.steps);
  const rawStep = failedStep?.details?.raw_step || failedStep?.action;

  return {
    reason: normalizeText(
      failedStep?.details?.error ||
        failedStep?.message ||
        result?.installer_progress?.current_message ||
        null
    ),
    suggestion: getInstallerFailureSuggestion(t, rawStep)
  };
};

export const getInstallerSummaryLabel = (
  t: TranslationFunction,
  installerProgress?: InstallerProgressSummary | null
) => {
  if (!installerProgress) {
    return null;
  }

  return getInstallerStepLabel(
    t,
    installerProgress.current_step,
    installerProgress.current_message || installerProgress.current_step
  );
};
