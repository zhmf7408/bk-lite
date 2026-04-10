"""PELT 模型的 MLflow 推理包装器。"""

from __future__ import annotations

from typing import Any, cast

import mlflow
import numpy as np
import pandas as pd
from mlflow.pyfunc.model import PythonModel
from .pelt_utils import detect_changepoints, event_window_scores


class PELTWrapper(PythonModel):
    """将 PELT changepoint 结果映射为点级输出。"""

    def __init__(
        self,
        cost_model: str,
        pen: float,
        min_size: int,
        jump: int,
        event_window: int,
        threshold: float,
    ) -> None:
        self.cost_model = cost_model
        self.pen = pen
        self.min_size = min_size
        self.jump = jump
        self.event_window = event_window
        self.threshold = threshold

    def predict(self, context, model_input, params=None):
        data, threshold = self._parse_input(model_input)
        series = self._to_series(data)
        signal = series.to_numpy(dtype=float)

        changepoints = detect_changepoints(
            signal,
            cost_model=self.cost_model,
            min_size=self.min_size,
            jump=self.jump,
            pen=self.pen,
        )
        scores = event_window_scores(
            length=len(signal),
            changepoints=changepoints,
            event_window=self.event_window,
        )

        anomaly_severity = np.minimum(scores / (threshold * 2), 1.0)
        labels = (scores > threshold).astype(int)

        result: Any = {
            "labels": labels.tolist(),
            "scores": scores.tolist(),
            "anomaly_severity": anomaly_severity.tolist(),
            "_changepoints": changepoints,
            "_event_window": self.event_window,
        }
        return result

    def _parse_input(
        self, model_input: dict[str, Any]
    ) -> tuple[pd.Series | pd.DataFrame, float]:
        if not isinstance(model_input, dict):
            raise ValueError("输入格式错误，需要 dict 类型")

        data = model_input.get("data")
        if data is None:
            raise ValueError("输入必须包含 'data' 字段")

        threshold = float(model_input.get("threshold", self.threshold))
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
