"""
Advanced Anomaly Detection Module
Menggunakan statistical methods untuk deteksi anomali air quality
"""

import numpy as np
from collections import deque
from typing import Tuple, Dict


class AnomalyDetector:
    """
    Anomaly detector menggunakan Z-score dan rolling statistics
    untuk mendeteksi pola tidak normal pada data air quality.
    """
    
    def __init__(self, window_size: int = 20, z_threshold: float = 3.0):
        """
        Args:
            window_size: Jumlah data points untuk rolling calculation
            z_threshold: Threshold Z-score untuk menentukan anomali
        """
        self.window_size = window_size
        self.z_threshold = z_threshold
        
        # Rolling windows untuk setiap metric
        self.pm25_window = deque(maxlen=window_size)
        self.aqi_window = deque(maxlen=window_size)
        self.co_window = deque(maxlen=window_size)
        
    def detect(self, payload: Dict) -> Tuple[bool, str]:
        """
        Deteksi anomali berdasarkan multiple methods:
        1. Rule-based threshold (WHO standards)
        2. Statistical Z-score
        3. Sudden spike detection
        
        Args:
            payload: Dictionary berisi air quality metrics
            
        Returns:
            Tuple (is_anomaly, reason)
        """
        pm25 = payload.get('pm25') or 0
        aqi = payload.get('aqi') or 0
        co = payload.get('carbon_monoxide') or 0
        
        anomalies = []
        
        # Method 1: Rule-based (WHO Air Quality Guidelines)
        if pm25 > 50:  # WHO 24-hour guideline: 15 μg/m³, alert at 50
            anomalies.append(f"PM2.5 tinggi ({pm25:.1f} μg/m³)")
        
        if aqi > 100:  # AQI > 100 = Unhealthy for sensitive groups
            anomalies.append(f"AQI tidak sehat ({aqi})")
        
        if co > 10000:  # CO > 10 mg/m³ (10000 μg/m³)
            anomalies.append(f"CO tinggi ({co:.0f} μg/m³)")
        
        # Method 2: Statistical Z-score (jika sudah ada cukup data)
        if len(self.pm25_window) >= 10:
            z_score = self._calculate_zscore(pm25, self.pm25_window)
            if abs(z_score) > self.z_threshold:
                anomalies.append(f"PM2.5 anomali statistik (Z={z_score:.2f})")
        
        # Method 3: Sudden spike detection
        if len(self.pm25_window) > 0:
            last_pm25 = self.pm25_window[-1]
            if pm25 > last_pm25 * 2:  # Spike 2x dari nilai sebelumnya
                anomalies.append(f"Lonjakan PM2.5 mendadak ({last_pm25:.1f} → {pm25:.1f})")
        
        # Update rolling windows
        self.pm25_window.append(pm25)
        self.aqi_window.append(aqi)
        self.co_window.append(co)
        
        # Return result
        if anomalies:
            return True, " | ".join(anomalies)
        else:
            return False, "Normal"
    
    def _calculate_zscore(self, value: float, window: deque) -> float:
        """
        Hitung Z-score untuk deteksi outlier
        Z = (x - μ) / σ
        """
        if len(window) < 2:
            return 0.0
        
        mean = np.mean(window)
        std = np.std(window)
        
        if std == 0:
            return 0.0
        
        return (value - mean) / std
    
    def get_statistics(self) -> Dict:
        """
        Dapatkan statistik rolling window untuk monitoring
        """
        if len(self.pm25_window) == 0:
            return {}
        
        return {
            "pm25_mean": np.mean(self.pm25_window),
            "pm25_std": np.std(self.pm25_window),
            "pm25_min": np.min(self.pm25_window),
            "pm25_max": np.max(self.pm25_window),
            "window_size": len(self.pm25_window)
        }


# Singleton instance untuk digunakan di consumer
detector = AnomalyDetector(window_size=20, z_threshold=3.0)
