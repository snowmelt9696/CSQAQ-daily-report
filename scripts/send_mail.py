#!/usr/bin/env python3
"""
CSQAQ Daily Report Email Sender
Reads goods_data.json and sends a formatted HTML email via QQ SMTP.
"""

import json
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "goods_data.json"

# Beijing timezone
TZ_BEIJING = timezone(timedelta(hours=8))


def load_data():
    """Load scraped goods data from JSON file."""
    if not DATA_FILE.exists():
        print(f"ERROR: Data file not found at {DATA_FILE}")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def format_price(value):
    """Format price value, handling None."""
    if value is None:
        return "-"
    return f"¥{value:.2f}"


def format_volume(value):
    """Format volume number."""
    if value is None or value == 0:
        return "-"
    if value >= 10000:
        return f"{value/10000:.1f}万"
    return str(value)


def format_change(value):
    """Format change value with color indicator."""
    if value is None:
        return "-"
    if value > 0:
        return f'+{value:.2f}%'
    elif value < 0:
        return f'{value:.2f}%'
    return "0.00%"


def change_class(value):
    """Return CSS class for change value."""
    if value is None:
        return "neutral"
    if value > 0:
        return "up"
    elif value < 0:
        return "down"
    return "neutral"


def generate_html(data):
    """Generate HTML email from goods data."""
    info = data.get("goods_info", {})
    scraped_at = data.get("scraped_at", "")

    # Parse scrape time to Beijing time
    try:
        dt = datetime.fromisoformat(scraped_at.replace("Z", "+00:00"))
        bj_time = dt.astimezone(TZ_BEIJING).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        bj_time = scraped_at

    # Parse data update time
    updated_at = info.get("updated_at", "")
    try:
        udt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        updated_bj = udt.astimezone(TZ_BEIJING).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        updated_bj = updated_at

    name = info.get("name", "N/A")
    market_hash = info.get("market_hash_name", "N/A")
    type_name = info.get("type_localized_name", "")
    rarity = info.get("rarity_localized_name", "")
    img_url = info.get("img", "")
    rank = info.get("rank_num", "-")
    rank_change = info.get("rank_num_change", 0)

    # Ranking change text
    if rank_change is None:
        rank_change = 0
    rank_str = f"#{rank}" if rank else "-"
    rank_delta = ""
    if rank_change > 0:
        rank_delta = f' <span style="color:#e74c3c;">↑{rank_change}</span>'  # Up is bad for rank
    elif rank_change < 0:
        rank_delta = f' <span style="color:#27ae60;">↓{abs(rank_change)}</span>'  # Down is good for rank

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ font-family: 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 0; color: #333; }}
  .container {{ max-width: 680px; margin: 20px auto; background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden; }}
  .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: #fff; padding: 28px 32px; text-align: center; }}
  .header h1 {{ margin: 0 0 6px 0; font-size: 22px; font-weight: 700; }}
  .header .subtitle {{ font-size: 13px; opacity: 0.8; }}
  .body {{ padding: 24px 32px; }}
  .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }}
  .info-item {{ background: #f8f9fb; border-radius: 8px; padding: 12px 16px; }}
  .info-item .label {{ font-size: 12px; color: #888; margin-bottom: 4px; }}
  .info-item .value {{ font-size: 16px; font-weight: 600; color: #1a1a2e; }}
  table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; }}
  th {{ background: #1a1a2e; color: #fff; padding: 10px 12px; text-align: left; font-weight: 600; }}
  th:first-child {{ border-radius: 6px 0 0 0; }}
  th:last-child {{ border-radius: 0 6px 0 0; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #eef0f4; }}
  tr:hover td {{ background: #f8f9fb; }}
  .up {{ color: #e74c3c; font-weight: 600; }}
  .down {{ color: #27ae60; font-weight: 600; }}
  .neutral {{ color: #888; }}
  .section-title {{ font-size: 16px; font-weight: 700; color: #1a1a2e; margin: 24px 0 12px 0; padding-bottom: 6px; border-bottom: 2px solid #0f3460; }}
  .footer {{ background: #f8f9fb; padding: 16px 32px; text-align: center; font-size: 11px; color: #aaa; }}
  .footer a {{ color: #0f3460; text-decoration: none; }}
  .platform-tag {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-left: 4px; }}
  .tag-buff {{ background: #fff3e0; color: #e65100; }}
  .tag-yyyp {{ background: #e8f5e9; color: #2e7d32; }}
  .tag-steam {{ background: #e3f2fd; color: #1565c0; }}
  .tag-c5 {{ background: #fce4ec; color: #c62828; }}
  .tag-igxe {{ background: #f3e5f5; color: #6a1b9a; }}
  .tag-eco {{ background: #e0f7fa; color: #00695c; }}
  @media (max-width: 480px) {{
    .info-grid {{ grid-template-columns: 1fr; }}
    .body {{ padding: 16px; }}
    table {{ font-size: 12px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📊 {name} 行情日报</h1>
    <div class="subtitle">{market_hash} · {type_name} · {rarity} · 排名 {rank_str}{rank_delta}</div>
  </div>
  <div class="body">

    <div class="info-grid">
      <div class="info-item">
        <div class="label">📅 抓取时间（北京时间）</div>
        <div class="value">{bj_time}</div>
      </div>
      <div class="info-item">
        <div class="label">🕐 数据更新时间</div>
        <div class="value">{updated_bj}</div>
      </div>
    </div>

    <!-- Price Comparison Table -->
    <div class="section-title">💰 各平台价格对比</div>
    <table>
      <tr>
        <th>平台</th>
        <th>售价</th>
        <th>求购价</th>
        <th>在售数量</th>
        <th>求购数量</th>
      </tr>
      <tr>
        <td><span class="platform-tag tag-buff">Buff</span></td>
        <td><b>{format_price(info.get('buff_sell_price'))}</b></td>
        <td>{format_price(info.get('buff_buy_price'))}</td>
        <td>{format_volume(info.get('buff_sell_num'))}</td>
        <td>{format_volume(info.get('buff_buy_num'))}</td>
      </tr>
      <tr>
        <td><span class="platform-tag tag-yyyp">悠悠有品</span></td>
        <td><b>{format_price(info.get('yyyp_sell_price'))}</b></td>
        <td>{format_price(info.get('yyyp_buy_price'))}</td>
        <td>{format_volume(info.get('yyyp_sell_num'))}</td>
        <td>{format_volume(info.get('yyyp_buy_num'))}</td>
      </tr>
      <tr>
        <td><span class="platform-tag tag-steam">Steam</span></td>
        <td><b>{format_price(info.get('steam_sell_price'))}</b></td>
        <td>{format_price(info.get('steam_buy_price'))}</td>
        <td>{format_volume(info.get('steam_sell_num'))}</td>
        <td>{format_volume(info.get('steam_buy_num'))}</td>
      </tr>
      <tr>
        <td><span class="platform-tag tag-c5">C5GAME</span></td>
        <td><b>{format_price(info.get('c5_sell_price'))}</b></td>
        <td>{format_price(info.get('c5_buy_price'))}</td>
        <td>{format_volume(info.get('c5_sell_num'))}</td>
        <td>{format_volume(info.get('c5_buy_num'))}</td>
      </tr>
      <tr>
        <td><span class="platform-tag tag-igxe">IGXE</span></td>
        <td><b>{format_price(info.get('igxe_sell_price'))}</b></td>
        <td>{format_price(info.get('igxe_buy_price'))}</td>
        <td>{format_volume(info.get('igxe_sell_num'))}</td>
        <td>{format_volume(info.get('igxe_buy_num'))}</td>
      </tr>
      <tr>
        <td><span class="platform-tag tag-eco">ECO</span></td>
        <td><b>{format_price(info.get('eco_sell_price'))}</b></td>
        <td>{format_price(info.get('eco_buy_price'))}</td>
        <td>{format_volume(info.get('eco_sell_num'))}</td>
        <td>{format_volume(info.get('eco_buy_num'))}</td>
      </tr>
    </table>

    <!-- Buff Price Change Table -->
    <div class="section-title">📈 Buff 售价涨跌幅</div>
    <table>
      <tr>
        <th>周期</th>
        <th>涨跌金额</th>
        <th>涨跌幅</th>
      </tr>
      <tr>
        <td>1 天</td>
        <td class="{change_class(info.get('sell_price_1'))}">{format_price(info.get('sell_price_1'))}</td>
        <td class="{change_class(info.get('sell_price_rate_1'))}">{format_change(info.get('sell_price_rate_1'))}</td>
      </tr>
      <tr>
        <td>7 天</td>
        <td class="{change_class(info.get('sell_price_7'))}">{format_price(info.get('sell_price_7'))}</td>
        <td class="{change_class(info.get('sell_price_rate_7'))}">{format_change(info.get('sell_price_rate_7'))}</td>
      </tr>
      <tr>
        <td>15 天</td>
        <td class="{change_class(info.get('sell_price_15'))}">{format_price(info.get('sell_price_15'))}</td>
        <td class="{change_class(info.get('sell_price_rate_15'))}">{format_change(info.get('sell_price_rate_15'))}</td>
      </tr>
      <tr>
        <td>30 天</td>
        <td class="{change_class(info.get('sell_price_30'))}">{format_price(info.get('sell_price_30'))}</td>
        <td class="{change_class(info.get('sell_price_rate_30'))}">{format_change(info.get('sell_price_rate_30'))}</td>
      </tr>
      <tr>
        <td>90 天</td>
        <td class="{change_class(info.get('sell_price_90'))}">{format_price(info.get('sell_price_90'))}</td>
        <td class="{change_class(info.get('sell_price_rate_90'))}">{format_change(info.get('sell_price_rate_90'))}</td>
      </tr>
      <tr>
        <td>180 天</td>
        <td class="{change_class(info.get('sell_price_180'))}">{format_price(info.get('sell_price_180'))}</td>
        <td class="{change_class(info.get('sell_price_rate_180'))}">{format_change(info.get('sell_price_rate_180'))}</td>
      </tr>
      <tr>
        <td>365 天</td>
        <td class="{change_class(info.get('sell_price_365'))}">{format_price(info.get('sell_price_365'))}</td>
        <td class="{change_class(info.get('sell_price_rate_365'))}">{format_change(info.get('sell_price_rate_365'))}</td>
      </tr>
    </table>

    <!-- Additional Info -->
    <div class="section-title">📋 其他信息</div>
    <div class="info-grid">
      <div class="info-item">
        <div class="label">Buff→Steam 求购折价</div>
        <div class="value">{info.get('buff_steam_buy_conversion', '-')}</div>
      </div>
      <div class="info-item">
        <div class="label">Buff→Steam 售价折价</div>
        <div class="value">{info.get('buff_steam_sell_conversion', '-')}</div>
      </div>
      <div class="info-item">
        <div class="label">Steam→Buff 求购折价</div>
        <div class="value">{info.get('steam_buff_buy_conversion', '-')}</div>
      </div>
      <div class="info-item">
        <div class="label">Steam→Buff 售价折价</div>
        <div class="value">{info.get('steam_buff_sell_conversion', '-')}</div>
      </div>
    </div>

  </div>
  <div class="footer">
    数据来源：<a href="https://csqaq.com/goods/19521">CSQAQ.com</a> · 自动生成于 {bj_time} · 仅供参考
  </div>
</div>
</body>
</html>"""

    return html


def send_email(html_content, subject):
    """Send email via QQ SMTP."""
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.qq.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    sender_email = os.environ.get("QQ_EMAIL")
    sender_password = os.environ.get("QQ_AUTH_CODE")
    recipient_email = os.environ.get("RECIPIENT_EMAIL")

    if not all([sender_email, sender_password, recipient_email]):
        print("ERROR: Missing required environment variables:")
        print(f"  QQ_EMAIL: {'set' if sender_email else 'MISSING'}")
        print(f"  QQ_AUTH_CODE: {'set' if sender_password else 'MISSING'}")
        print(f"  RECIPIENT_EMAIL: {'set' if recipient_email else 'MISSING'}")
        sys.exit(1)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"CSQAQ日报 <{sender_email}>"
    msg["To"] = recipient_email

    msg.attach(MIMEText(html_content, "html", "utf-8"))

    print(f"Sending email to {recipient_email} via {smtp_server}:{smtp_port}...")

    try:
        if smtp_port == 465:
            # SSL mode
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
        else:
            # STARTTLS mode
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())

        print("Email sent successfully!")
    except smtplib.SMTPAuthenticationError:
        print("ERROR: SMTP authentication failed. Check QQ_EMAIL and QQ_AUTH_CODE.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR sending email: {e}")
        sys.exit(1)


def main():
    print(f"Loading data from {DATA_FILE}...")
    data = load_data()

    info = data.get("goods_info", {})
    name = info.get("name", "CSQAQ Goods")
    date_str = datetime.now(TZ_BEIJING).strftime("%Y-%m-%d")

    subject = f"📊 {name} 行情日报 - {date_str}"

    print(f"Generating HTML email for: {name}")
    html = generate_html(data)

    send_email(html, subject)


if __name__ == "__main__":
    main()
