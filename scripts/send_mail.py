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

fp = fmt_price
fv = fmt_vol
fc = fmt_change
fa = fmt_amt
cl = cls

def _unused(value):
    if value is None:
        return "neutral"
    if value > 0:
        return "up"
    elif value < 0:
        return "down"
    return "neutral"


def generate_item_section(data):
    i = data.get("goods_info", {})
    n = i.get("name", "N/A"); mh = i.get("market_hash_name", ""); tp = i.get("type_localized_name", "")
    rr = i.get("rarity_localized_name", ""); img = i.get("img", ""); rk = i.get("rank_num", "-")
    rc = i.get("rank_num_change", 0) or 0
    cp = i.get("buff_sell_price"); cb = i.get("buff_buy_price"); dr = i.get("sell_price_rate_1")
    rks = "#" + str(rk) if rk else "-"
    rd = ""
    if rc and rc > 0:
        rd = " <span class=\"up-text\">↑" + str(rc) + "</span>"
    elif rc and rc < 0:
        rd = " <span class=\"down-text\">↓" + str(abs(rc)) + "</span>"
    it = "<img src=\"" + img + "\" class=\"item-img\" alt=\"" + n + "\">" if img else ""
    plats = [("BUFF","buff"),("悠悠有品","yyyp"),("Steam","steam"),("C5","c5"),("IGXE","igxe"),("ECO","eco")]
    pcs = ""
    for pn, pk in plats:
        ps = fp(i.get(pk + "_sell_price")); pb = fp(i.get(pk + "_buy_price"))
        psn = fv(i.get(pk + "_sell_num")); pbn = fv(i.get(pk + "_buy_num"))
        pcs += "<div class=\"pcc\"><div class=\"pcn\">" + pn + "</div><div class=\"pcr\"><span>售 " + ps + "</span><span>购 " + pb + "</span></div><div class=\"pcr2\"><span>在售 " + psn + "</span><span>求购 " + pbn + "</span></div></div>"
    trs = ""
    for lb, sf in [("24h","1"),("7天","7"),("15天","15"),("30天","30"),("90天","90"),("180天","180"),("365天","365")]:
        am = i.get("sell_price_" + sf); rt = i.get("sell_price_rate_" + sf)
        trs += "<tr><td>" + lb + "</td><td class=\"" + cl(am) + "\">" + fa(am) + "</td><td class=\"" + cl(rt) + "\">" + fc(rt) + "</td></tr>"
    s = "<div class=\"is\">"
    s += "<div class=\"ih\"><div class=\"iht\">" + it + "<div><div class=\"ihn\">" + n + "</div><div class=\"ihs\">" + mh + " · " + tp + " · " + rr + " · 排名 " + rks + rd + "</div></div></div>"
    s += "<div class=\"ihp\"><div class=\"ihpv\">" + fp(cp) + "</div><div class=\"ihpc " + cl(dr) + "\">" + fc(dr) + "</div></div></div>"
    s += "<div class=\"ib\">"
    s += "<div class=\"pg\"><div class=\"pcd\"><span>BUFF 售价</span><strong>" + fp(cp) + "</strong></div><div class=\"pcd\"><span>BUFF 求购</span><strong>" + fp(cb) + "</strong></div><div class=\"pcd\"><span>在售数</span><strong>" + fv(i.get("buff_sell_num")) + "</strong></div><div class=\"pcd\"><span>24h 涨跌</span><strong class=\"" + cl(dr) + "\">" + fc(dr) + "</strong></div></div>"
    s += "<div class=\"st\">📊 平台对比</div><div class=\"pg2\">" + pcs + "</div>"
    s += "<div class=\"st\">📈 价格趋势</div><div class=\"tw\"><table class=\"tt\"><thead><tr><th>周期</th><th>涨跌金额</th><th>涨跌幅</th></tr></thead><tbody>" + trs + "</tbody></table></div>"
    s += "</div></div>"
    return s

