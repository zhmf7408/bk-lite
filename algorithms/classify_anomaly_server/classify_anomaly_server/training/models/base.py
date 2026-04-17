"""异常检测模型基类和注册机制."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
import pandas as pd
import numpy as np
from numpy.typing import NDArray
from loguru import logger
from sklearn.metrics import roc_auc_score, confusion_matrix


class BaseAnomalyModel(ABC):
    """异常检测模型基类 - 统一接口

    所有异常检测模型必须实现此接口，确保可以被通用训练器调用。

    核心方法：
    - fit(): 训练模型（通常使用正常样本）
    - predict(): 预测异常标签
    - predict_proba(): 预测异常分数
    - evaluate(): 评估模型性能

    工具方法：
    - get_params(): 获取模型参数
    """

    def __init__(self, **kwargs):
        """初始化模型

        Args:
            **kwargs: 模型特定的参数
        """
        self.model = None
        self.config = kwargs
        self.is_fitted = False
        self.contamination = kwargs.get("contamination", 0.1)
        self.threshold_ = None  # 异常阈值

    @abstractmethod
    def fit(
        self,
        train_data: pd.DataFrame,
        train_labels: pd.Series | NDArray[np.int_] | None = None,
        **kwargs,
    ) -> "BaseAnomalyModel":
        """训练模型

        Args:
            train_data: 训练数据（特征矩阵）
            train_labels: 训练标签（可选，供需要标签的模型使用）
            **kwargs: 模型特定的训练参数

        Returns:
            self: 训练后的模型实例

        Raises:
            ValueError: 数据格式不正确
        """
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> NDArray[np.int_]:
        """预测异常标签

        Args:
            X: 特征矩阵

        Returns:
            预测标签数组（0=正常, 1=异常）

        Raises:
            RuntimeError: 模型未训练
        """
        pass

    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> NDArray[np.float64]:
        """预测异常分数

        Args:
            X: 特征矩阵

        Returns:
            异常分数数组（值越大越异常）

        Raises:
            RuntimeError: 模型未训练
        """
        pass

    def optimize_hyperparams(
        self,
        train_data: pd.DataFrame,
        val_data: pd.DataFrame,
        train_labels: pd.Series | NDArray[np.int_],
        val_labels: pd.Series | NDArray[np.int_],
        config: Any,
    ) -> Dict[str, Any]:
        """优化超参数。

        默认实现返回空字典，供不支持超参数优化的模型安全复用。
        """
        logger.warning(f"{self.__class__.__name__} 未实现 optimize_hyperparams，跳过")
        return {}

    def save_mlflow(self, artifact_path: str = "model") -> None:
        """保存模型到 MLflow。

        默认实现为空操作，供不支持 MLflow 导出的模型安全复用。
        """
        logger.warning(f"{self.__class__.__name__} 未实现 save_mlflow，跳过保存")
        return None

    def get_changepoints(self, X: pd.DataFrame) -> list[int]:
        """返回变点索引。

        默认实现返回空列表，供非变点模型安全复用。
        """
        return []

    def evaluate_changepoints(
        self,
        X: pd.DataFrame,
        labels: pd.Series | NDArray[np.int_],
        prefix: str = "",
    ) -> Dict[str, Any]:
        """计算变点相关指标。

        默认实现返回空字典，供非变点模型安全复用。
        """
        return {}

    def evaluate(
        self,
        test_data: pd.DataFrame,
        test_labels: pd.Series | NDArray[np.int_],
        prefix: str = "",
    ) -> Dict[str, Any]:
        """评估模型性能

        Args:
            test_data: 测试数据特征矩阵
            test_labels: 真实标签（0=正常, 1=异常）
            prefix: 指标名称前缀（如 "train", "test", "final_train"）

        Returns:
            评估指标字典，包含：
            - precision: 精确率
            - recall: 召回率
            - f1: F1分数
            - auc: ROC AUC（如果可计算）
            - confusion_matrix: 混淆矩阵
            - _predictions / _scores / _true_labels: 原始序列载荷

        Raises:
            RuntimeError: 模型未训练
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before evaluation")

        labels_array = (
            test_labels.to_numpy(dtype=int)
            if isinstance(test_labels, pd.Series)
            else test_labels.astype(int, copy=False)
        )

        # 预测
        y_pred = self.predict(test_data)
        y_scores = self.predict_proba(test_data)

        cm = confusion_matrix(labels_array, y_pred)
        tn = fp = fn = tp = 0
        if cm.shape == (2, 2):
            tn, fp, fn, tp = (int(value) for value in cm.ravel())

        precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = (
            float(2 * precision * recall / (precision + recall))
            if (precision + recall) > 0
            else 0.0
        )

        # 计算指标
        metrics: Dict[str, Any] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

        # 尝试计算 AUC
        try:
            metrics["auc"] = float(roc_auc_score(labels_array, y_scores))
        except ValueError as e:
            logger.warning(f"Cannot compute AUC: {e}")
            metrics["auc"] = 0.0

        # 混淆矩阵
        metrics["confusion_matrix"] = cm.tolist()

        # 真负例、假正例、假负例、真正例
        if cm.shape == (2, 2):
            metrics["true_negative"] = tn
            metrics["false_positive"] = fp
            metrics["false_negative"] = fn
            metrics["true_positive"] = tp

        # 存储预测结果和真实标签（用于后续分析）
        metrics["_predictions"] = y_pred.tolist()
        metrics["_scores"] = y_scores.tolist()
        metrics["_true_labels"] = labels_array.tolist()

        # 应用前缀（如果提供）
        if prefix:
            metrics = {
                f"{prefix}_{k}" if not k.startswith("_") else k: v
                for k, v in metrics.items()
            }

        return metrics

    def get_params(self) -> Dict[str, Any]:
        """获取模型参数

        Returns:
            模型参数字典
        """
        return self.config.copy()

    def _check_fitted(self):
        """检查模型是否已训练"""
        if not self.is_fitted:
            raise RuntimeError(
                "This model instance is not fitted yet. "
                "Call 'fit' with appropriate arguments before using this method."
            )


