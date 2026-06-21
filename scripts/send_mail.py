#!/usr/bin/env python3
"""
CSQAQ Daily Report Email Sender (Multi-Goods)
Reads all goods_*.json files and sends a combined HTML email via QQ SMTP.
"""

import json
import os
import sys
import smtplib
import glob
from email.mime.text import MIMEText
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
TZ_BEIJING = timezone(timedelta(hours=8))


def load_all_data():
    """Load all goods_*.json files from data directory."""
    pattern = str(DATA_DIR / "goods_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"ERROR: No goods_*.json files found in {DATA_DIR}")
        sys.exit(1)

    results = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            results.append(json.load(fh))
    return results


def fmt_price(value):
    if value is None:
        return "-"
    return f"¥{value:.2f}"


def fmt_vol(value):
    if value is None or value == 0:
        return "-"
    if value >= 10000:
        return f"{value/10000:.1f}万"
    return str(value)


def fmt_change(value):
    if value is None:
        return "-"
    if value > 0:
        return f"+{value:.2f}%"
    elif value < 0:
        return f"{value:.2f}%"
    return "0.00%"


def fmt_amt(value):
    """Format price change amount."""
    if value is None:
        return "-"
    if value > 0:
        return f"+¥{value:.2f}"
    elif value < 0:
        return f"-¥{abs(value):.2f}"
    return "¥0.00"


def cls(value):
    if value is None:
        return "neutral"
    if value > 0:
        return "up"
    elif value < 0:
        return "down"
    return "neutral"


def generate_item_section(data):
    """Generate HTML section for a single goods item."""
    info = data.get("goods_info", {})
    goods_id = data.get("goods_id", "N/A")

    name = info.get("name", "N/A")
    market_hash = info.get("market_hash_name", "N/A")
    type_name = info.get("type_localized_name", "")
    rarity = info.get("rarity_localized_name", "")
    img_url = info.get("img", "")
    rank = info.get("rank_num", "-")
    rank_change = info.get("rank_num_change", 0) or 0

    # Current state
    cur_price = info.get("buff_sell_price")
    cur_buy = info.get("buff_buy_price")
    day_rate = info.get("sell_price_rate_1")
    day_amt = info.get("sell_price_1")

    # Ranking
    rank_str = f"#{rank}" if rank else "-"
    rank_delta = ""
    if rank_change and rank_change > 0:
        rank_delta = f' <span style="color:#e74c3c;">↑{rank_change}</span>'
    elif rank_change and rank_change < 0:
        rank_delta = f' <span style="color:#27ae60;">↓{abs(rank_change)}</span>'

    # Image
    img_tag = ""
    if img_url:
        img_tag = f'<img src="{img_url}" alt="{name}" style="width:64px;height:64px;border-radius:6px;margin-right:16px;float:left;">'

    # Platform comparison rows
    platforms = [
        ("BUFF", "buff"),
        ("悠悠有品", "yyyp"),
        ("Steam", "steam"),
        ("C5", "c5"),
        ("IGXE", "igxe"),
        ("ECO", "eco"),
    ]
    plat_rows = ""
    for plat_name, key in platforms:
        sell = fmt_price(info.get(f"{key}_sell_price"))
        buy = fmt_price(info.get(f"{key}_buy_price"))
        sell_num = fmt_vol(info.get(f"{key}_sell_num"))
        buy_num = fmt_vol(info.get(f"{key}_buy_num"))
        plat_rows += f"""
            <tr>
              <td>{plat_name}</td>
              <td class="price-col">{sell}</td>
              <td class="price-col">{buy}</td>
              <td>{sell_num}</td>
              <td>{buy_num}</td>
            </tr>"""

    # Price trend rows
    periods = [
        ("24h", "1"),
        ("7 天", "7"),
        ("15 天", "15"),
        ("30 天", "30"),
        ("90 天", "90"),
        ("180 天", "180"),
        ("365 天", "365"),
    ]
    trend_rows = ""
    for label, suffix in periods:
        amt = info.get(f"sell_price_{suffix}")
        rate = info.get(f"sell_price_rate_{suffix}")
        trend_rows += f"""
            <tr>
              <td>{label}</td>
              <td class="{cls(amt)}">{fmt_amt(amt)}</td>
              <td class="{cls(rate)}">{fmt_change(rate)}</td>
            </tr>"""

    # Build historical prices (current + change)
    hist_7 = cur_price - (info.get("sell_price_7") or 0) if cur_price is not None else None
    hist_30 = cur_price - (info.get("sell_price_30") or 0) if cur_price is not None else None
    hist_90 = cur_price - (info.get("sell_price_90") or 0) if cur_price is not None else None
    hist_365 = cur_price - (info.get("sell_price_365") or 0) if cur_price is not None else None

    # Conversion rates
    conv_rows = ""
    conv_pairs = [
        ("Steam→Buff 售价折价", "steam_buff_sell_conversion"),
        ("Steam→Buff 求购折价", "steam_buff_buy_conversion"),
        ("Buff→Steam 售价折价", "buff_steam_sell_conversion"),
        ("Buff→Steam 求购折价", "buff_steam_buy_conversion"),
    ]
    for clabel, ckey in conv_pairs:
        val = info.get(ckey)
        if val is not None:
            conv_rows += f"""
            <div class="info-item">
              <div class="label">{clabel}</div>
              <div class="value">{val}</div>
            </div>"""

    section = f"""
    <!-- {name} -->
    <div class="item-section">
      <div class="item-header">
        <table style="margin:0;width:100%;"><tr>
          <td style="width:80px;border:none;padding:0;">{img_tag}</td>
          <td style="border:none;padding:0;vertical-align:middle;">
            <div class="item-name">{name}</div>
            <div style="font-size:12px;color:#888;">{market_hash} · {type_name} · {rarity}</div>
            <div style="font-size:12px;color:#666;margin-top:2px;">排名 {rank_str}{rank_delta}</div>
          </td>
          <td style="border:none;text-align:right;vertical-align:middle;">
            <div style="font-size:22px;font-weight:700;color:#1a1a2e;">{fmt_price(cur_price)}</div>
            <div class="{cls(day_rate)}" style="font-size:14px;font-weight:600;">{fmt_change(day_rate)}</div>
          </td>
        </tr></table>
      </div>

      <div class="item-body">
        <!-- Quick Stats -->
        <div class="price-grid">
          <div class="price-card">
            <div class="label">BUFF 售价</div>
            <div class="value">{fmt_price(cur_price)}</div>
          </div>
          <div class="price-card">
            <div class="label">BUFF 求购</div>
            <div class="value">{fmt_price(cur_buy)}</div>
          </div>
          <div class="price-card">
            <div class="label">BUFF 在售</div>
            <div class="value">{fmt_vol(info.get("buff_sell_num"))}</div>
          </div>
          <div class="price-card">
            <div class="label">24h 涨跌</div>
            <div class="value {cls(day_rate)}">{fmt_change(day_rate)}</div>
          </div>
        </div>

        <!-- Platform Comparison -->
        <div class="section-title">📊 平台对比</div>
        <table>
          <thead><tr><th>平台</th><th>售价</th><th>求购</th><th>在售数</th><th>求购数</th></tr></thead>
          <tbody>{plat_rows}</tbody>
        </table>

        <!-- Price Trend -->
        <div class="section-title">📈 价格趋势（相对当前）</div>
        <table>
          <thead><tr><th>周期</th><th>涨跌金额</th><th>涨跌幅</th><th>周期</th><th>涨跌金额</th><th>涨跌幅</th></tr></thead>
          <tbody>
            <tr>
              <td>24h</td>
              <td class="{cls(day_amt)}">{fmt_amt(day_amt)}</td>
              <td class="{cls(day_rate)}">{fmt_change(day_rate)}</td>
              <td>7 天</td>
              <td class="{cls(info.get('sell_price_7'))}">{fmt_amt(info.get('sell_price_7'))}</td>
              <td class="{cls(info.get('sell_price_rate_7'))}">{fmt_change(info.get('sell_price_rate_7'))}</td>
            </tr>
            <tr>
              <td>15 天</td>
              <td class="{cls(info.get('sell_price_15'))}">{fmt_amt(info.get('sell_price_15'))}</td>
              <td class="{cls(info.get('sell_price_rate_15'))}">{fmt_change(info.get('sell_price_rate_15'))}</td>
              <td>30 天</td>
              <td class="{cls(info.get('sell_price_30'))}">{fmt_amt(info.get('sell_price_30'))}</td>
              <td class="{cls(info.get('sell_price_rate_30'))}">{fmt_change(info.get('sell_price_rate_30'))}</td>
            </tr>
            <tr>
              <td>90 天</td>
              <td class="{cls(info.get('sell_price_90'))}">{fmt_amt(info.get('sell_price_90'))}</td>
              <td class="{cls(info.get('sell_price_rate_90'))}">{fmt_change(info.get('sell_price_rate_90'))}</td>
              <td>180 天</td>
              <td class="{cls(info.get('sell_price_180'))}">{fmt_amt(info.get('sell_price_180'))}</td>
              <td class="{cls(info.get('sell_price_rate_180'))}">{fmt_change(info.get('sell_price_rate_180'))}</td>
            </tr>
            <tr>
              <td>365 天</td>
              <td class="{cls(info.get('sell_price_365'))}">{fmt_amt(info.get('sell_price_365'))}</td>
              <td class="{cls(info.get('sell_price_rate_365'))}">{fmt_change(info.get('sell_price_rate_365'))}</td>
              <td></td><td></td><td></td>
            </tr>
          </tbody>
        </table>

        <!-- Historical Prices -->
        <div class="section-title">📅 历史价格估算</div>
        <div class="price-grid" style="grid-template-columns: 1fr 1fr 1fr 1fr 1fr;">
          <div class="price-card">
            <div class="label">当前</div>
            <div class="value">{fmt_price(cur_price)}</div>
          </div>
          <div class="price-card">
            <div class="label">7 天前</div>
            <div class="value">{fmt_price(hist_7)}</div>
          </div>
          <div class="price-card">
            <div class="label">30 天前</div>
            <div class="value">{fmt_price(hist_30)}</div>
          </div>
          <div class="price-card">
            <div class="label">90 天前</div>
            <div class="value">{fmt_price(hist_90)}</div>
          </div>
          <div class="price-card">
            <div class="label">365 天前</div>
            <div class="value">{fmt_price(hist_365)}</div>
          </div>
        </div>

        <!-- Steam/Buff Conversion -->
        <div class="section-title">🔄 Steam ↔ Buff 折价率</div>
        <div class="info-grid">{conv_rows}</div>

      </div>
    </div>
    """
    return section


def generate_summary_table(all_data):
    """Generate a quick overview table of all items."""
    rows = ""
    for data in all_data:
        info = data.get("goods_info", {})
        goods_id = data.get("goods_id", "-")
        name = info.get("name", "N/A")
        price = fmt_price(info.get("buff_sell_price"))
        buy = fmt_price(info.get("buff_buy_price"))
        vol = fmt_vol(info.get("buff_sell_num"))
        rate = info.get("sell_price_rate_1")
        rank = info.get("rank_num", "-")

        img = info.get("img", "")
        img_tag = f'<img src="{img}" style="width:32px;height:32px;vertical-align:middle;margin-right:6px;border-radius:4px;">' if img else ""

        rows += f"""
            <tr>
              <td style="text-align:center;">{goods_id}</td>
              <td>{img_tag} {name}</td>
              <td class="price-col">{price}</td>
              <td class="price-col">{buy}</td>
              <td class="{cls(rate)}">{fmt_change(rate)}</td>
              <td style="text-align:center;">{vol}</td>
              <td style="text-align:center;">#{rank}</td>
            </tr>"""

    return f"""
    <div class="summary-section">
      <div class="section-title">📋 概览</div>
      <table>
        <thead>
          <tr><th style="width:50px;">ID</th><th>名称</th><th>售价</th><th>求购</th><th>24h 涨跌</th><th>在售数</th><th>排名</th></tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    """


def generate_html(all_data):
    """Generate full combined HTML email."""
    bj_time = datetime.now(TZ_BEIJING).strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now(TZ_BEIJING).strftime("%Y-%m-%d")

    item_count = len(all_data)

    item_sections = ""
    for data in all_data:
        item_sections += generate_item_section(data)

    summary_table = generate_summary_table(all_data)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{ font-family: 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 0; color: #333; }}
  .container {{ max-width: 720px; margin: 20px auto; background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden; }}
  .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); color: #fff; padding: 28px 32px; text-align: center; }}
  .header h1 {{ margin: 0 0 6px 0; font-size: 22px; font-weight: 700; }}
  .header .subtitle {{ font-size: 13px; opacity: 0.85; }}
  .body {{ padding: 20px 28px; }}
  .summary-section {{ margin-bottom: 20px; }}
  .item-section {{ border: 1px solid #e8ecf1; border-radius: 10px; margin-bottom: 20px; overflow: hidden; }}
  .item-header {{ background: #f8f9fb; padding: 14px 18px; border-bottom: 1px solid #e8ecf1; }}
  .item-name {{ font-size: 17px; font-weight: 700; color: #1a1a2e; }}
  .item-body {{ padding: 16px 18px; }}
  .price-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 10px; margin-bottom: 14px; }}
  .price-card {{ background: #f8f9fb; border-radius: 8px; padding: 10px 14px; text-align: center; }}
  .price-card .label {{ font-size: 11px; color: #888; margin-bottom: 4px; }}
  .price-card .value {{ font-size: 16px; font-weight: 700; color: #1a1a2e; }}
  .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }}
  .info-item {{ background: #f8f9fb; border-radius: 8px; padding: 10px 14px; }}
  .info-item .label {{ font-size: 11px; color: #888; margin-bottom: 2px; }}
  .info-item .value {{ font-size: 15px; font-weight: 600; color: #1a1a2e; }}
  .section-title {{ font-size: 15px; font-weight: 700; color: #1a1a2e; margin: 18px 0 10px 0; padding-bottom: 6px; border-bottom: 2px solid #0f3460; }}
  table {{ width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 13px; }}
  th {{ background: #1a1a2e; color: #fff; padding: 8px 10px; text-align: left; font-weight: 600; }}
  th:first-child {{ border-radius: 6px 0 0 0; }}
  th:last-child {{ border-radius: 0 6px 0 0; }}
  td {{ padding: 8px 10px; border-bottom: 1px solid #eef0f4; }}
  tr:hover td {{ background: #f8f9fb; }}
  .up {{ color: #e74c3c; font-weight: 600; }}
  .down {{ color: #27ae60; font-weight: 600; }}
  .neutral {{ color: #888; }}
  .price-col {{ font-family: 'Consolas', 'Courier New', monospace; }}
  .footer {{ background: #f8f9fb; padding: 16px 28px; text-align: center; font-size: 11px; color: #aaa; }}
  .footer a {{ color: #0f3460; text-decoration: none; }}
  @media (max-width: 600px) {{
    .price-grid {{ grid-template-columns: 1fr 1fr; }}
    .body {{ padding: 12px 14px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📊 CSQAQ 行情日报</h1>
    <div class="subtitle">{date_str} · {item_count} 件物品 · 北京时间 {bj_time}</div>
  </div>
  <div class="body">
    {summary_table}
    {item_sections}
  </div>
  <div class="footer">
    数据来源：<a href="https://csqaq.com">CSQAQ.com</a> · 自动生成于 {bj_time} · 仅供参考
  </div>
</div>
</body>
</html>"""
    return html


def send_email(html_content, subject):
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
    msg["From"] = formataddr(("CSQAQ日报", sender_email))
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    print(f"Sending email to {recipient_email} via {smtp_server}:{smtp_port}...")

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
        print("Email sent successfully!")
    except smtplib.SMTPAuthenticationError:
        print("ERROR: SMTP authentication failed.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR sending email: {e}")
        sys.exit(1)


def main():
    print(f"Loading data from {DATA_DIR}...")
    all_data = load_all_data()
    print(f"Found {len(all_data)} goods data files")

    item_names = [d.get("goods_info", {}).get("name", "?") for d in all_data]
    date_str = datetime.now(TZ_BEIJING).strftime("%Y-%m-%d")

    if len(all_data) <= 3:
        subject = f"📊 {'、'.join(item_names)} 行情 - {date_str}"
    else:
        subject = f"📊 CSQAQ 行情日报 - {date_str} ({len(all_data)}件)"

    print(f"Generating HTML email for: {', '.join(item_names)}")
    html = generate_html(all_data)

    send_email(html, subject)


if __name__ == "__main__":
    main()