def generate_summary_table(all_data):
    rows = ""
    for d in all_data:
        i = d.get("goods_info", {}); gid = d.get("goods_id", "-"); n = i.get("name", "N/A")
        pr = fp(i.get("buff_sell_price")); rt = i.get("sell_price_rate_1"); rk = i.get("rank_num", "-")
        img = i.get("img", ""); it = "<img src=\"" + img + "\" class=\"sum-img\">" if img else ""
        rows += "<tr><td>" + str(gid) + "</td><td>" + it + n + "</td><td class=\"pc\">" + pr + "</td><td class=\"" + cl(rt) + "\">" + fc(rt) + "</td><td>#" + str(rk) + "</td></tr>"
    return "<div class=\"st\">📋 概览</div><div class=\"tw\"><table class=\"sum\"><thead><tr><th>ID</th><th>名称</th><th>售价</th><th>24h</th><th>排名</th></tr></thead><tbody>" + rows + "</tbody></table></div>"

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
<meta name="x-apple-disable-message-reformatting">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body{{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:#f4f6f9;margin:0;padding:0;color:#333;-webkit-text-size-adjust:100%}}
  .c{{max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden}}
  .hd{{background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);color:#fff;padding:20px 16px;text-align:center}}
  .hd h1{{margin:0 0 2px;font-size:18px;font-weight:700}}
  .hd .sub{{font-size:11px;opacity:.85}}
  .bd{{padding:12px}}
  .st{{font-size:13px;font-weight:700;color:#1a1a2e;margin:12px 0 6px;padding-bottom:3px;border-bottom:2px solid #0f3460}}
  .tw{{overflow-x:auto;-webkit-overflow-scrolling:touch}}
  .tw table{{min-width:320px}}
  table{{width:100%;border-collapse:collapse;font-size:11px}}
  th{{background:#1a1a2e;color:#fff;padding:5px 6px;text-align:left;font-weight:600;white-space:nowrap}}
  td{{padding:5px 6px;border-bottom:1px solid #eef0f4}}
  .up{{color:#e74c3c;font-weight:600}} .down{{color:#27ae60;font-weight:600}} .neutral{{color:#888}}
  .up-text{{color:#e74c3c}} .down-text{{color:#27ae60}}
  .pc{{font-family:Consolas,monospace;white-space:nowrap}}
  .is{{border:1px solid #e8ecf1;border-radius:10px;margin-bottom:12px;overflow:hidden}}
  .ih{{background:#f8f9fb;padding:8px 12px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px}}
  .iht{{display:flex;align-items:center;gap:8px;min-width:0;flex:1}}
  .item-img{{width:40px;height:40px;border-radius:6px;flex-shrink:0}}
  .ihn{{font-size:14px;font-weight:700;color:#1a1a2e}}
  .ihs{{font-size:10px;color:#888;margin-top:1px}}
  .ihp{{text-align:right;flex-shrink:0}}
  .ihpv{{font-size:18px;font-weight:700;color:#1a1a2e}}
  .ihpc{{font-size:12px;font-weight:600}}
  .ib{{padding:10px 12px}}
  .pg{{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px;margin-bottom:8px}}
  .pcd{{background:#f8f9fb;border-radius:6px;padding:6px 8px;text-align:center}}
  .pcd span{{display:block;font-size:9px;color:#888;margin-bottom:2px}}
  .pcd strong{{font-size:13px;font-weight:700;color:#1a1a2e}}
  .pg2{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px}}
  .pcc{{background:#f8f9fb;border-radius:6px;padding:6px 8px}}
  .pcn{{font-size:10px;font-weight:600;color:#1a1a2e;margin-bottom:3px}}
  .pcr,.pcr2{{display:flex;justify-content:space-between;font-size:10px;color:#555}}
  .pcr span,.pcr2 span{{font-family:Consolas,monospace}}
  .tt{{font-size:11px}} .tt th,.tt td{{padding:4px 6px}}
  .sum th,.sum td{{padding:4px 6px;font-size:10px}}
  .sum-img{{width:20px;height:20px;vertical-align:middle;margin-right:3px;border-radius:2px}}
  .ft{{background:#f8f9fb;padding:10px 16px;text-align:center;font-size:10px;color:#aaa}}
  .ft a{{color:#0f3460;text-decoration:none}}
  @media(max-width:400px){{
    .pg{{grid-template-columns:1fr 1fr}} .pg2{{grid-template-columns:1fr 1fr}}
    .bd{{padding:8px}} .ih{{padding:6px 8px}} .ib{{padding:6px 8px}}
    .ihn{{font-size:13px}} .ihpv{{font-size:16px}}
  }}
</style>
</head>
<body>
<div class="c">
  <div class="hd">
    <h1>📊 CSQAQ 行情日报</h1>
    <div class="sub">{date_str} · {item_count} 件物品 · 北京时间 {bj_time}</div>
  </div>
  <div class="bd">
    {summary_table}
    {item_sections}
  </div>
  <div class="ft">
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
