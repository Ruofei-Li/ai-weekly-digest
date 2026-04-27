# AI 技术洞察周报项目复盘：从想法到落地，那些踩过的坑

## 缘起

事情是这样的：我想做一个 AI 技术洞察的自动化工具。

需求看起来很明确——每周一早上，一封邮件自动飞到我的公司邮箱，告诉我过去一周 AI 圈发生了什么：谁发了新模型、哪家出了新功能、有什么值得关注的 AI 工具、企业之间有什么收购合作、AI 安全领域有什么新进展。

这事听起来不算复杂，但真正走下来，从需求设计到最终跑通，中间踩了不少坑。这篇文章就当是一次完整的项目复盘。

---

## 一、方案设计阶段

### 需求定义

最开始我跟 Claude 讨论了两条路线：

1. **让 Claude 做技术洞察，直接写邮件发给我**——但这有个硬伤：Claude 没有发送邮件的能力
2. **搭一个完整的自动化系统**——从数据采集到邮件发送全自动

最终选了后者。

进一步明确了几个关键决策：

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 技术栈 | **Python** | 生态丰富，AI/数据处理/邮件库齐全 |
| 调度方式 | **GitHub Actions**（最初）→ **Mac launchd**（最终） | 见后文的"坑" |
| LLM 引擎 | **Claude API**（通过 DeepSeek 代理） | 摘要/分类质量高 |
| 邮件发送 | **SMTP** | 通用协议，几乎支持所有邮箱 |

### 系统架构

最终的系统架构：

```
┌─ 数据采集层 ─────────────────────────────┐
│  Hacker News Algolia API                  │
│  arXiv API                                │  各自 try/catch
│  RSS Feeds (TechCrunch/Ars/VentureBeat)   │  互不影响
│  NewsAPI (可选)                           │
└────────────────────┬──────────────────────┘
                     ▼
┌─ LLM 精炼层 ──────────────────────────────┐
│  Claude API (DeepSeek 代理)                │
│  → 分类 / 去重 / 50-100字中文摘要          │
│  → 两大板块：科技资讯 + 安全洞察           │
│  → 子专栏动态显隐                          │
└────────────────────┬──────────────────────┘
                     ▼
┌─ 邮件渲染层 ──────────────────────────────┐
│  结构化 HTML 模板                          │
│  微软雅黑 16pt / 1290px 宽                │
│  bgcolor + <font face> 兼容企业邮箱        │
└────────────────────┬──────────────────────┘
                     ▼
┌─ 发送层 ──────────────────────────────────┐
│  SMTP (QQ邮箱)                            │
│  → your_email@company.com                 │
└───────────────────────────────────────────┘
                     ▲
┌─ 调度层 ──────────────────────────────────┐
│  Mac launchd：每 5 分钟轮询                │
│  run-digest.sh：三层过滤（周一/9点/锁）    │
│  唤醒后自动补执行                          │
└───────────────────────────────────────────┘
```

---

## 二、开发实现阶段

### 数据采集模块

设计了 4 个数据源，全部免费/免 API Key（NewsAPI 除外）：

- **Hacker News**：通过 Algolia API 搜索近期 AI 相关热门帖子。做了两段查询——关键词精准匹配 + 高分文章兜底，避免漏掉不带明确 AI 关键词但实质相关的内容。
- **arXiv**：拉取 cs.AI、cs.CL、cs.LG、cs.CV 等分类的最新论文预印本，用 feedparser 解析 Atom XML。
- **RSS**：订阅 TechCrunch AI、Ars Technica、VentureBeat 三个科技媒体的 feeds。
- **NewsAPI**（可选）：综合科技新闻聚合，需要 API Key。

**关键设计**：每个源都是独立的采集器，用 `try/catch` 包裹——一个源挂了不影响其他。这一设计在后续运行中证明非常必要（网络波动、API 限流、RSS 超时等偶发问题是家常便饭）。

### LLM 内容精炼

