"""
Telegram Alert System
Mengirim notifikasi real-time ke Telegram saat terdeteksi anomali
"""

import os
import requests
from datetime import datetime
from typing import Dict, Optional
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
        
        if not self.enabled:
            print("[TELEGRAM ALERT] Disabled - Bot token atau chat ID tidak ditemukan")
        else:
            print(f"[TELEGRAM ALERT] Enabled - Chat ID: {self.chat_id}")
    
    def send_anomaly_alert(self, payload: Dict, anomaly_reason: str) -> bool:
        """
        Kirim alert anomali ke Telegram
        
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
    
    def _format_alert_message(self, payload: Dict, reason: str) -> str:
        """
        Format pesan alert dengan emoji dan struktur yang jelas
        """
        timestamp = payload.get('timestamp', datetime.now().isoformat())
        city = payload.get('city', 'Unknown')
        pm25 = payload.get('pm25', 0)
        aqi = payload.get('aqi', 0)
        
        # Tentukan severity level
        if aqi > 200 or pm25 > 100:
            severity = "🔴 CRITICAL"
        elif aqi > 150 or pm25 > 75:
            severity = "🟠 HIGH"
        else:
            severity = "🟡 MODERATE"
        
        message = f"""
🚨 *AIR QUALITY ANOMALY DETECTED*

{severity}

📍 *Lokasi:* {city}
🕐 *Waktu:* {timestamp}

📊 *Metrics:*
• PM2.5: {pm25:.1f} μg/m³
• AQI: {aqi}
• CO: {payload.get('carbon_monoxide', 0):.0f} μg/m³
• NO₂: {payload.get('nitrogen_dioxide', 0):.1f} μg/m³
• O₃: {payload.get('ozone', 0):.1f} μg/m³

⚠️ *Alasan:*
{reason}

💡 *Rekomendasi:*
{"Hindari aktivitas outdoor" if aqi > 150 else "Gunakan masker jika keluar"}
"""
        return message
    
    def _format_summary_message(self, stats: Dict) -> str:
        """
        Format pesan summary harian
        """
        message = f"""
📊 *Daily Air Quality Summary*

🕐 *Tanggal:* {datetime.now().strftime('%Y-%m-%d')}

📈 *Statistik PM2.5:*
• Rata-rata: {stats.get('pm25_mean', 0):.1f} μg/m³
• Min: {stats.get('pm25_min', 0):.1f} μg/m³
• Max: {stats.get('pm25_max', 0):.1f} μg/m³

🚨 *Anomali Terdeteksi:* {stats.get('anomaly_count', 0)} kali

✅ *Status:* Monitoring aktif
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
        
        test_message = "🤖 Telegram Alert System - Test Connection\n\nBot berhasil terhubung!"
        return self._send_message(test_message)


# Singleton instance
alerter = TelegramAlerter()


# Standalone test function
if __name__ == "__main__":
    print("Testing Telegram Alert System...")
    
    # Test connection
    if alerter.test_connection():
        print("✅ Telegram bot berhasil terhubung!")
        
        # Test anomaly alert
        test_payload = {
            "timestamp": datetime.now().isoformat(),
            "latitude": -7.5561,
            "longitude": 110.8317,
            "pm25": 75.5,
            "pm10": 120.0,
            "carbon_monoxide": 8500,
            "nitrogen_dioxide": 45.2,
            "sulphur_dioxide": 12.3,
            "ozone": 85.1,
            "aqi": 125
        }
        
        alerter.send_anomaly_alert(
            test_payload,
            "PM2.5 tinggi (75.5 μg/m³) | AQI tidak sehat (125)"
        )
    else:
        print("❌ Telegram bot gagal terhubung")
        print("Pastikan TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID sudah diset di .env")
