# CSQAQ 多物品每日行情邮件报告

每天自动抓取 [CSQAQ.com](https://csqaq.com) 上指定物品的完整行情数据，通过 QQ 邮箱 SMTP 发送 HTML 格式的组合邮件日报。

## 功能

- 🕘 **定时抓取**：每天北京时间 9:00 自动执行
- 📦 **多物品支持**：可同时追踪多个物品，设置 `GOODS_IDS` 即可
- 📊 **完整数据**：价格、涨跌幅、成交量、各平台对比、排名变化、Steam 折价率
- 📧 **邮件推送**：精美 HTML 邮件（含概览表 + 逐物品详情），支持手机端自适应
- 🔒 **安全配置**：邮箱凭据和物品配置通过 GitHub Secrets 管理

## 邮件内容

每封日报包含：
- **概览表**：所有物品的售价、求购、涨跌、成交量、排名一目了然
- **逐物品详情**：平台对比表（Buff/Steam/UUYP/C5/IGXE/YouPin）、价格趋势表（24h~365天）

## 快速开始

### 1. 准备 QQ 邮箱授权码

登录 QQ 邮箱网页版 → **设置 → 账户 → POP3/SMTP 服务** → 开启服务 → 生成授权码

### 2. Fork 或推送代码到 GitHub

```bash
git clone https://github.com/snowmelt9696/CSQAQ-daily-report.git
cd CSQAQ-daily-report
# 修改后推送
git push
```

### 3. 配置 GitHub Secrets

在仓库页面 **Settings → Secrets and variables → Actions → New repository secret** 添加：

| Secret 名称 | 必填 | 说明 |
|---|---|---|
| `QQ_EMAIL` | ✅ | 你的 QQ 邮箱地址（如 `123456@qq.com`） |
| `QQ_AUTH_CODE` | ✅ | QQ 邮箱 SMTP 授权码 |
| `RECIPIENT_EMAIL` | ✅ | 接收日报的邮箱地址 |
| `GOODS_IDS` | ❌ | 要追踪的物品 ID，逗号分隔（如 `19521,12345`）。不设置则默认追踪 `19521`（千瓦武器箱） |

### 4. 如何找到物品 ID

在 [CSQAQ.com](https://csqaq.com) 上浏览任意物品，URL 末尾的数字就是 ID：
- `https://csqaq.com/goods/19521` → ID = `19521`
- `https://csqaq.com/goods/12345` → ID = `12345`

### 5. 手动触发测试

**Actions** → **CSQAQ Daily Report** → **Run workflow**

### 6. 自动运行

推送并配置 Secrets 后，工作流会在每天 **UTC 01:00（北京时间 09:00）** 自动执行。

## 项目结构

```
.
├── .github/workflows/daily-report.yml   # GitHub Actions 工作流
├── scripts/
│   ├── scrape.js                        # Playwright 多物品抓取脚本
│   └── send_mail.py                     # QQ 邮箱 SMTP 组合邮件发送
├── data/                                # 抓取结果（gitignore）
│   ├── goods_19521.json                 # 单个物品数据
│   └── manifest.json                    # 抓取清单
├── package.json                         # Node.js 依赖
├── requirements.txt                     # Python 依赖
└── README.md
```

## 本地运行

```bash
# 安装依赖
npm ci
npx playwright install chromium
pip install jinja2

# 抓取（默认 ID 19521，可通过环境变量修改）
$env:GOODS_IDS="19521,12345"; node scripts/scrape.js

# 发送邮件
$env:QQ_EMAIL="your@qq.com"; $env:QQ_AUTH_CODE="xxx"; $env:RECIPIENT_EMAIL="to@qq.com"; python scripts/send_mail.py
```

## 技术栈

- **[Playwright](https://playwright.dev/)**：启动 headless Chromium 绕过站点反爬保护
- **[GitHub Actions](https://github.com/features/actions)**：定时调度 + CI/CD 运行环境
- **QQ 邮箱 SMTP**：通过 SSL 发送邮件

## 许可证

MIT