这是系统的核心。用 Claude API 把 60 条原始新闻分类、去重、写成中文摘要。

第一版的 Prompt 是扁平结构：硬编码 6 个分类，每条一句话摘要。后来经过用户反馈迭代：

1. **结构升级**：改为两大板块——"AI 科技资讯"和"AI 安全技术洞察"
2. **动态专栏**：子专栏按实际情况动态显隐，安全板块的专栏名由 Claude 根据内容自主命名
3. **详细描述**：每条资讯从一句话（~20字）升级到 50-100 字，包含具体技术细节和影响
4. **JSON 格式**：输出 `sections → columns → items` 三层嵌套结构

**Prompt 工程的要点**：Claude 对 JSON 格式的跟随能力很强，但偶尔会输出尾逗号。所以在解析端做了容错处理。

---

## 三、那些踩过的坑

以下按痛苦程度排序。

---

### 坑一：邮件发送——最折腾的一环

原本以为最容易的部分，结果成了最折腾的。

**第一回合：QQ 邮箱 SMTP 本地测试通过**

本地 Mac 跑 `python src/main.py`，QQ 邮箱 SMTP 用授权码认证，一条命令就发成功了，过程 3 秒。

**第二回合：GitHub Actions 上运行时——Network is unreachable**

推到 GitHub 用 Actions 跑，结果报错：

```
OSError: [Errno 101] Network is unreachable
```

原因很直接：GitHub Actions 的运行节点在美国，QQ 邮箱的 SMTP 服务器在国内，从海外 IP 直连会被网络层拦截。这不是代码问题，是网络问题——改代码也没用。

**第三回合：阿里云邮件推送——配置太复杂**

想着用国内服务应该没问题。结果阿里云邮件推送需要购买/验证域名、配 DNS 的 TXT 记录、等待域名审核……用户评估后放弃。

**第四回合：SendGrid——国内注册被拦**

转向 SendGrid，免费套餐 100 封/天、API 文档齐全、全球可访问。结果用户注册时提示：

```
You are not authorized to access this account.
Please contact your administrator or support for help.
```

注册入口被墙了。

**最终方案：Mac 本地 launchd 定时任务**

放弃在 GitHub Actions 上发邮件的想法，改为 Mac 本机定时任务。这个方案的好处是：零第三方依赖、本地网络通畅、QQ 邮箱 SMTP 完全正常。

#### launchd 实现方案详解

**为什么不用 cron？**

Mac 虽然支持传统的 `cron`，但有 3 个硬伤：

| 问题 | cron | launchd |
|------|------|---------|
| 休眠错过 | 机器休眠时任务直接跳过 | 唤醒后会自动补执行 |
| 时区感知 | 默认 UTC，需手动处理 | 支持 `TZ` 环境变量 |
| 日志管理 | 无内置日志 | `StandardOutPath` / `StandardErrorPath` |

对于"如果 Mac 在休眠就等唤醒后再发"这个需求，`launchd` 是正确的选择。

**核心机制：每 5 分钟检查一次**

不是 9:00 整点触发，而是让 launchd 每 300 秒执行一次包装脚本，脚本里做条件过滤：

```
launchd 每 300 秒 → run-digest.sh
                         │
              ┌─ 今天周一？ ──┬── 否 → exit 0
              │              │
              ▼              │
           ┌─ ≥ 9点？ ──────┤
           │                │
           ▼                │
        ┌─ 今天已发过？ ────┤
        │                   │
        ▼                   │
     执行周报 + 写入锁文件    │
        │                   │
        ▼                   ▼
     当天不再执行           跳过
```

**三层过滤逻辑：**

```
第 1 层（星期）→ 第 2 层（时间）→ 第 3 层（锁文件）
  非周一 → 跳过      没到 9 点 → 跳过   今天已发过 → 跳过
```

**锁文件机制：**

位置 `~/.local/share/ai-weekly-digest/last_run.txt`，只存一行日期（如 `2026-04-27`）。每次执行前读取，如果日期和今天一致就跳过。脚本执行成功后写入当天日期。

