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
            data = json.load(fh)
            results.append(data)
    return results


def format_price(value):
    if value is None:
        return "-"
    return f"¥{value:.2f}"


def format_volume(value):
    if value is None or value == 0:
        return "-"
    if value >= 10000:
        return f"{value/10000:.1f}万"
    return str(value)


def format_change(value):
    if value is None:
        return "-"
    if value > 0:
        return f"+{value:.2f}%"
    elif value < 0:
        return f"{value:.2f}%"
    return "0.00%"


def change_class(value):
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
    updated_at = info.get("updated_at", "")

    # Ranking
    rank_str = f"#{rank}" if rank else "-"
    rank_delta = ""
    if rank_change > 0:
        rank_delta = f' <span style="color:#e74c3c;">↑{rank_change}</span>'
    elif rank_change < 0:
        rank_delta = f' <span style="color:#27ae60;">↓{abs(rank_change)}</span>'

    # Image
    img_tag = ""
    if img_url:
        img_tag = f'<img src="{img_url}" alt="{name}" style="width:64px;height:64px;border-radius:6px;margin-right:16px;float:left;">'

    section = f"""
    <!-- {name} Section -->
    <div class="item-section">
      <div class="item-header">
        <table style="margin:0;width:100%;"><tr>
          <td style="width:80px;border:none;padding:0;">{img_tag}</td>
          <td style="border:none;padding:0;vertical-align:middle;">
            <div class="item-name">{name}</div>
            <div style="font-size:12px;color:#888;">{market_hash}</div>
            <div style="font-size:12px;color:#666;margin-top:4px;">
              {type_name} · {rarity} · 排名 {rank_str}{rank_delta}
            </div>
          </td>
          <td style="border:none;text-align:right;vertical-align:middle;">
            <div style="font-size:12px;color:#aaa;">数据更新</div>
            <div style="font-size:13px;color:#555;">{updated_at}</div>
          </td>
        </tr></table>
      </div>

      <div class="item-body">
        <!-- Price Overview -->
        <div class="price-grid">
          <div class="price-card">
            <div class="label">当前售价</div>
            <div class="value">{format_price(info.get("sell_price"))}</div>
          </div>
          <div class="price-card">
            <div class="label">当前求购</div>
            <div class="value">{format_price(info.get("buy_price"))}</div>
          </div>
          <div class="price-card">
            <div class="label">24h 成交量</div>
            <div class="value">{format_volume(info.get("day_sell_num"))}</div>
          </div>
          <div class="price-card">
            <div class="label">24h 涨跌</div>
            <div class="value {change_class(info.get("sell_price_rate"))}">{format_change(info.get("sell_price_rate"))}</div>
          </div>
        </div>

        <!-- Platform Comparison -->
        <div class="section-title">📊 平台对比</div>
        <table>
          <thead>
            <tr><th>平台</th><th>售价</th><th>求购</th><th>成交量</th><th>在售数</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>BUFF</td>
              <td>{format_price(info.get("buff_sell_price"))}</td>
              <td>{format_price(info.get("buff_buy_price"))}</td>
              <td>{format_volume(info.get("buff_day_sell_num"))}</td>
              <td>{info.get("buff_on_sale_num", "-")}</td>
            </tr>
            <tr>
              <td>Steam</td>
              <td>{format_price(info.get("steam_sell_price"))}</td>
              <td>{format_price(info.get("steam_buy_price"))}</td>
              <td>{format_volume(info.get("steam_day_sell_num") or info.get("steam_sell_num"))}</td>
              <td>{info.get("steam_on_sale_num", "-")}</td>
            </tr>
            <tr>
              <td>UUYP</td>
              <td>{format_price(info.get("uuyp_sell_price"))}</td>
              <td>{format_price(info.get("uuyp_buy_price"))}</td>
              <td>{format_volume(info.get("uuyp_day_sell_num"))}</td>
              <td>{info.get("uuyp_on_sale_num", "-")}</td>
            </tr>
            <tr>
              <td>C5</td>
              <td>{format_price(info.get("c5_sell_price"))}</td>
              <td>{format_price(info.get("c5_buy_price"))}</td>
              <td>{format_volume(info.get("c5_day_sell_num"))}</td>
              <td>{info.get("c5_on_sale_num", "-")}</td>
            </tr>
            <tr>
              <td>IGXE</td>
              <td>{format_price(info.get("igxe_sell_price"))}</td>
              <td>{format_price(info.get("igxe_buy_price"))}</td>
              <td>{format_volume(info.get("igxe_day_sell_num"))}</td>
              <td>{info.get("igxe_on_sale_num", "-")}</td>
            </tr>
            <tr>
              <td>YouPin</td>
              <td>{format_price(info.get("yp_sell_price"))}</td>
              <td>{format_price(info.get("yp_buy_price"))}</td>
              <td>{format_volume(info.get("yp_day_sell_num"))}</td>
              <td>{info.get("yp_on_sale_num", "-")}</td>
            </tr>
          </tbody>
        </table>

        <!-- Price Trend -->
        <div class="section-title">📈 价格趋势</div>
        <table>
          <thead>
            <tr><th>周期</th><th>售价</th><th>涨跌幅</th><th>周期</th><th>售价</th><th>涨跌幅</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>24h</td>
              <td class="{change_class(info.get("sell_price_rate"))}">{format_price(info.get("sell_price"))}</td>
              <td class="{change_class(info.get("sell_price_rate"))}">{format_change(info.get("sell_price_rate"))}</td>
              <td>7 天</td>
              <td class="{change_class(info.get("sell_price_7"))}">{format_price(info.get("sell_price_7"))}</td>
              <td class="{change_class(info.get("sell_price_rate_7"))}">{format_change(info.get("sell_price_rate_7"))}</td>
            </tr>
            <tr>
              <td>15 天</td>
              <td class="{change_class(info.get("sell_price_15"))}">{format_price(info.get("sell_price_15"))}</td>
              <td class="{change_class(info.get("sell_price_rate_15"))}">{format_change(info.get("sell_price_rate_15"))}</td>
              <td>30 天</td>
              <td class="{change_class(info.get("sell_price_30"))}">{format_price(info.get("sell_price_30"))}</td>
              <td class="{change_class(info.get("sell_price_rate_30"))}">{format_change(info.get("sell_price_rate_30"))}</td>
            </tr>
            <tr>
              <td>90 天</td>
              <td class="{change_class(info.get("sell_price_90"))}">{format_price(info.get("sell_price_90"))}</td>
              <td class="{change_class(info.get("sell_price_rate_90"))}">{format_change(info.get("sell_price_rate_90"))}</td>
              <td>180 天</td>
              <td class="{change_class(info.get("sell_price_180"))}">{format_price(info.get("sell_price_180"))}</td>
              <td class="{change_class(info.get("sell_price_rate_180"))}">{format_change(info.get("sell_price_rate_180"))}</td>
            </tr>
            <tr>
              <td>365 天</td>
              <td class="{change_class(info.get("sell_price_365"))}">{format_price(info.get("sell_price_365"))}</td>
              <td class="{change_class(info.get("sell_price_rate_365"))}">{format_change(info.get("sell_price_rate_365"))}</td>
              <td></td><td></td><td></td>
            </tr>
          </tbody>
        </table>
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
        sell_price = format_price(info.get("sell_price"))
        buy_price = format_price(info.get("buy_price"))
        day_vol = format_volume(info.get("day_sell_num"))
        rate = info.get("sell_price_rate")
        rank = info.get("rank_num", "-")

        rate_html = f'<span class="{change_class(rate)}">{format_change(rate)}</span>'
        img = info.get("img", "")
        img_tag = f'<img src="{img}" style="width:32px;height:32px;vertical-align:middle;margin-right:6px;border-radius:4px;">' if img else ""

        rows += f"""
            <tr>
              <td style="text-align:center;">{goods_id}</td>
              <td>{img_tag} {name}</td>
              <td class="price-col">{sell_price}</td>
              <td class="price-col">{buy_price}</td>
              <td class="{change_class(rate)}">{rate_html}</td>
              <td>{day_vol}</td>
              <td style="text-align:center;">#{rank}</td>
            </tr>"""

    return f"""
    <div class="summary-section">
      <div class="section-title">📋 概览</div>
      <table>
        <thead>
          <tr><th style="width:50px;">ID</th><th>名称</th><th>售价</th><th>求购</th><th>24h 涨跌</th><th>成交量</th><th>排名</th></tr>
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
    item_names = [d.get("goods_info", {}).get("name", "?") for d in all_data]

    # Build item sections
    item_sections = ""
    for data in all_data:
        item_sections += generate_item_section(data)

    # Build summary
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
        print("ERROR: SMTP authentication failed. Check QQ_EMAIL and QQ_AUTH_CODE.")
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

    subject = f"📊 CSQAQ 行情日报 - {date_str} ({len(all_data)}件)"
    if len(all_data) <= 3:
        subject = f"📊 {'、'.join(item_names)} 行情 - {date_str}"

    print(f"Generating HTML email for: {', '.join(item_names)}")
    html = generate_html(all_data)

    send_email(html, subject)


if __name__ == "__main__":
    main()
