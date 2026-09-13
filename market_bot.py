   import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo


# =========================================================
# Discord Webhook
# =========================================================
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
        "events": "div,splits",
    }

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    chart = data.get("chart", {})
    results = chart.get("result")

    if not results:
        return None

    result = results[0]

    timestamps = result.get("timestamp", [])

    indicators = result.get("indicators", {})
    quotes = indicators.get("quote", [])

    if not quotes:
        return None

    closes = quotes[0].get("close", [])

    valid_rows = []

    for ts, close in zip(timestamps, closes):
        if close is not None:
            valid_rows.append((ts, close))

    if len(valid_rows) < 2:
        return None

    previous_ts, previous = valid_rows[-2]
    latest_ts, latest = valid_rows[-1]

    change = latest - previous

    if previous != 0:
        change_pct = (change / previous) * 100
    else:
        change_pct = 0

    return {
        "price": latest,
        "previous": previous,
        "change": change,
        "change_pct": change_pct,
        "timestamp": latest_ts,
        "previous_timestamp": previous_ts,
    }


# =========================================================
# 一般市場格式
# =========================================================
def format_market(name, symbol):

    try:

        data = get_yahoo_price(symbol)

        if data is None:
            return f"⚪ **{name}**：資料不足"

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

        return f"⚠️ **{name}**：抓取失敗"


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

    # =====================================================
    # 主要指數
    # =====================================================
    index_changes = []

    for name, symbol in indices:

        try:

            data = get_yahoo_price(symbol)

            if data is None:
                text += f"⚪ **{name}**：資料不足\n\n"
                continue

            pct = data["change_pct"]

            index_changes.append(
                {
                    "name": name,
                    "symbol": symbol,
                    "pct": pct,
                }
            )

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
    # 市場氣氛
    # =====================================================
    if index_changes:

        pct_values = [x["pct"] for x in index_changes]

        avg_change = sum(pct_values) / len(pct_values)

        positive_count = sum(
            1 for x in pct_values if x > 0
        )

        negative_count = sum(
            1 for x in pct_values if x < 0
        )

        if avg_change >= 1 and positive_count >= 3:

            market_view = (
                "🔥 美股整體明顯偏強，"
                "主要指數同步上漲，風險偏好升溫。"
            )

        elif avg_change >= 0.3 and positive_count >= 3:

            market_view = (
                "📈 美股整體偏多，"
                "主要指數多數走高。"
            )

        elif avg_change <= -1 and negative_count >= 3:

            market_view = (
                "⚠️ 美股整體明顯走弱，"
                "市場風險情緒升高。"
            )

        elif avg_change <= -0.3 and negative_count >= 3:

            market_view = (
                "📉 美股整體偏弱，"
                "主要指數多數下跌。"
            )

        else:

            market_view = (
                "➖ 美股漲跌互見，"
                "市場目前偏震盪。"
            )

    else:

        market_view = "⚪ 暫時無法判讀整體市場方向。"

    text += (
        "━━━━━━━━━━━━━━━━━━\n"
        "🧭 **市場氣氛判讀**\n\n"
        f"{market_view}\n\n"
    )

    # =====================================================
    # 大型科技 / AI
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

                text += (
                    f"⚪ **{name}**：資料不足\n"
                )

                continue

            pct = data["change_pct"]

            tech_performance.append(
                (name, pct)
            )

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

            print(
                f"{name} 抓取失敗：{e}"
            )

            text += (
                f"⚠️ **{name}**：抓取失敗\n"
            )

    # =====================================================
    # 科技股強弱
    # =====================================================
    if tech_performance:

        strongest = max(
            tech_performance,
            key=lambda x: x[1]
        )

        weakest = min(
            tech_performance,
            key=lambda x: x[1]
        )

        text += (
            "\n"
            f"🚀 最強：**{strongest[0]}** "
            f"{strongest[1]:+.2f}%\n"
            f"🧊 最弱：**{weakest[0]}** "
            f"{weakest[1]:+.2f}%\n"
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

                text += (
                    f"⚪ **{name}**：資料不足\n"
                )

                continue

            pct = data["change_pct"]

            # =================================================
            # VIX
            # =================================================
            if symbol == "%5EVIX":

                vix = data["price"]

                if vix < 15:

                    vix_view = (
                        "市場情緒偏穩定"
                    )

                elif vix < 20:

                    vix_view = (
                        "市場情緒正常"
                    )

                elif vix < 30:

                    vix_view = (
                        "市場避險情緒升高"
                    )

                else:

                    vix_view = (
                        "⚠️ 市場恐慌程度偏高"
                    )

                # VIX 上升 = 風險增加
                if pct > 0:
                    icon = "🔴"
                elif pct < 0:
                    icon = "🟢"
                else:
                    icon = "⚪"

                text += (
                    f"{icon} **{name}** "
                    f"`{vix:.2f}` "
                    f"({pct:+.2f}%) "
                    f"｜{vix_view}\n"
                )

            # =================================================
            # 美元指數
            # =================================================
            elif symbol == "DX-Y.NYB":

                dollar = data["price"]

                if pct >= 0.5:

                    dollar_view = (
                        "美元明顯走強，"
                        "對風險資產偏壓力"
                    )

                elif pct > 0:

                    dollar_view = (
                        "美元小幅走強"
                    )

                elif pct <= -0.5:

                    dollar_view = (
                        "美元明顯走弱，"
                        "風險資產壓力減輕"
                    )

                elif pct < 0:

                    dollar_view = (
                        "美元小幅走弱"
                    )

                else:

                    dollar_view = (
                        "美元大致持平"
                    )

                # 美元上升以風險角度標紅
                if pct > 0:
                    icon = "🔴"
                elif pct < 0:
                    icon = "🟢"
                else:
                    icon = "⚪"

                text += (
                    f"{icon} **{name}** "
                    f"`{dollar:.2f}` "
                    f"({pct:+.2f}%) "
                    f"｜{dollar_view}\n"
                )

            # =================================================
            # 美國 10 年債殖利率
            # =================================================
            elif symbol == "%5ETNX":

                latest_yield = data["price"]
                previous_yield = data["previous"]

                # 4.90 → 4.97
                # = +0.07 percentage point
                # = +7 basis points
                bps_change = (
                    latest_yield
                    - previous_yield
                ) * 100

                if bps_change > 0:
                    icon = "🔴"
                elif bps_change < 0:
                    icon = "🟢"
                else:
                    icon = "⚪"

                if bps_change >= 10:

                    yield_view = (
                        "殖利率明顯上升，"
                        "科技成長股估值壓力增加"
                    )

                elif bps_change > 0:

                    yield_view = (
                        "殖利率小幅上升"
                    )

                elif bps_change <= -10:

                    yield_view = (
                        "殖利率明顯下降，"
                        "科技股估值壓力減輕"
                    )

                elif bps_change < 0:

                    yield_view = (
                        "殖利率小幅下降"
                    )

                else:

                    yield_view = (
                        "殖利率大致持平"
                    )

                text += (
                    f"{icon} **{name}** "
                    f"`{latest_yield:.3f}%` "
                    f"({bps_change:+.1f} bps) "
                    f"｜{yield_view}\n"
                )

            # =================================================
            # 其他
            # =================================================
            else:

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

            print(
                f"{name} 抓取失敗：{e}"
            )

            text += (
                f"⚠️ **{name}**：抓取失敗\n"
            )

    # =====================================================
    # 台股開盤前觀察
    # =====================================================
    text += (
        "\n━━━━━━━━━━━━━━━━━━\n"
        "🇹🇼 **今日台股開盤前觀察**\n\n"
        "• 費半：觀察台灣半導體族群氣氛\n"
        "• NVIDIA：觀察 AI 伺服器與供應鏈\n"
        "• 台積電 ADR：觀察台積電開盤方向\n"
        "• VIX：判斷全球市場風險情緒\n"
        "• 美國10年債：觀察科技股估值壓力\n"
        "• 美元指數：觀察全球資金風險偏好\n"
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

    now = datetime.now(
        ZoneInfo("Asia/Taipei")
    )

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

        text += (
            format_market(
                name,
                symbol
            )
            + "\n\n"
        )

    text += (
        "━━━━━━━━━━━━━━━━━━\n"
        "🔥 **大型權值 / AI 指標股**\n\n"
    )

    stock_performance = []

    for name, symbol in stocks:

        try:

            data = get_yahoo_price(symbol)

            if data is None:

                text += (
                    f"⚪ **{name}**：資料不足\n"
                )

                continue

            pct = data["change_pct"]

            stock_performance.append(
                (name, pct)
            )

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

            print(
                f"{name} 抓取失敗：{e}"
            )

            text += (
                f"⚠️ **{name}**：抓取失敗\n"
            )

    if stock_performance:

        strongest = max(
            stock_performance,
            key=lambda x: x[1]
        )

        weakest = min(
            stock_performance,
            key=lambda x: x[1]
        )

        text += (
            "\n"
            f"🚀 最強：**{strongest[0]}** "
            f"{strongest[1]:+.2f}%\n"
            f"🧊 最弱：**{weakest[0]}** "
            f"{weakest[1]:+.2f}%\n"
        )

    text += (
        "\n━━━━━━━━━━━━━━━━━━\n"
        "🤖 GitHub Actions 自動市場情報系統\n"
        "資料來源：Yahoo Finance\n"
        "⚠️ 僅供市場資訊整理，不構成投資建議"
    )

    return text


# =========================================================
# Discord 傳送
# =========================================================
def send_discord(text):

    # Discord 單則訊息上限約 2000 字
    max_length = 1900

    chunks = [
        text[i:i + max_length]
        for i in range(
            0,
            len(text),
            max_length
        )
    ]

    for chunk in chunks:

        response = requests.post(
            WEBHOOK_URL,
            json={
                "content": chunk
            },
            timeout=15,
        )

        if response.status_code not in [
            200,
            204,
        ]:

            raise Exception(
                "Discord 傳送失敗："
                f"{response.status_code} "
                f"{response.text}"
            )


# =========================================================
# 判斷現在要傳哪一份
# =========================================================
now = datetime.now(
    ZoneInfo("Asia/Taipei")
)

print(
    "目前台北時間：",
    now
)

hour = now.hour

test_mode = os.environ.get(
    "TEST_MODE",
    ""
).upper()


# =========================================================
# 手動選 US
# =========================================================
if test_mode == "US":

    print(
        "手動測試：執行美股晨報"
    )

    report = us_market_report()


# =========================================================
# 手動選 TW
# =========================================================
elif test_mode == "TW":

    print(
        "手動測試：執行台股收盤報"
    )

    report = taiwan_market_report()


# =========================================================
# AUTO / 自動排程
# =========================================================
elif 7 <= hour <= 9:

    print(
        "自動排程：執行美股晨報"
    )

    report = us_market_report()


elif 14 <= hour <= 16:

    print(
        "自動排程：執行台股收盤報"
    )

    report = taiwan_market_report()


# =========================================================
# 其他時間
# =========================================================
else:

    print(
        "目前不是正式排程時段"
    )

    report = (
        "🧪 **Discord 市場系統測試**\n\n"
        f"目前台北時間："
        f"{now.strftime('%Y/%m/%d %H:%M:%S')}\n\n"
        "✅ GitHub Actions\n"
        "✅ Python\n"
        "✅ Discord Webhook\n\n"
        "系統運作正常。"
    )


# =========================================================
# 傳送 Discord
# =========================================================
send_discord(report)

print(
    "Discord 傳送完成"
)
