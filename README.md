# AI 技术洞察周报

每周一早上自动发送 AI 技术新闻周报到邮箱。

## 功能

- 多源采集：Hacker News、arXiv、RSS、NewsAPI
- Claude API 智能分类、去重、中文摘要
- 结构化 HTML 邮件，按分类组织
- GitHub Actions 每周一 9:00 (北京时间) 自动触发

## 使用方法

### 1. Fork 仓库

Fork 本仓库到你的 GitHub 账号下。

### 2. 配置 GitHub Secrets

在仓库 **Settings → Secrets and variables → Actions** 中添加：

| Secret | 说明 | 必填 |
|--------|------|------|
| `ANTHROPIC_API_KEY` | Claude API Key ([console.anthropic.com](https://console.anthropic.com)) | 是 |
| `SMTP_HOST` | SMTP 服务器地址 (QQ邮箱: `smtp.qq.com`) | 是 |
| `SMTP_PORT` | SMTP 端口 (QQ邮箱: `587`) | 是 |
| `SMTP_USER` | 发信邮箱地址 | 是 |
| `SMTP_PASSWORD` | SMTP 授权码 (不是邮箱密码) | 是 |
| `EMAIL_FROM` | 发信邮箱 (同 SMTP_USER) | 是 |
| `EMAIL_TO` | 收信邮箱 | 是 |
| `NEWSAPI_API_KEY` | NewsAPI Key (可选, [newsapi.org](https://newsapi.org)) | 否 |

### 3. 邮件发送配置 (推荐 SendGrid)

[SendGrid](https://sendgrid.com) 免费套餐 100 封/天，全球可访问：

1. 注册 [SendGrid](https://signup.sendgrid.com/) (免费)
2. 创建 API Key：**Settings → API Keys → Create API Key** (Full Access)
3. 验证发件地址：**Settings → Sender Authentication → Single Sender Verification**
4. 在 GitHub Secrets 中设置：

| Secret | 值 |
|--------|-----|
| `SMTP_HOST` | `smtp.sendgrid.net` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | `apikey`（固定值） |
| `SMTP_PASSWORD` | 上一步创建的 SendGrid API Key |
| `EMAIL_FROM` | 已验证的发件地址 |
| `EMAIL_TO` | 收件邮箱 |

### 4. 手动触发测试

进入 Actions 页面 → 选择 **AI Weekly Digest** → 点 **Run workflow** 立即运行一次。

### 5. 确认定时触发

workflow 已配置每周一 9:00 (北京时间) 自动运行。

## 本地运行

```bash
cp .env.example .env
# 编辑 .env 填入配置

pip install -r requirements.txt
python src/main.py
```

## 数据来源

- [Hacker News](https://news.ycombinator.com/) — 技术社区热门
- [arXiv](https://arxiv.org/) — AI/ML 论文预印本
- RSS Feeds — TechCrunch、Ars Technica、VentureBeat
- [NewsAPI](https://newsapi.org/) — 综合科技新闻 (可选)

## 自定义

编辑以下文件可调整行为：

- `src/sources/rss.py` — 增删 RSS 源
- `src/sources/arxiv.py` — 调整论文分类
- `src/email/template.py` — 修改邮件模板
- `src/config.py` — 调整采集参数