class ModelRegistry:
    """模型注册器 - 支持动态模型加载

    使用装饰器模式注册模型类：

    Example:
        @ModelRegistry.register("ECOD")
        class ECODModel(BaseAnomalyModel):
            pass

        # 动态创建模型
        model = ModelRegistry.create_model("ECOD", contamination=0.1)
    """

    _registry: Dict[str, Type[BaseAnomalyModel]] = {}

    @classmethod
    def register(cls, model_type: str):
        """注册模型类的装饰器

        Args:
            model_type: 模型类型标识（如 "ECOD", "IsolationForest"）

        Returns:
            装饰器函数
        """

        def decorator(model_class: Type[BaseAnomalyModel]):
            if not issubclass(model_class, BaseAnomalyModel):
                raise TypeError(
                    f"Model class must inherit from BaseAnomalyModel, got {model_class}"
                )

            cls._registry[model_type.lower()] = model_class
            logger.debug(f"Registered model: {model_type} -> {model_class.__name__}")
            return model_class

        return decorator

    @classmethod
    def get(cls, model_type: str) -> Type[BaseAnomalyModel]:
        """获取已注册的模型类（兼容timeseries_server API）

        Args:
            model_type: 模型类型（如 "ECOD"）

        Returns:
            模型类

        Raises:
            ValueError: 模型类型未注册
        """
        model_type_lower = model_type.lower()

        if model_type_lower not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Unknown model type: '{model_type}'. Available models: {available}"
            )

        return cls._registry[model_type_lower]

    @classmethod
    def create_model(cls, model_type: str, **kwargs) -> BaseAnomalyModel:
        """创建模型实例

        Args:
            model_type: 模型类型（如 "ECOD"）
            **kwargs: 模型初始化参数

        Returns:
            模型实例

        Raises:
            ValueError: 模型类型未注册
        """
        model_class = cls.get(model_type)
        logger.info(f"Creating model: {model_type} ({model_class.__name__})")

        return model_class(**kwargs)

    @classmethod
    def list_models(cls) -> list[str]:
        """列出所有已注册的模型

        Returns:
            模型类型列表
        """
        return list(cls._registry.keys())
