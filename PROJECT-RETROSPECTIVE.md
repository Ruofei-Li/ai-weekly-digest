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
| 调度方式 | **GitHub Actions** | 免费，cron 定时触发，与代码仓库一体化 |
| LLM 引擎 | **Claude API** (通过 DeepSeek 代理) | 摘要/分类质量高 |
| 邮件发送 | **SMTP** | 通用协议，几乎支持所有邮箱 |

### 系统架构

当时画的架构图很清晰：

```
GitHub Actions（每周一 9:00 触发）
       │
       ▼
┌──────────────────────┐
│  1. 多渠道采集新闻     │  Hacker News + arXiv + RSS + NewsAPI
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  2. Claude API 精炼   │  去重、分类、摘要、中文化
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  3. 渲染 HTML 邮件    │  结构化排版
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│  4. SMTP 发送         │  → 邮箱
└──────────────────────┘
```

看起来完美无瑕。然而，真正的挑战在实现阶段才开始。

---

## 二、开发实现阶段

### 数据采集模块

设计了 4 个数据源：

- **Hacker News**：通过 Algolia API 搜索近期 AI 相关热门帖子，关键词覆盖 GPT、Claude、LLM、DeepSeek 等
- **arXiv**：拉取 cs.AI、cs.CL、cs.LG 等分类的最新论文
- **RSS**：订阅 TechCrunch AI、Ars Technica、VentureBeat 的 feeds
- **NewsAPI**（可选）：综合科技新闻聚合

每个源都是独立的采集器，用 try/catch 包裹——一个源挂了不影响其他。这一设计在后续运行中证明非常必要（有些 RSS 源偶尔会超时）。

### LLM 内容精炼

这是系统的核心。用 Claude API 把几十条原始新闻分类、去重、写成中文摘要。

第一版的 Prompt 简单直接：硬编码 6 个分类，每条一句话摘要。后来用户反馈了一轮迭代需求：

- 内容结构改为**两大板块**：AI 科技资讯 + AI 安全技术洞察
- 子专栏**动态显隐**：有内容就显示，没有就省略
- 每条资讯 **50-100 字**详细描述，包含技术细节和影响
- 安全板块的专栏名由 Claude **根据实际内容动态命名**

Prompt 工程是 LLM 应用中最值得花时间的环节。一个好的 Prompt 直接决定了输出质量。

## 三、那些踩过的坑

以下按痛苦程度排序。

---

### 坑一：邮件发送——最折腾的一环

原本以为最容易的部分，结果成了最折腾的。

**第一回合：QQ 邮箱 SMTP 本地测试通过**

本地 Mac 跑 `python src/main.py`，QQ 邮箱 SMTP 一条命令就发成功了，一切完美。

**第二回合：GitHub Actions 上运行时——Network is unreachable**

推到 GitHub 用 Actions 跑，结果报错 `[Errno 101] Network is unreachable`。原因很直接：GitHub Actions 的运行节点在美国，QQ 邮箱的 SMTP 服务器在国内，从海外 IP 直连会被网络层拦截。

**第三回合：阿里云邮件推送——配置太复杂**

想着用国内服务应该没问题，结果阿里云邮件推送需要购买/验证域名，还要配 DNS 记录。用户表示"太难搞了"。

**第四回合：SendGrid——国内注册被拦**

转向 SendGrid，免费套餐 100封/天，全球可访问。结果用户注册时提示 "You are not authorized to access this account"——注册被墙了。

**最终方案：Mac 本地 launchd 定时任务**

放弃在 GitHub Actions 上发邮件的想法，改为 Mac 本机定时任务：

- 用 macOS 自带的 `launchd` 替代 cron
- **每 5 分钟检查一次**：周一 + 9点后 + 今天还没发过？
- 满足条件就执行周报，写锁文件，当天不再重复
- Mac 在休眠？没关系，唤醒后 5 分钟内自动补发

这个方案的好处是：零第三方依赖、本地网络通畅、QQ 邮箱 SMTP 完全正常。

> **教训**：GitHub Actions 虽然是优秀的 CI/CD 工具，但涉及网络请求到特定区域的服务时（特别是中国国内的服务），网络连通性是要提前考虑的约束条件。

---

### 坑二：Python 模块命名冲突

一个低级但隐蔽的错误。

项目结构里有一个 `src/email/` 目录，里面放的是邮件发送和模板模块。当 `python src/main.py` 运行时，Python 会自动把 `src/` 加入 `sys.path`。于是 `import email` 时，Python 优先找到了项目里的 `src/email/`，而不是标准库的 `email` 模块。

结果在 `sender.py` 里 `from email.mime.text import MIMEText` 时，Python 在 `src/email/` 下找 `mime/text`，找不到，报错：

```
ModuleNotFoundError: No module named 'email.errors'
```

**修复**：把 `src/email/` 重命名为 `src/mailer/`。

> **教训**：项目内部的包名不要和 Python 标准库重名。`email`、`json`、`os`、`sys` 这些常见标准库模块名都应该避让。

---

### 坑三：Python 3.9 vs 3.11 语法兼容

本地 Mac 是 Python 3.9，GitHub Actions 配的是 3.11。在代码里用了 Python 3.10+ 才支持的 `X | None` 联合类型语法（如 `datetime | None`），本地一跑就报错：

```
TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'
```

