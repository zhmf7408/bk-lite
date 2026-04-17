"""PELT 模型的 MLflow 推理包装器。"""

from __future__ import annotations

from typing import Any, cast

import pandas as pd
from loguru import logger
from mlflow.pyfunc.model import PythonModel

from .pelt_utils import (
    detect_changepoints,
    project_changepoints_to_point_labels,
    project_changepoints_to_point_scores,
)


class PELTWrapper(PythonModel):
    """将 PELT changepoint 结果映射为统一 serving 输出。"""

    def __init__(
        self,
        cost_model: str,
        pen: float,
        min_size: int,
        jump: int,
        event_window: int,
    ) -> None:
        self.cost_model = cost_model
        self.pen = pen
        self.min_size = min_size
        self.jump = jump
        self.event_window = event_window

    def predict(self, context, model_input, params=None):
        data, threshold = self._parse_input(model_input)
        series = self._to_series(data)
        signal = series.to_numpy(dtype=float)

        if threshold is not None:
            logger.debug(
                "PELTWrapper 忽略 runtime threshold，固定使用 changepoint 窗口投影输出"
            )

        changepoints = detect_changepoints(
            signal,
            cost_model=self.cost_model,
            min_size=self.min_size,
            jump=self.jump,
            pen=self.pen,
        )
        scores = project_changepoints_to_point_scores(
            length=len(signal),
            changepoints=changepoints,
            event_window=self.event_window,
        )
        labels = project_changepoints_to_point_labels(
            length=len(signal),
            changepoints=changepoints,
            event_window=self.event_window,
        )
        anomaly_severity = scores.copy()

        result: Any = {
            "labels": labels.tolist(),
            "scores": scores.tolist(),
            "anomaly_severity": anomaly_severity.tolist(),
            "_changepoints": changepoints,
            "_event_window": self.event_window,
            "_score_semantics": "binary_window",
            "_severity_semantics": "display_only_binary",
            "_supports_runtime_threshold": False,
            "_threshold_semantics": "legacy_compatibility_only",
        }
        return result

    def _parse_input(
        self, model_input: dict[str, Any]
    ) -> tuple[pd.Series | pd.DataFrame, float | None]:
        if not isinstance(model_input, dict):
            raise ValueError("输入格式错误，需要 dict 类型")

        data = model_input.get("data")
        if data is None:
            raise ValueError("输入必须包含 'data' 字段")

        threshold = model_input.get("threshold")
        if threshold is not None:
            threshold = float(threshold)
            if threshold <= 0:
                raise ValueError("threshold 必须 > 0")

        return data, threshold

    def _to_series(self, data: pd.Series | pd.DataFrame) -> pd.Series:
        if isinstance(data, pd.Series):
            return data
        if isinstance(data, pd.DataFrame):
            if "value" not in data.columns:
                raise ValueError("DataFrame 输入必须包含 value 列")
            return cast(pd.Series, data["value"])
        raise ValueError(
            f"data 必须是 pd.Series 或 pd.DataFrame，实际类型: {type(data)}"
        )