**launchd plist 配置：**

```xml
<key>StartInterval</key>
<integer>300</integer>
<key>WorkingDirectory</key>
<string>/Users/your_name/code/ai-weekly-digest</string>
<key>StandardOutPath</key>
<string>/tmp/ai-weekly-digest-stdout.log</string>
<key>StandardErrorPath</key>
<string>/tmp/ai-weekly-digest-stderr.log</string>
```

**关于休眠唤醒的实际行为：**

`launchd` 的 `StartInterval` 计时器在休眠期间暂停，系统唤醒后计时器继续。因为我们是每 5 分钟检查一次，最多等 5 分钟就能触发。实际测试：合盖休眠 → 开盖 → 最长 5 分钟内 → 邮件自动发出。

**管理命令：**

```bash
launchctl load   ~/Library/LaunchAgents/com.user.ai-weekly-digest.plist   # 加载
launchctl unload ~/Library/LaunchAgents/com.user.ai-weekly-digest.plist   # 卸载
launchctl list   com.user.ai-weekly-digest                                # 查看状态
cat /tmp/ai-weekly-digest-stdout.log                                      # 查看日志
```

> **教训**：GitHub Actions 虽然是优秀的 CI/CD 工具，但涉及网络请求到特定区域的服务时（特别是中国国内的服务），网络连通性是要提前考虑的约束条件。有时候"笨办法"（本地脚本）才是最好的办法。

---

### 坑二：Python 模块命名冲突

一个低级但隐蔽的错误。

项目结构里有一个 `src/email/` 目录，里面放的是邮件发送和模板模块。当 `python src/main.py` 运行时，Python 会自动把 `src/` 加入 `sys.path`。于是 `import email` 时，Python 优先找到了项目里的 `src/email/`，而不是标准库的 `email` 模块。

结果在 `sender.py` 里 `from email.mime.text import MIMEText` 时，解析链变成了 `src/email/mime/text`——找不到，报错：

```
ModuleNotFoundError: No module named 'email.errors'
```

**修复**：把 `src/email/` 重命名为 `src/mailer/`。

> **教训**：项目内部的包名不要和 Python 标准库重名。`email`、`json`、`os`、`sys`、`time` 这些常见标准库模块名都应该避让。

---

### 坑三：Python 3.9 vs 3.11 语法兼容

本地 Mac 是 Python 3.9，GitHub Actions 配的是 3.11。在代码里用了 Python 3.10+ 才支持的 `X | None` 联合类型语法（如 `datetime | None`），本地一跑就报错：

```
TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
```

逐个文件加 `from __future__ import annotations` 修复。同时 `list[X]`、`dict[K, V]` 这样的泛型语法也需要这行 import。

受影响文件：`hackernews.py`、`arxiv.py`、`rss.py`、`newsapi.py`

> **教训**：开发环境和运行环境的 Python 版本不一致时，要么统一版本（推荐），要么用兼容写法。`from __future__ import annotations` 是新版类型注解的"时间机器"。

---

### 坑四：Claude API 代理适配

用户用的是 DeepSeek 提供的 Claude API 代理接口（`api.deepseek.com/anthropic`），不是 Anthropic 官方的 `api.anthropic.com`。

Anthropic Python SDK 默认连官方 endpoint，传 DeepSeek 的 API key 过去自然 401 认证失败。

**修复**：配置 `ANTHROPIC_BASE_URL` 环境变量，在初始化 `Anthropic()` 客户端时传入 `base_url` 参数：

```python
client_kwargs = {"api_key": config.anthropic_api_key}
if config.anthropic_base_url:
    client_kwargs["base_url"] = config.anthropic_base_url
client = Anthropic(**client_kwargs)
```

同时需要在 GitHub Secrets 和本地 `.env` 中配置 `ANTHROPIC_BASE_URL`。

> **教训**：国内使用 API 代理/网关是常见操作，代码里要预留自定义 endpoint 的能力。不要把 API endpoint 硬编码。