逐个文件加 `from __future__ import annotations` 修复。

> **教训**：开发环境和运行环境的 Python 版本不一致时，要么统一版本，要么用兼容写法。`from __future__ import annotations` 是新版类型注解向后兼容的好工具。

---

### 坑四：Claude API 代理适配

用户用的是 DeepSeek 提供的 Claude API 代理接口（`api.deepseek.com/anthropic`），不是 Anthropic 官方的 `api.anthropic.com`。

Anthropic Python SDK 默认连官方 endpoint，传 DeepSeek 的 API key 过去自然 401 认证失败。

**修复**：配置 `ANTHROPIC_BASE_URL` 环境变量，在初始化 `Anthropic()` 客户端时传入 `base_url` 参数。

```python
client_kwargs = {"api_key": config.anthropic_api_key}
if config.anthropic_base_url:
    client_kwargs["base_url"] = config.anthropic_base_url
client = Anthropic(**client_kwargs)
```

> **教训**：API 代理/网关是国内的常见用法，代码里要预留自定义 endpoint 的能力。

---

### 坑五：LLM 输出 JSON 解析失败

当 Prompt 要求生成结构复杂的 JSON 时，Claude 偶尔会在数组或对象的末尾多打一个逗号（trailing comma），Python 的 `json.loads()` 直接报错。

幸好这个问题在 LLM 应用中很常见，加一行正则修复：

```python
text = re.sub(r",\s*([\]}])", r"\1", text)
```

同时把 `max_tokens` 从 4096 提升到 8192，因为 50-100 字的详细描述比一句话摘要长得多，token 不够会导致截断和 JSON 损坏。

> **教训**：LLM 输出的 JSON 永远要假设可能带尾逗号，做好容错。同时 max_tokens 要根据实际内容量合理设置。

---

### 坑六：企业邮件客户端 CSS 兼容性

这可能是最隐形的坑。

代码生成的 HTML 在浏览器里预览完美无缺——微软雅黑字体、蓝色/深青色板块标题、渐变色背景。但用户收到的邮件里：**字体是宋体，颜色没变，板块没区分**。

原因：华为企业邮箱（以及很多国内企业邮箱）会过滤或覆盖内联 CSS 样式。

最终找到一个能生效的写法组合：

- 用 `bgcolor` HTML 属性代替 CSS `background` 设背景色
- 用 `<font face="Microsoft YaHei">` 标签强制指定字体
- 每个 `<td>`、`<a>`、`<span>` 都显式设置 `font-family`
- 字号用 `pt` 单位（`16pt` 对应三号字）
- 避免使用 CSS 渐变色（`linear-gradient`）

同时邮件宽度也经过几轮迭代：660px → 700px → 860px → 1290px，最终用户满意。

> **教训**：做邮件模板和做网页是完全不同的技能树。邮件 HTML 要用 2000 年代的写法——表格布局、`bgcolor`、`<font>` 标签。接受这个现实能省很多时间。

---

## 四、最终交付物

| 维度 | 详情 |
|------|------|
| **代码仓库** | GitHub 开源托管 |
| **数据源** | Hacker News、arXiv、RSS、NewsAPI（可选） |
| **内容引擎** | Claude API（通过 DeepSeek 代理） |
| **排版** | 微软雅黑 16pt（三号字），邮件宽 1290px |
| **内容结构** | 两大板块：AI 科技资讯（4 个子专栏）+ AI 安全技术洞察（动态子专栏） |
| **发送方式** | Mac 本地 launchd 定时任务，每 5 分钟轮询，周一 9 点后唤醒即发 |
| **项目结构** | 17 个文件，约 700 行 Python |

当前项目目录：

```
ai-weekly-digest/
├── .github/workflows/weekly-digest.yml   # GitHub Actions（用于采集+精炼流程验证）
├── src/
│   ├── main.py                            # 主入口
│   ├── config.py                          # 配置
│   ├── sources/                           # 数据采集
│   │   ├── hackernews.py
│   │   ├── arxiv.py
│   │   ├── rss.py
│   │   └── newsapi.py
│   ├── llm/claude.py                      # Claude API 精炼
│   └── mailer/                            # 邮件模块
│       ├── template.py                    # HTML 模板
│       └── sender.py                      # SMTP 发送
├── run-digest.sh                          # launchd 定时脚本
├── .env.example
└── README.md
```

---

## 五、一些感悟

1. **自动化≠上云**。一开始想全部在 GitHub Actions 上跑，觉得高大上又免费。但遇到国内网络问题后，最终方案是本地 launchd —— 简单、可靠、零依赖。有时候"笨办法"才是最好的办法。

2. **LLM 应用的瓶颈在 prompt**。这个项目的核心引擎是 Claude，所有输出质量都取决于 prompt 怎么写。迭代了好几个版本才找到合适的指令粒度。

3. **邮件 HTML 是 2025 年的 IE6**。如果你做过邮件模板，你一定懂我在说什么。

4. **产品形态要在迭代中找**。最初只是 6 个固定分类+一句话摘要，经过几轮用户反馈才演变成两大板块+50字详细描述+动态专栏。需求在干的过程中才会变清晰。

5. **小项目也要重视工程规范**。虽然只是个几百行的脚本项目，但目录结构、配置管理、错误处理、容错设计都值得用心做，否则踩坑的时候会很痛苦。
