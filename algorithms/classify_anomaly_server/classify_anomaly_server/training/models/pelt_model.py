"""PELT changepoint 异常检测模型。"""

from __future__ import annotations

import hashlib
from importlib import import_module
from typing import Any, Optional

import mlflow
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from loguru import logger

from .base import BaseAnomalyModel, ModelRegistry
from .pelt_utils import (
    detect_changepoints,
    project_changepoints_to_point_labels,
    project_changepoints_to_point_scores,
)


@ModelRegistry.register("PELT")
class PELTModel(BaseAnomalyModel):
    """基于 ruptures PELT 的点级异常检测模型。"""

    def __init__(
        self,
        cost_model: str = "l2",
        pen: float = 10.0,
        min_size: int = 3,
        jump: int = 1,
        event_window: int = 1,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            cost_model=cost_model,
            pen=pen,
            min_size=min_size,
            jump=jump,
            event_window=event_window,
            **kwargs,
        )
        self.cost_model = str(cost_model)
        self.pen = float(pen)
        self.min_size = int(min_size)
        self.jump = int(jump)
        self.event_window = int(event_window)
        self.feature_names_: list[str] | None = None
        self.n_samples_train_: int | None = None
        self.hyperopt_history_: list[dict[str, float | int | str]] = []
        self._changepoint_cache_key: str | None = None
        self._changepoint_cache: list[int] | None = None

    def fit(
        self,
        train_data: pd.DataFrame,
        train_labels: pd.Series | NDArray[np.int_] | None = None,
        **kwargs: Any,
    ) -> "PELTModel":
        if not isinstance(train_data, pd.DataFrame):
            raise ValueError("train_data 必须是 pandas.DataFrame")
        if list(train_data.columns) != ["value"]:
            raise ValueError("PELTModel 训练数据必须只包含 value 列")

        self.feature_names_ = train_data.columns.tolist()
        self.n_samples_train_ = len(train_data)
        self.threshold_ = None
        self._changepoint_cache_key = None
        self._changepoint_cache = None
        self.is_fitted = True

        logger.info(
            f"PELT 模型训练完成: samples={self.n_samples_train_}"
        )
        return self

    def predict(self, X: pd.DataFrame) -> NDArray[np.int_]:
        self._check_fitted()
        self._validate_features(X)

        changepoints = self.get_changepoints(X)
        return project_changepoints_to_point_labels(
            length=len(X),
            changepoints=changepoints,
            event_window=self.event_window,
        )

    def predict_proba(self, X: pd.DataFrame) -> NDArray[np.float64]:
        self._check_fitted()
        self._validate_features(X)

        changepoints = self.get_changepoints(X)
        return project_changepoints_to_point_scores(
            length=len(X),
            changepoints=changepoints,
            event_window=self.event_window,
        )

    def get_changepoints(self, X: pd.DataFrame) -> list[int]:
        """返回输入序列对应的 changepoint 索引。"""
        self._check_fitted()
        self._validate_features(X)

        signal = X["value"].to_numpy(dtype=float)
        cache_key = self._build_changepoint_cache_key(signal)
        if self._changepoint_cache_key == cache_key and self._changepoint_cache is not None:
            return list(self._changepoint_cache)

        changepoints = detect_changepoints(
            signal,
            cost_model=self.cost_model,
            min_size=self.min_size,
            jump=self.jump,
            pen=self.pen,
        )
        self._changepoint_cache_key = cache_key
        self._changepoint_cache = list(changepoints)
        return list(changepoints)

    def evaluate_changepoints(
        self,
        X: pd.DataFrame,
        labels: NDArray[np.int_] | pd.Series,
        prefix: str = "",
    ) -> dict[str, float]:
        """计算 PELT 专属 changepoint / event-window 指标。"""
        changepoints = self.get_changepoints(X)
        labels_array = (
            labels.to_numpy(dtype=int)
            if isinstance(labels, pd.Series)
            else labels.astype(int, copy=False)
        )

        labeled_points = int(labels_array.sum())
        matched_changepoints = sum(
            1
            for changepoint in changepoints
            if labels_array[
                max(0, changepoint - self.event_window) : min(
                    len(labels_array), changepoint + self.event_window + 1
                )
            ].any()
        )

        if labeled_points > 0:
            covered_points = sum(
                1
                for idx, value in enumerate(labels_array)
                if value == 1
                and any(
                    abs(idx - changepoint) <= self.event_window
                    for changepoint in changepoints
                )
            )
            changepoint_recall = covered_points / labeled_points
        else:
            changepoint_recall = 0.0

        changepoint_precision = (
            matched_changepoints / len(changepoints) if changepoints else 0.0
        )
        changepoint_f1 = (
            float(
                2
                * changepoint_precision
                * changepoint_recall
                / (changepoint_precision + changepoint_recall)
            )
            if (changepoint_precision + changepoint_recall) > 0
            else 0.0
        )

        metrics = {
            "num_changepoints": float(len(changepoints)),
            "num_labeled_points": float(labeled_points),
            "changepoint_precision": float(changepoint_precision),
            "changepoint_recall": float(changepoint_recall),
            "changepoint_f1": changepoint_f1,
        }

        if prefix:
            return {f"{prefix}_{key}": value for key, value in metrics.items()}
        return metrics

    def optimize_hyperparams(
        self,
        train_data: pd.DataFrame,
        val_data: pd.DataFrame,
        train_labels: NDArray[np.int_] | pd.Series,
        val_labels: NDArray[np.int_] | pd.Series,
        config: Any,
    ) -> dict[str, Any]:
        search_config = config.get_search_config()
        search_space = search_config["search_space"]
        max_evals = int(search_config.get("max_evals", 1))
        metric = search_config["metric"]
        early_stop_config = search_config.get("early_stopping", {})
        early_stop_enabled = bool(early_stop_config.get("enabled", True))
        patience = int(early_stop_config.get("patience", 10))

        best_score = float("-inf")
        best_params = {
            "pen": self.pen,
            "min_size": self.min_size,
            "jump": self.jump,
        }

        jump_values = search_space.get("jump", [self.jump])
        resolved_cost_model = config.cost_model or self.cost_model
        resolved_event_window = (
            config.event_window if config.event_window is not None else self.event_window
        )
        if isinstance(val_labels, pd.Series):
            labels_array: NDArray[np.int_] = val_labels.to_numpy(dtype=int)
        else:
            labels_array = val_labels.astype(int, copy=False)
        changepoint_metrics = {
            "changepoint_precision",
            "changepoint_recall",
            "changepoint_f1",
        }
        eval_count = 0
        no_progress_count = 0
        grid_total_evals = (
            len(search_space["pen"]) * len(search_space["min_size"]) * len(jump_values)
        )
        total_evals = min(max_evals, grid_total_evals)
        early_stopped = False

        logger.info(f"开始超参数优化: max_evals={max_evals}, metric={metric}")
        if early_stop_enabled:
            logger.info(f"早停机制: 启用 (patience={patience})")

        self.hyperopt_history_ = []

        for pen in search_space["pen"]:
            for min_size in search_space["min_size"]:
                for jump in jump_values:
                    if eval_count >= total_evals:
                        break

                    eval_count += 1
                    candidate = PELTModel(
                        pen=pen,
                        min_size=min_size,
                        jump=jump,
                        cost_model=resolved_cost_model,
                        event_window=resolved_event_window,
                    )
                    candidate.fit(train_data)
                    if metric in changepoint_metrics:
                        changepoint_eval = candidate.evaluate_changepoints(
                            val_data, labels_array
                        )
                        metrics = changepoint_eval
                        fallback_metric = "changepoint_f1"
                    else:
                        changepoint_eval = candidate.evaluate_changepoints(
                            val_data, labels_array
                        )
                        metrics = candidate.evaluate(val_data, labels_array)
                        fallback_metric = "f1"
                    score = float(metrics.get(metric, metrics[fallback_metric]))
                    trial_num_changepoints = float(
                        changepoint_eval.get("num_changepoints", 0.0)
                    )
                    self.hyperopt_history_.append(
                        {
                            "trial": int(eval_count),
                            "metric": str(metric),
                            "score": float(score),
                            "pen": float(pen),
                            "min_size": int(min_size),
                            "jump": int(jump),
                            "num_changepoints": trial_num_changepoints,
                        }
                    )

                    logger.debug(
                        f"PELT trial [{eval_count}/{total_evals}] "
                        f"pen={pen}, min_size={min_size}, jump={jump}: "
                        f"{metric}={score:.4f}"
                    )

                    # 每轮试验记录到 MLflow（镜像 ECOD 的 hyperopt/* 命名）
                    if mlflow.active_run():
                        mlflow.log_metric(
                            f"hyperopt/val_{metric}", score, step=eval_count
                        )
                        if metric in changepoint_metrics:
                            mlflow.log_metric(
                                "hyperopt/val_changepoint_precision",
                                float(metrics.get("changepoint_precision", 0.0)),
                                step=eval_count,
                            )
                            mlflow.log_metric(
                                "hyperopt/val_changepoint_recall",
                                float(metrics.get("changepoint_recall", 0.0)),
                                step=eval_count,
                            )
                            mlflow.log_metric(
                                "hyperopt/val_changepoint_f1",
                                float(metrics.get("changepoint_f1", score)),
                                step=eval_count,
                            )
                        else:
                            mlflow.log_metric(
                                "hyperopt/val_f1",
                                float(metrics.get("f1", score)),
                                step=eval_count,
                            )
                            mlflow.log_metric(
                                "hyperopt/val_precision",
                                float(metrics.get("precision", 0.0)),
                                step=eval_count,
                            )
                            mlflow.log_metric(
                                "hyperopt/val_recall",
                                float(metrics.get("recall", 0.0)),
                                step=eval_count,
                            )

                    if score > best_score:
                        best_score = score
                        no_progress_count = 0
                        best_params = {
                            "pen": float(pen),
                            "min_size": int(min_size),
                            "jump": int(jump),
                        }
                        if mlflow.active_run():
                            mlflow.log_metric(
                                "hyperopt/best_so_far", score, step=eval_count
                            )
                    else:
                        no_progress_count += 1

                    if early_stop_enabled and no_progress_count >= patience:
                        early_stopped = True
                        logger.info(
                            f"PELT 早停触发: 连续 {patience} 次无提升，"
                            f"在 {eval_count}/{total_evals} 次停止"
                        )
                        break

                if eval_count >= total_evals or early_stopped:
                    break
            if eval_count >= total_evals or early_stopped:
                break

        if self.hyperopt_history_ and all(
            float(item.get("num_changepoints", 0.0)) == 0.0
            for item in self.hyperopt_history_
        ):
            logger.warning(
                "PELT 超参数搜索未检测到任何 changepoint: all trials produced num_changepoints=0"
            )

        # 汇总指标（镜像 ECOD 的 hyperopt_summary/* 命名）
        if mlflow.active_run():
            summary_metrics = {
                "hyperopt_summary/total_evals": float(total_evals),
                "hyperopt_summary/actual_evals": float(eval_count),
                "hyperopt_summary/grid_total_evals": float(grid_total_evals),
                "hyperopt_summary/best_score": best_score,
            }
            if early_stop_enabled:
                summary_metrics["hyperopt_summary/early_stop_enabled"] = 1.0
                summary_metrics["hyperopt_summary/early_stopped"] = (
                    1.0 if early_stopped else 0.0
                )
                summary_metrics["hyperopt_summary/patience_used"] = float(patience)
                if early_stopped and total_evals > 0:
                    summary_metrics["hyperopt_summary/time_saved_pct"] = (
                        (total_evals - eval_count) / total_evals * 100
                    )

            mlflow.log_metrics(summary_metrics)
            logger.info(
                f"PELT 超参数搜索完成: {eval_count} 轮, 最优 {metric}={best_score:.4f}, "
                f"参数={best_params}"
            )
            mlflow.log_dict(
                {"trial_history": self.hyperopt_history_},
                "pelt_hyperopt_history.json",
            )

        self.pen = float(best_params["pen"])
        self.min_size = int(best_params["min_size"])
        self.jump = int(best_params["jump"])
        self.config.update(best_params)
        return best_params

    def save_mlflow(self, artifact_path: str = "model") -> None:
        self._check_fitted()

        if mlflow.active_run():
            mlflow.log_dict(
                {
                    "model_type": "PELT",
                    "cost_model": self.cost_model,
                    "pen": self.pen,
                    "min_size": self.min_size,
                    "jump": self.jump,
                    "event_window": self.event_window,
                    "score_semantics": "binary_window",
                    "supports_runtime_threshold": False,
                    "threshold_semantics": "legacy_compatibility_only",
                    "feature_names": self.feature_names_,
                    "n_samples_train": self.n_samples_train_,
                },
                "model_metadata.json",
            )

        pelt_wrapper_module = import_module(
            "classify_anomaly_server.training.models.pelt_wrapper"
        )
        PELTWrapper = pelt_wrapper_module.PELTWrapper

        wrapped_model = PELTWrapper(
            cost_model=self.cost_model,
            pen=self.pen,
            min_size=self.min_size,
            jump=self.jump,
            event_window=self.event_window,
        )

        import cloudpickle

        cloudpickle.dumps(wrapped_model)
        mlflow.pyfunc.log_model(
            artifact_path=artifact_path,
            python_model=wrapped_model,
        )

    def _build_changepoint_cache_key(self, signal: NDArray[np.float64]) -> str:
        hasher = hashlib.blake2b(digest_size=16)
        hasher.update(signal.tobytes())
        hasher.update(str(self.cost_model).encode())
        hasher.update(str(self.pen).encode())
        hasher.update(str(self.min_size).encode())
        hasher.update(str(self.jump).encode())
        hasher.update(str(self.event_window).encode())
        return hasher.hexdigest()

    def _validate_features(self, X: pd.DataFrame) -> None:
        if not isinstance(X, pd.DataFrame):
            raise ValueError("X 必须是 pandas.DataFrame")
        if self.feature_names_ is None or list(X.columns) != self.feature_names_:
            raise ValueError(
                f"特征列不匹配。期望: {self.feature_names_}, 实际: {list(X.columns)}"
            )
