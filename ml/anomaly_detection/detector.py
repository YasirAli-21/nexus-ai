import pandas as pd
from sklearn.ensemble import IsolationForest


FEATURES = [
    "cpu_usage",
    "memory_usage",
    "latency_ms",
    "request_count",
    "error_rate",
]


class AnomalyDetector:

    def __init__(self):
        self.model = IsolationForest(
            contamination=0.05,
            random_state=42
        )

    def train(self, normal_data: pd.DataFrame):
        self.model.fit(normal_data[FEATURES])

    def predict(self, data: pd.DataFrame):
        predictions = self.model.predict(data[FEATURES])

        result = data.copy()

        result["anomaly"] = predictions
        result["is_anomaly"] = result["anomaly"] == -1

        return result