---

### 坑五：LLM 输出 JSON 解析失败

当 Prompt 要求生成结构复杂的 JSON 时，Claude 偶尔会在数组或对象的末尾多打一个逗号（trailing comma），Python 的 `json.loads()` 直接抛异常。

后来还把 `max_tokens` 从 4096 提升到 8192，因为 50-100 字的详细描述比一句话摘要长得多，token 不够会导致内容被截断，截断后的 JSON 必然无法解析。

```python
# 去掉尾逗号
text = re.sub(r",\s*([\]}])", r"\1", text)
```

> **教训**：LLM 输出的 JSON 永远要假设可能带尾逗号或其他格式瑕疵，解析端做好容错。同时 `max_tokens` 要根据实际内容量合理设置，不能沿用默认值。

---

### 坑六：企业邮件客户端 CSS 兼容性

这可能是最隐形的坑。

代码生成的 HTML 在浏览器里预览完美无缺——微软雅黑字体、蓝色/深青色板块标题、渐变色背景。但用户收到的邮件里：**字体是宋体，颜色没变，板块没区分**。

原因：国内某企业邮箱（以及很多国内企业邮箱）会过滤或覆盖内联 CSS 样式。

**6.1 字体和颜色**

找到了一套能在企业邮箱生效的写法组合：

```html
<!-- ❌ 被过滤 -->
<td style="background:linear-gradient(135deg, #2b6cb0, #2c5282); font-family: Microsoft YaHei">

<!-- ✅ 能生效 -->
<td bgcolor="#2b6cb0" style="font-family: 'Microsoft YaHei', '微软雅黑', sans-serif">
    <font face="'Microsoft YaHei', '微软雅黑', sans-serif">文本</font>
</td>
```

关键点：
- 用 `bgcolor` HTML 属性代替 CSS `background` 设背景色
- 用 `<font face="Microsoft YaHei">` 标签强制指定字体
- 每个 `<td>`、`<a>`、`<p>` 都显式设置 `font-family`
- 字号用 `pt` 单位（`16pt` 对应三号字）
- 避免使用 CSS 渐变色（`linear-gradient`）

**6.2 宽度——一个参数改了 4 遍**

邮件宽度经历了 4 轮调整：

| 版本 | 宽度 | 结果 |
|------|------|------|
| 初始 | 660px | 用户说太窄 |
| V2 | 700px | 还是窄 |
| V3 | 860px | 好了点 |
| V4 | **1290px（1.5倍）** | 最终满意 |

**6.3 字号——从 14px 到 16pt**

用户要"三号字"（中文排版标准，16pt）。最初用的 14px，考虑到邮件客户端的渲染差异，最终改用 `16pt`，并且所有字号都从 px 换成了 pt。

> **教训**：做邮件模板和做网页是完全不同的技能树。邮件 HTML 要用 2000 年代的写法——表格布局、`bgcolor`、`<font>` 标签。接受这个现实能省很多时间。做之前先确认对方用什么邮箱客户端——决定了你能用到什么程度的 CSS。

---

## 四、代码结构深度解析

最终项目总 17 个文件、约 800 行 Python。以下是每个模块的详细分析：

### 项目全景

```
ai-weekly-digest/
├── .github/workflows/weekly-digest.yml    # CI
├── run-digest.sh                           # 调度脚本
├── .env.example                            # 配置模板
├── requirements.txt                        # 依赖
├── README.md                               # 使用文档
├── PROJECT-RETROSPECTIVE.md                # 本文
└── src/                                    # 核心代码
    ├── main.py                             # 工作流编排
    ├── config.py                           # 统一配置
    ├── sources/                            # 数据采集层
    ├── llm/                                # LLM 精炼层
    └── mailer/                             # 邮件发送层
```

### main.py——工作流编排

```python
def main():
    cfg = Config.from_env()                 # 1. 加载配置
    items = collect_news(cfg)               # 2. 采集新闻
    digest = refine(cfg, items)             # 3. Claude 精炼
    html = build_html(digest)               # 4. 渲染 HTML
    send(cfg, subject, html)                # 5. 发送邮件
```

