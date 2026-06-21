# CSQAQ 千瓦武器箱 每日行情邮件报告

每天自动抓取 [CSQAQ.com](https://csqaq.com/goods/19521) 上「千瓦武器箱 (Kilowatt Case)」的完整行情数据，通过 QQ 邮箱 SMTP 发送 HTML 格式的邮件日报。

## 功能

- 🕘 **定时抓取**：每天北京时间 9:00 自动执行
- 📊 **完整数据**：价格、涨跌幅、成交量、各平台对比、排名变化、Steam 折价率
- 📧 **邮件推送**：精美 HTML 邮件，支持手机端自适应
- 🔒 **安全配置**：邮箱凭据通过 GitHub Secrets 管理

## 邮件内容示例

| 数据项 | 说明 |
|---|---|
| 各平台价格对比 | Buff / 悠悠有品 / Steam / C5 / IGXE / ECO 的售价、求购价、成交量 |
| Buff 涨跌幅 | 1天~365天的涨跌金额和百分比 |
| 折价率 | Steam↔Buff 四方向折价 |
| 排名变化 | 当前排名及变化方向 |

## 项目结构

```
.
├── .github/workflows/daily-report.yml   # GitHub Actions 工作流
├── scripts/
│   ├── scrape.js                        # Playwright 抓取脚本
│   └── send_mail.py                     # QQ 邮箱 SMTP 发送脚本
├── package.json                         # Node.js 依赖
├── requirements.txt                     # Python 依赖
└── README.md
```

## 快速开始

### 1. 准备 QQ 邮箱授权码

登录 QQ 邮箱网页版 → **设置 → 账户 → POP3/SMTP 服务** → 开启服务 → 生成授权码

### 2. Fork 或推送代码到 GitHub

```bash
git init
git add -A
git commit -m "Init CSQAQ daily report"
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```

### 3. 配置 GitHub Secrets

在仓库页面 **Settings → Secrets and variables → Actions → New repository secret** 添加三个 Secret：

| Secret 名称 | 说明 |
|---|---|
| `QQ_EMAIL` | 你的 QQ 邮箱地址（如 `123456@qq.com`） |
| `QQ_AUTH_CODE` | QQ 邮箱 SMTP 授权码 |
| `RECIPIENT_EMAIL` | 接收日报的邮箱地址 |

### 4. 手动触发测试

**Actions** → **CSQAQ Daily Report** → **Run workflow**

### 5. 自动运行

推送并配置 Secrets 后，工作流会在每天 **UTC 01:00（北京时间 09:00）** 自动执行。

## 技术栈

- **[Playwright](https://playwright.dev/)**：启动 headless Chromium 绕过站点反爬保护
- **[GitHub Actions](https://github.com/features/actions)**：定时调度 + CI/CD 运行环境
- **QQ 邮箱 SMTP**：通过 SSL 发送邮件

## 许可证

MIT
