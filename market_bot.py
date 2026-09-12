import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

if not WEBHOOK_URL:
    raise ValueError("找不到 DISCORD_WEBHOOK_URL")


# =========================================================
# Yahoo Finance 抓行情
# =========================================================
def get_yahoo_price(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    params = {
        "range": "5d",
        "interval": "1d"
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=15
    )

    r.raise_for_status()

    data = r.json()

    result = data["chart"]["result"][0]

    closes = result["indicators"]["quote"][0]["close"]

    closes = [x for x in closes if x is not None]

    if len(closes) < 2:
        return None

    previous = closes[-2]
    latest = closes[-1]

    change = latest - previous
    change_pct = (change / previous) * 100

    return {
        "price": latest,
        "change": change,
        "change_pct": change_pct
    }


# =========================================================
# 格式
# =========================================================
def format_market(name, symbol):

    try:
        data = get_yahoo_price(symbol)

        if data is None:
            return f"⚪ {name}：資料不足"

        pct = data["change_pct"]

        if pct > 0:
            icon = "🟢"
        elif pct < 0:
            icon = "🔴"
        else:
            icon = "⚪"

        return (
            f"{icon} **{name}**\n"
            f"`{data['price']:,.2f}` "
            f"({pct:+.2f}%)"
        )

    except Exception as e:
        print(f"{name} 抓取失敗：{e}")
        return f"⚠️ {name}：抓取失敗"


# =========================================================
# 美股晨報
# =========================================================
def us_market_report():

    now = datetime.now(ZoneInfo("Asia/Taipei"))

    markets = [
        ("S&P 500", "%5EGSPC"),
        ("NASDAQ", "%5EIXIC"),
        ("道瓊工業", "%5EDJI"),
        ("費城半導體", "%5ESOX"),
    ]

    stocks = [
        ("NVIDIA", "NVDA"),
        ("Apple", "AAPL"),
        ("Microsoft", "MSFT"),
        ("Alphabet", "GOOGL"),
        ("Amazon", "AMZN"),
        ("Meta", "META"),
        ("Tesla", "TSLA"),
        ("台積電 ADR", "TSM"),
    ]

    text = (
        "🇺🇸 **美股晨間市場簡報**\n"
        f"📅 {now.strftime('%Y/%m/%d %H:%M')} 台北時間\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📊 **主要指數**\n\n"
    )

    for name, symbol in markets:
        text += format_market(name, symbol) + "\n\n"

    text += "━━━━━━━━━━━━━━━━━━\n"
    text += "💻 **大型科技 / AI 股**\n\n"

    for name, symbol in stocks:
        text += format_market(name, symbol) + "\n\n"

    text += (
        "━━━━━━━━━━━━━━━━━━\n"
        "🤖 自動市場情報系統\n"
        "資料來源：Yahoo Finance"
    )

    return text


# =========================================================
# 台股收盤報
# =========================================================
def taiwan_market_report():

    now = datetime.now(ZoneInfo("Asia/Taipei"))

    markets = [
        ("台灣加權指數", "%5ETWII"),
    ]

    stocks = [
        ("台積電", "2330.TW"),
        ("聯發科", "2454.TW"),
        ("鴻海", "2317.TW"),
        ("台達電", "2308.TW"),
        ("廣達", "2382.TW"),
        ("緯創", "3231.TW"),
        ("緯穎", "6669.TW"),
    ]

    text = (
        "🇹🇼 **台股收盤市場簡報**\n"
        f"📅 {now.strftime('%Y/%m/%d %H:%M')} 台北時間\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📊 **大盤**\n\n"
    )

    for name, symbol in markets:
        text += format_market(name, symbol) + "\n\n"

    text += "━━━━━━━━━━━━━━━━━━\n"
    text += "🔥 **大型權值 / AI 指標股**\n\n"

    for name, symbol in stocks:
        text += format_market(name, symbol) + "\n\n"

    text += (
        "━━━━━━━━━━━━━━━━━━\n"
        "🤖 自動市場情報系統\n"
        "資料來源：Yahoo Finance"
    )

    return text


# =========================================================
# Discord
# =========================================================
def send_discord(text):

    # Discord 單則訊息限制約 2000 字
    max_length = 1900

    chunks = [
        text[i:i + max_length]
        for i in range(0, len(text), max_length)
    ]

    for chunk in chunks:

        response = requests.post(
            WEBHOOK_URL,
            json={"content": chunk},
            timeout=15
        )

        if response.status_code not in [200, 204]:
            raise Exception(
                f"Discord 傳送失敗："
                f"{response.status_code} {response.text}"
            )


# =========================================================
# 判斷現在該傳哪一份
# =========================================================
now = datetime.now(ZoneInfo("Asia/Taipei"))

print("目前台北時間：", now)

hour = now.hour


if 7 <= hour <= 9:

    print("執行美股晨報")
    report = us_market_report()

elif 14 <= hour <= 16:

    print("執行台股收盤報")
    report = taiwan_market_report()

else:

    print("目前不是排程時段，執行測試模式")

    report = (
        "🧪 **Discord 市場系統測試**\n\n"
        f"目前台北時間：{now.strftime('%Y/%m/%d %H:%M:%S')}\n\n"
        "✅ GitHub Actions\n"
        "✅ Python\n"
        "✅ Discord Webhook\n\n"
        "系統運作正常。"
    )


send_discord(report)

print("Discord 傳送完成")
