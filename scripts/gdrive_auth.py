#!/usr/bin/env python3
"""
Google Drive OAuth2 初次授權腳本
執行一次即可，之後 token 會自動刷新。
用法：python scripts/gdrive_auth.py
"""

from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = Path(__file__).parent / "gdrive_credentials.json"
TOKEN_FILE = Path(__file__).parent / "gdrive_token.json"


def main():
    if not CREDENTIALS_FILE.exists():
        print(
            f"[錯誤] 找不到 {CREDENTIALS_FILE}\n\n"
            "請依照以下步驟取得 credentials.json：\n"
            "1. 前往 https://console.cloud.google.com/\n"
            "2. 建立專案（或選擇現有專案）\n"
            "3. 啟用 Google Drive API\n"
            "4. 建立 OAuth 2.0 用戶端憑證（類型：桌面應用程式）\n"
            "5. 下載 JSON 檔案，重新命名為 gdrive_credentials.json\n"
            "6. 放到 scripts/ 資料夾下\n"
            "7. 再次執行本腳本\n"
        )
        return

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_FILE.write_text(creds.to_json())
    print(f"\n授權成功！Token 已儲存至 {TOKEN_FILE}")
    print("往後執行 gdrive_sync.py 將自動使用此 token，不需再次授權。")


if __name__ == "__main__":
    main()