这是全系统最简短也最重要的文件——它把 4 个模块串成一条流水线：**配置 → 采集 → 精炼 → 渲染 → 发送**。

每一步都有清晰的输入输出接口。如果未来要替换某个环节（比如把 Claude 换成其他 LLM），只需要改对应模块，main.py 不需要动。

### config.py——统一配置管理

从环境变量读取所有配置项，用 `dataclass` 封装。

```python
@dataclass
class Config:
    anthropic_api_key: str     # Claude API Key（必填）
    anthropic_base_url: str    # API 代理地址
    smtp_host: str             # SMTP 服务器
    smtp_port: int             # SMTP 端口
    smtp_user: str             # SMTP 用户名
    smtp_password: str         # SMTP 密码/授权码
    email_from: str            # 发件地址
    email_to: str              # 收件地址
    # ...

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            # ...
        )
```

**设计考量**：不用 YAML/JSON 配置文件，而是用环境变量 + `os.getenv()`。这样做的好处是：和 GitHub Secrets 天然对接，本地用 `.env` 文件（`python-dotenv` 加载），敏感信息不会被提交到仓库。

### sources/——数据采集层

每个采集器是一个独立文件，共享同一个 `NewsItem` 数据类：

```python
@dataclass
class NewsItem:
    title: str
    url: str
    description: str
    published_at: Optional[datetime]
    source_name: str
    category_hint: str           # 供 LLM 参考的预分类提示
```

**hackernews.py**

两个查询策略互备：
- **关键词搜索**：精准匹配 AI 关键词（GPT/Claude/LLM/DeepSeek 等），按相关性排序
- **高分文章兜底**：取本周 points > 50 的热门文章，去掉已收录的。用来捕获不带 AI 关键词但实际相关的帖子

**arxiv.py**

从 7 个分类（cs.AI、cs.CL、cs.LG、cs.CV、cs.MA、cs.RO、stat.ML）拉取最新论文。根据 arXiv 标签给 `category_hint` 赋值，帮助 LLM 做预分类。

**rss.py**

3 个科技媒体 RSS 源，用 `feedparser` 解析。每个 feed 独立 try/catch。

**newsapi.py**

可选的第 4 个源，需要 API Key。做了 URL 去重（同一个新闻可能被多个查询关键词搜到）。

### llm/claude.py——LLM 精炼层

这是"Prompt 即代码"的典范。核心逻辑不在 Python 代码里，而在 Prompt 指令中。

**Prompt 设计的演进：**

V1（初始版）：
```
6 个固定分类，每条一句话摘要 → JSON 输出
```

V2（迭代后）：
```
两大板块 + 子专栏动态显隐 + 50-100字描述 → 结构化 JSON
```

**关键配置项**：
- `max_tokens=8192`：比默认（4096）翻倍，因为输出内容更长
- JSON 后处理：去掉尾逗号、去掉代码块标记

**`_parse_json` 的实现**：

```python
def _parse_json(text: str) -> dict:
    text = text.strip()
    # 去掉 markdown 代码块标记
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    # 去掉尾逗号
    text = re.sub(r",\s*([\]}])", r"\1", text)
    return json.loads(text)
```

**为什么不从 SDK 获取结构化输出？**

Anthropic SDK 支持工具调用（tool use / function calling）获取结构化输出。但用 tool use 时模型输出会更结构化、但也更"机械"，影响摘要的自然度。权衡后选择了纯文本 Prompt + JSON string 的方案，可读性和灵活性更好。

### mailer/template.py——邮件渲染层

这是全项目迭代最多次数的文件（5 次重写）。

**文件结构**：

```python
def build_html(digest: dict) -> str:      # 入口：生成完整 HTML
def _build_section(section: dict) -> str:  # 渲染板块（蓝色/深青色）
def _build_column(col: dict, ...) -> str:  # 渲染子专栏
def _build_item(item: dict) -> str:        # 渲染单条资讯
```

