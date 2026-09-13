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
        "range": "10d",
        "interval": "1d",
        "includePrePost": "false",
        "events": "div,splits"
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

    timestamps = result.get("timestamp", [])
    closes = result["indicators"]["quote"][0]["close"]

    valid_rows = []

    for ts, close in zip(timestamps, closes):
        if close is not None:
            valid_rows.append((ts, close))

    if len(valid_rows) < 2:
        return None

    previous_ts, previous = valid_rows[-2]
    latest_ts, latest = valid_rows[-1]

    change = latest - previous
    change_pct = (change / previous) * 100 if previous != 0 else 0

    return {
        "price": latest,
        "previous": previous,
        "change": change,
        "change_pct": change_pct,
        "timestamp": latest_ts
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

    indices = [
        ("S&P 500", "%5EGSPC"),
        ("NASDAQ", "%5EIXIC"),
        ("道瓊工業", "%5EDJI"),
        ("費城半導體", "%5ESOX"),
    ]

    tech_stocks = [
        ("NVIDIA", "NVDA"),
        ("Apple", "AAPL"),
        ("Microsoft", "MSFT"),
        ("Alphabet", "GOOGL"),
        ("Amazon", "AMZN"),
        ("Meta", "META"),
        ("Tesla", "TSLA"),
        ("台積電 ADR", "TSM"),
    ]

    macro = [
        ("VIX 恐慌指數", "%5EVIX"),
        ("美元指數", "DX-Y.NYB"),
        ("美國10年期公債殖利率", "%5ETNX"),
    ]

    text = (
        "🇺🇸 **美股晨間市場簡報 V2**\n"
        f"📅 {now.strftime('%Y/%m/%d %H:%M')} 台北時間\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📊 **主要指數**\n\n"
    )

    index_changes = []

    for name, symbol in indices:

        try:
            data = get_yahoo_price(symbol)

            if data is None:
                text += f"⚪ **{name}**：資料不足\n\n"
                continue

            pct = data["change_pct"]
            index_changes.append(pct)

            if pct > 0:
                icon = "🟢"
            elif pct < 0:
                icon = "🔴"
            else:
                icon = "⚪"

            text += (
                f"{icon} **{name}**\n"
                f"`{data['price']:,.2f}` "
                f"({pct:+.2f}%)\n\n"
            )

        except Exception as e:
            print(f"{name} 抓取失敗：{e}")
            text += f"⚠️ **{name}**：抓取失敗\n\n"

    # =====================================================
    # 大盤簡單判讀
    # =====================================================
    if index_changes:

        avg_change = sum(index_changes) / len(index_changes)

        if avg_change >= 1:
            market_view = "🔥 美股整體偏強，市場風險偏好明顯升溫。"

        elif avg_change >= 0.3:
            market_view = "📈 美股整體偏多，主要指數多數走高。"

        elif avg_change > -0.3:
            market_view = "➖ 美股大致震盪，市場方向不明顯。"

        elif avg_change > -1:
            market_view = "📉 美股整體偏弱，市場風險偏好下降。"

        else:
            market_view = "⚠️ 美股明顯走弱，需留意風險情緒快速惡化。"

    else:
        market_view = "⚪ 暫時無法判讀整體市場方向。"

    text += (
        "━━━━━━━━━━━━━━━━━━\n"
        "🧭 **市場氣氛判讀**\n\n"
        f"{market_view}\n\n"
    )

    # =====================================================
    # 科技 / AI
    # =====================================================
    text += (
        "━━━━━━━━━━━━━━━━━━\n"
        "🤖 **大型科技 / AI 股**\n\n"
    )

    tech_performance = []

    for name, symbol in tech_stocks:

        try:
            data = get_yahoo_price(symbol)

            if data is None:
                text += f"⚪ **{name}**：資料不足\n\n"
                continue

            pct = data["change_pct"]
            tech_performance.append((name, pct))

            if pct > 0:
                icon = "🟢"
            elif pct < 0:
                icon = "🔴"
            else:
                icon = "⚪"

            text += (
                f"{icon} **{name}** "
                f"`{data['price']:,.2f}` "
                f"({pct:+.2f}%)\n"
            )

        except Exception as e:
            print(f"{name} 抓取失敗：{e}")
            text += f"⚠️ **{name}**：抓取失敗\n"

    # =====================================================
    # 強弱股
    # =====================================================
    if tech_performance:

        strongest = max(tech_performance, key=lambda x: x[1])
        weakest = min(tech_performance, key=lambda x: x[1])

        text += (
            "\n"
            f"🚀 最強：**{strongest[0]}** {strongest[1]:+.2f}%\n"
            f"🧊 最弱：**{weakest[0]}** {weakest[1]:+.2f}%\n"
        )

    # =====================================================
    # 總經 / 風險
    # =====================================================
    text += (
        "\n━━━━━━━━━━━━━━━━━━\n"
        "🌎 **風險與總經指標**\n\n"
    )

   for name, symbol in macro:

    try:
        data = get_yahoo_price(symbol)

        if data is None:
            text += f"⚪ **{name}**：資料不足\n"
            continue

        pct = data["change_pct"]

        if pct > 0:
            icon = "🟢"
        elif pct < 0:
            icon = "🔴"
        else:
            icon = "⚪"

        # 美國10年債殖利率改用 bps 顯示
        if symbol == "%5ETNX":

            latest_yield = data["price"]
            previous_yield = data["previous"]

            bps_change = (latest_yield - previous_yield) * 10

            if bps_change > 0:
                icon = "🔴"
            elif bps_change < 0:
                icon = "🟢"
            else:
                icon = "⚪"

            text += (
                f"{icon} **{name}** "
                f"`{latest_yield:.2f}%` "
                f"({bps_change:+.1f} bps)\n"
            )

        else:

            text += (
                f"{icon} **{name}** "
                f"`{data['price']:,.2f}` "
                f"({pct:+.2f}%)\n"
            )

    except Exception as e:
        print(f"{name} 抓取失敗：{e}")
        text += f"⚠️ **{name}**：抓取失敗\n"
    # =====================================================
    # 對台股影響
    # =====================================================
    text += (
        "\n━━━━━━━━━━━━━━━━━━\n"
        "🇹🇼 **今日台股開盤前觀察**\n\n"
        "• 費半與 NVIDIA：觀察半導體 / AI 族群氣氛\n"
        "• 台積電 ADR：觀察台積電現貨開盤方向\n"
        "• VIX：判斷全球風險情緒\n"
        "• 美國10年債殖利率：留意高估值科技股壓力\n"
        "• 美元指數：觀察資金風險偏好與亞洲市場壓力\n"
    )

    text += (
        "\n━━━━━━━━━━━━━━━━━━\n"
        "🤖 GitHub Actions 自動市場情報系統\n"
        "資料來源：Yahoo Finance\n"
        "⚠️ 僅供市場資訊整理，不構成投資建議"
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


test_mode = os.environ.get("TEST_MODE", "").upper()

if test_mode == "US":

    print("手動測試：執行美股晨報")
    report = us_market_report()

elif test_mode == "TW":

    print("手動測試：執行台股收盤報")
    report = taiwan_market_report()

elif 7 <= hour <= 9:

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
