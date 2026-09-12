import os
import requests

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

if not WEBHOOK_URL:
    raise ValueError("找不到 DISCORD_WEBHOOK_URL")

message = {
    "content": "✅ Discord 市場情報系統測試成功！GitHub Actions 已經可以傳送訊息。"
}

response = requests.post(WEBHOOK_URL, json=message)

if response.status_code == 204:
    print("Discord 傳送成功！")
else:
    print("Discord 傳送失敗")
    print("狀態碼：", response.status_code)
    print("回應：", response.text)