这种函数的责任链结构让模板渲染逻辑清晰可维护。

**配色方案**：
- 概览线：`#4299e1`（亮蓝）
- AI 科技资讯板块头：`#2b6cb0`（深蓝），子专栏底色 `#ebf8ff`（浅蓝）
- AI 安全技术洞察板块头：`#285e61`（深青），子专栏底色 `#e6fffa`（浅青）
- 链接色：`#2b6cb0`（蓝），不加下划线，用 font-weight 区分

**企业邮箱兼容的写法**：全局不用 CSS 渐变色；背景色用 `bgcolor` 属性；字体用 `<font face>` 标签加双重兜底。

### mailer/sender.py——邮件发送层

```python
def send(config: Config, subject: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if config.smtp_port == 465:
        # SSL（阿里云、QQ邮箱 465 端口）
        with smtplib.SMTP_SSL(...) as server:
            server.login(...)
    else:
        # STARTTLS（587 端口）
        with smtplib.SMTP(...) as server:
            server.starttls()
            server.login(...)
    server.sendmail(...)
```

关键设计：支持 SSL（465）和 STARTTLS（587）两种模式。因为不同邮件服务商用的端口不同。QQ 邮箱 587（TLS），SendGrid 587（TLS），阿里云邮件推送 465（SSL）。

### run-digest.sh——本地调度脚本

launchd 的包装器，职责是"条件过滤 + 执行 + 写锁"。

**为什么用 shell 脚本而不是 Python？** shell 脚本启动更快（不用等 Python 解释器加载），条件判断更轻量。99% 的调用在前两层过滤就会 exit 0，完全不需要启动 Python。

---

## 五、最终交付物

| 维度 | 详情 |
|------|------|
| **代码仓库** | GitHub 开源托管 |
| **技术栈** | Python 3.9+ / 3.11+ |
| **数据源** | Hacker News、arXiv、RSS、NewsAPI（可选） |
| **内容引擎** | Claude API（通过 DeepSeek 代理） |
| **邮件排版** | 微软雅黑 16pt（三号字），邮件宽 1290px |
| **内容结构** | 两大板块（AI 科技资讯 + AI 安全技术洞察），子专栏动态显隐 |
| **调度方式** | Mac launchd 每 5 分钟轮询，周一 9 点后唤醒即发 |
| **项目规模** | 17 个文件，约 800 行 Python |

---

## 六、一些感悟

1. **自动化≠上云**。一开始想全部在 GitHub Actions 上跑，觉得高大上又免费。但遇到国内网络问题后，最终方案是本地 launchd —— 简单、可靠、零依赖。有时候"笨办法"才是最好的办法。

2. **LLM 应用的瓶颈在 prompt**。这个项目的核心引擎是 Claude，所有输出质量都取决于 prompt 怎么写。迭代了好几个版本才找到合适的指令粒度。代码逻辑反而是次要的。

3. **邮件 HTML 是 2025 年的 IE6**。如果你做过邮件模板，你一定懂我在说什么。`<font face="...">`、`bgcolor`、表格布局——2000 年代的技术栈在现代邮件中仍然最可靠。

4. **产品形态要在迭代中找**。最初只是 6 个固定分类 + 一句话摘要，经过几轮用户反馈才演变成两大板块 + 50 字详细描述 + 动态专栏。需求在干的过程中才会变清晰，不要试图一开始就设计完美。

5. **小项目也要重视容错设计**。多数据源各自 try/catch、LLM JSON 解析做容错、SMTP 支持两种端口模式——这几百行代码里至少有一半是用来处理异常情况的。软件工程的本质就是处理意料之外的事情。

6. **技术选型要考虑网络拓扑**。在选 GitHub Actions 之前，应该先确认目标服务（QQ 邮箱 SMTP）是否能从 GitHub 的海外 IP 访问到。国内的网络环境是一个需要认真对待的约束条件。
