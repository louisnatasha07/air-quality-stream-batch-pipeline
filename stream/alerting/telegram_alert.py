"""
Telegram Alert System
Mengirim notifikasi real-time ke Telegram saat terdeteksi anomali
"""

import os
import requests
from datetime import datetime
from typing import Dict, Optional, List
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')


class TelegramAlerter:
    """
    Telegram bot untuk mengirim alert anomali air quality
    """
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        """
        Args:
            bot_token: Telegram Bot API Token (dari @BotFather)
            chat_id: Telegram Chat ID tujuan alert
        """
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        self.enabled = bool(self.bot_token and self.chat_id)
        self.batch_buffer = []  # Buffer untuk mengumpulkan data sebelum kirim
        self.seen_keys = set()  # Track unique city+timestamp untuk deduplikasi
        
        if not self.enabled:
            print("[TELEGRAM ALERT] Disabled - Bot token atau chat ID tidak ditemukan")
        else:
            print(f"[TELEGRAM ALERT] Enabled - Chat ID: {self.chat_id}")
    
    def add_to_batch(self, payload: Dict, anomaly_reason: str):
        """
        Tambahkan data ke batch buffer (tidak langsung kirim)
        Automatically deduplicate by city + timestamp
        
        Args:
            payload: Data air quality
            anomaly_reason: Alasan anomaly jika ada
        """
        if not self.enabled:
            return
        
        # Create unique key for deduplication
        city = payload.get('city', 'Unknown')
        timestamp = payload.get('timestamp', '')
        unique_key = f"{city}_{timestamp}"
        
        # Only add if not already in batch (deduplicate)
        if unique_key not in self.seen_keys:
            self.batch_buffer.append({
                'payload': payload,
                'reason': anomaly_reason,
                'is_anomaly': anomaly_reason != "Normal"
            })
            self.seen_keys.add(unique_key)
    
    def send_batch_summary(self) -> bool:
        """
        Kirim summary dari semua data yang dikumpulkan dalam batch
        
        Returns:
            True jika berhasil kirim, False jika gagal
        """
        if not self.enabled or not self.batch_buffer:
            return False
        
        # Format pesan summary
        message = self._format_batch_summary()
        
        # Kirim ke Telegram
        success = self._send_message(message)
        
        # Clear buffer dan seen keys setelah kirim
        self.batch_buffer.clear()
        self.seen_keys.clear()
        
        return success
    
    def send_anomaly_alert(self, payload: Dict, anomaly_reason: str) -> bool:
        """
        [DEPRECATED] Kirim alert individual (kept for backward compatibility)
        Gunakan add_to_batch() + send_batch_summary() untuk batch notification
        
        Args:
            payload: Data air quality yang terdeteksi anomali
            anomaly_reason: Alasan kenapa dianggap anomali
            
        Returns:
            True jika berhasil kirim, False jika gagal
        """
        if not self.enabled:
            return False
        
        # Format pesan alert
        message = self._format_alert_message(payload, anomaly_reason)
        
        # Kirim ke Telegram
        return self._send_message(message)
    
    def send_daily_summary(self, stats: Dict) -> bool:
        """
        Kirim summary harian (opsional, untuk monitoring)
        
        Args:
            stats: Dictionary berisi statistik harian
        """
        if not self.enabled:
            return False
        
        message = self._format_summary_message(stats)
        return self._send_message(message)
    
    def _categorize_aqi(self, aqi: int, pm25: float) -> tuple:
        """
        Kategorikan AQI ke severity level
        Returns: (category_name, priority_order)
        """
        if aqi > 200 or pm25 > 150:
            return ("HAZARDOUS", 0)
        elif aqi > 150 or pm25 > 100:
            return ("UNHEALTHY", 1)
        elif aqi > 100 or pm25 > 50:
            return ("MODERATE", 2)
        else:
            return ("GOOD", 3)
    
    def _format_batch_summary(self) -> str:
        """
        Format pesan summary batch - clean & professional
        """
        if not self.batch_buffer:
            return ""
        
        # Group by severity
        groups = defaultdict(list)
        
        for item in self.batch_buffer:
            payload = item['payload']
            aqi = payload.get('aqi', 0)
            pm25 = payload.get('pm25', 0)
            pm10 = payload.get('pm10', 0)
            city = payload.get('city', 'Unknown')
            
            category, priority = self._categorize_aqi(aqi, pm25)
            
            groups[category].append({
                'city': city,
                'pm25': pm25,
                'pm10': pm10,
                'aqi': aqi,
                'priority': priority
            })
        
        # Sort categories by priority
        sorted_categories = sorted(groups.items(), key=lambda x: groups[x[0]][0]['priority'])
        
        # Build message
        timestamp = datetime.now().strftime('%H:%M WIB')
        total = len(self.batch_buffer)
        
        lines = [
            f"*AIR QUALITY UPDATE*",
            f"{timestamp} | {total} cities monitored",
            ""
        ]
        
        # Add each category
        for category, cities in sorted_categories:
            count = len(cities)
            
            # Category header with severity indicator
            if category == "HAZARDOUS":
                header = f"[!!] *{category}* ({count})"
            elif category == "UNHEALTHY":
                header = f"[!] *{category}* ({count})"
            elif category == "MODERATE":
                header = f"[~] *{category}* ({count})"
            else:
                header = f"[✓] *{category}* ({count})"
            
            lines.append(header)
            
            # Sort cities by PM2.5 descending
            cities.sort(key=lambda x: x['pm25'], reverse=True)
            
            # Add city details (cleaner format)
            for city_data in cities:
                city_name = city_data['city']
                pm25_val = city_data['pm25']
                pm10_val = city_data['pm10']
                aqi_val = city_data['aqi']
                lines.append(f"  {city_name}: PM2.5 {pm25_val:.1f} | PM10 {pm10_val:.1f} | AQI {aqi_val:.0f}")
            
            lines.append("")  # Empty line between categories
        
        # Footer
        lines.append("Stream monitoring active")
        
        return "\n".join(lines)
    
    def _format_alert_message(self, payload: Dict, reason: str) -> str:
        """
        Format pesan alert individual (untuk backward compatibility)
        """
        timestamp = payload.get('timestamp', datetime.now().isoformat())
        city = payload.get('city', 'Unknown')
        pm25 = payload.get('pm25', 0)
        aqi = payload.get('aqi', 0)
        
        # Tentukan severity level
        category, _ = self._categorize_aqi(aqi, pm25)
        
        message = f"""
*AIR QUALITY ALERT*

Status: {category}
Location: {city}
Time: {timestamp}

PM2.5: {pm25:.1f} μg/m³
AQI: {aqi}

Reason: {reason}
"""
        return message
    
    def _format_summary_message(self, stats: Dict) -> str:
        """
        Format pesan summary harian
        """
        message = f"""
*DAILY AIR QUALITY SUMMARY*

Date: {datetime.now().strftime('%Y-%m-%d')}

PM2.5 Statistics:
  Average: {stats.get('pm25_mean', 0):.1f} μg/m³
  Min: {stats.get('pm25_min', 0):.1f} μg/m³
  Max: {stats.get('pm25_max', 0):.1f} μg/m³

Anomalies Detected: {stats.get('anomaly_count', 0)}

Status: Monitoring active
"""
        return message
    
    def _send_message(self, message: str) -> bool:
        """
        Kirim pesan ke Telegram via Bot API
        """
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print("[TELEGRAM] Alert sent successfully")
                return True
            else:
                print(f"[TELEGRAM ERROR] Failed to send: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[TELEGRAM ERROR] Exception: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test koneksi Telegram bot
        """
        if not self.enabled:
            print("[TELEGRAM] Bot tidak aktif - token/chat_id tidak ada")
            return False
        
        test_message = "*TELEGRAM ALERT SYSTEM*\n\nConnection test successful\nBot is online and ready"
        return self._send_message(test_message)


# Singleton instance
alerter = TelegramAlerter()


# Standalone test function
if __name__ == "__main__":
    print("Testing Telegram Alert System...")
    
    # Test connection
    if alerter.test_connection():
        print("✅ Telegram bot berhasil terhubung!")
        
        # Test batch summary dengan multiple cities
        test_cities = [
            {"city": "Jakarta", "pm25": 165.5, "aqi": 210, "timestamp": datetime.now().isoformat()},
            {"city": "Bandung", "pm25": 75.2, "aqi": 125, "timestamp": datetime.now().isoformat()},
            {"city": "Surabaya", "pm25": 155.0, "aqi": 195, "timestamp": datetime.now().isoformat()},
            {"city": "Yogyakarta", "pm25": 45.0, "aqi": 85, "timestamp": datetime.now().isoformat()},
            {"city": "Semarang", "pm25": 38.5, "aqi": 70, "timestamp": datetime.now().isoformat()},
            {"city": "Medan", "pm25": 92.0, "aqi": 145, "timestamp": datetime.now().isoformat()},
        ]
        
        # Add to batch
        for city_data in test_cities:
            is_anomaly = city_data['pm25'] > 50
            reason = f"PM2.5: {city_data['pm25']}, AQI: {city_data['aqi']}" if is_anomaly else "Normal"
            
            # Fill remaining fields
            city_data.update({
                "latitude": -7.5,
                "longitude": 110.8,
                "pm10": 120.0,
                "carbon_monoxide": 8500,
                "nitrogen_dioxide": 45.2,
                "sulphur_dioxide": 12.3,
                "ozone": 85.1,
            })
            
            alerter.add_to_batch(city_data, reason)
        
        # Send batch summary
        print("\nSending batch summary...")
        alerter.send_batch_summary()
        print("✅ Batch summary sent!")
        
    else:
        print("❌ Telegram bot gagal terhubung")
        print("Pastikan TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID sudah diset di .env")