# Mac 定时任务方案：launchd 实现解读

## 为什么不用 cron？

Mac 虽然支持传统的 `cron`，但有 3 个硬伤：

| 问题 | cron | launchd |
|------|------|---------|
| **休眠错过** | 机器休眠时任务直接跳过 | 唤醒后会自动补执行 |
| **时区感知** | 默认 UTC，需手动处理 | 支持 `TZ` 环境变量 |
| **日志管理** | 无内置日志 | `StandardOutPath` / `StandardErrorPath` |

对于「每周一早上 9 点发邮件，但如果 Mac 在休眠就等唤醒后再发」这个需求，`launchd` 是 macOS 上的正确选择。

---

## 核心机制：每 5 分钟检查一次

我们最终的方案不是「9:00 整点触发」，而是**每 5 分钟检查一次条件**：

```
launchd 每 300 秒执行 run-digest.sh
                    │
                    ▼
         ┌─ 今天周一？ ──┬── 否 → 退出
         │              │
        是              │
         │              │
         ▼              │
       ┌─ 超过 9 点？ ──┤
       │               │
      是               │
       │               │
       ▼               │
     ┌─ 今天已执行？ ──┤
     │                │
    否                │
     │                │
     ▼                │
  执行周报 + 写锁文件    │
     │                │
     ▼                ▼
  完成，当天不再执行    退出
```

**关键设计**：锁文件机制保证一天只执行一次，即使脚本被多次触发。

---

## 组成部分

### 1. launchd 配置文件（plist）

路径：`~/Library/LaunchAgents/com.user.ai-weekly-digest.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- 任务唯一标识 -->
    <key>Label</key>
    <string>com.user.ai-weekly-digest</string>

    <!-- 要执行的脚本 -->
    <key>ProgramArguments</key>
    <array>
        <string>/Users/liruofei/code/ai-weekly-digest/run-digest.sh</string>
    </array>

    <!-- 每 300 秒（5 分钟）执行一次 -->
    <key>StartInterval</key>
    <integer>300</integer>

    <!-- 工作目录 -->
    <key>WorkingDirectory</key>
    <string>/Users/liruofei/code/ai-weekly-digest</string>

    <!-- 环境变量 -->
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>

    <!-- 日志输出 -->
    <key>StandardOutPath</key>
    <string>/tmp/ai-weekly-digest-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ai-weekly-digest-stderr.log</string>
</dict>
</plist>
```

**关键字段说明：**

| 字段 | 作用 |
|------|------|
| `Label` | 任务的唯一 ID，用于 `launchctl` 管理 |
| `ProgramArguments` | 要执行的命令（必须用绝对路径） |
| `StartInterval` | 定时间隔（秒），比 `StartCalendarInterval`（cron 式）更适合"间隔检查"场景 |
| `WorkingDirectory` | 执行脚本前 `cd` 到该目录 |
| `EnvironmentVariables` | 注入环境变量（比如 `PATH`，GUI 应用和 CLI 的 PATH 不一样） |
| `StandardOutPath` / `StandardErrorPath` | 标准输出和错误日志路径 |

### 2. 包装脚本（run-digest.sh）

路径：`~/code/ai-weekly-digest/run-digest.sh`

```bash
#!/bin/bash
set -e

LOCK_DIR="$HOME/.local/share/ai-weekly-digest"
LOCK_FILE="$LOCK_DIR/last_run.txt"
TODAY=$(TZ=Asia/Shanghai date +%Y-%m-%d)
HOUR=$(TZ=Asia/Shanghai date +%H)
WEEKDAY=$(TZ=Asia/Shanghai date +%u)

# 条件 1：只在周一执行
[ "$WEEKDAY" != "1" ] && exit 0

# 条件 2：9 点之前不执行
[ "$HOUR" -lt 9 ] && exit 0

# 条件 3：今天已经执行过就不重复
[ -f "$LOCK_FILE" ] && [ "$(cat "$LOCK_FILE")" = "$TODAY" ] && exit 0

# 执行主程序
mkdir -p "$LOCK_DIR"
cd "$(dirname "$0")"
python3 src/main.py

# 标记今日已执行
echo "$TODAY" > "$LOCK_FILE"
```

**三层过滤逻辑：**

```
第 1 层（星期）→ 第 2 层（时间）→ 第 3 层（锁文件）
  非周一 → 跳过       没到 9 点 → 跳过   今天已发过 → 跳过
```

### 3. 锁文件机制

位置：`~/.local/share/ai-weekly-digest/last_run.txt`

作用：记录最后一次成功执行的日期（格式 `2026-04-27`）。

每次执行前读取这个文件，如果日期和今天一致，说明今天已经发过，直接退出。

---

## 任务管理命令

```bash
# 加载任务（注册到 launchd）
launchctl load ~/Library/LaunchAgents/com.user.ai-weekly-digest.plist

# 卸载任务
launchctl unload ~/Library/LaunchAgents/com.user.ai-weekly-digest.plist

# 查看任务状态
launchctl list com.user.ai-weekly-digest

# 查看任务详细配置
launchctl print gui/$(id -u)/com.user.ai-weekly-digest

# 查看日志
cat /tmp/ai-weekly-digest-stdout.log    # 正常输出
cat /tmp/ai-weekly-digest-stderr.log    # 错误输出
```

`launchctl list` 输出格式说明：

```
PID    ExitCode   Label
-      0          com.user.ai-weekly-digest
```

- `PID` 为 `-`：任务当前不在运行（正常，因为 `KeepAlive=false`）
- `ExitCode` 为 `0`：上次退出正常

---

## 与 cron 的对比

| 特性 | cron | launchd |
|------|------|---------|
| 配置位置 | `/etc/crontab` 或 `crontab -e` | `~/Library/LaunchAgents/*.plist` |
| 配置格式 | 纯文本 5 字段 | XML plist |
| 加载方式 | 自动 | `launchctl load/unload` |
| 休眠处理 | 错过就错过 | 唤醒后补执行 |
| 日志管理 | 需手动 `>> /var/log/xxx` | 内置 stdout/stderr 重定向 |
| 环境变量 | 受限的 PATH | 可自定义 |
| 粒度 | 分钟级（最小 1 分钟） | 秒级（最小可设 10 秒） |
| 守护进程 | 无（依赖 crond） | 系统内置，更可靠 |

### 什么时候用 cron？

- 服务器上（Linux 没有 launchd）
- 任务对时间不敏感，错过无所谓
- 习惯传统 Unix 工具

### 什么时候用 launchd？

- **需要休眠唤醒后补执行** ← 这是本项目选择 launchd 的核心原因
- 需要更精细的时间控制（秒级）
- 需要完善的日志管理
- 开发 Mac 桌面应用辅助工具

---

## 为什么不继续用 GitHub Actions？

项目一开始用 GitHub Actions 做调度，数据采集和精炼都跑在上面。但因为：

- GitHub Actions 节点在美国，连不上国内 QQ 邮箱的 SMTP 服务器
- 尝试阿里云邮件推送（需域名验证，配置复杂）
- 尝试 SendGrid（国内注册被墙）

最终放弃云端方案，改为本地执行。本地 Mac 网络通畅，QQ 邮箱 SMTP 一条命令就发成功。

> 取舍：如果你在国内有云服务器，或者用国际邮件服务（SendGrid/Mailgun）+ 非中国邮箱，GitHub Actions 方案仍然成立。

---

## 关于 launchd 休眠唤醒行为

这是一个常见的误解。`launchd` 在 Mac 休眠时的行为：

- **`StartInterval` 模式**：计时器在休眠期间暂停。系统唤醒后，计时器从暂停位置续起。也就是说，如果间隔是 300 秒，休眠 2 小时后唤醒，launchd 会在**下次间隔到期时**（而不是立即）执行。
- **但因为我们是每 5 分钟检查一次**：即使休眠后计时器重置，最多也是等 5 分钟就能触发，用户基本无感知。

**实际测试结果**：合盖休眠 → 开盖 → 最长 5 分钟内 → 邮件自动发出。满足"唤醒后尽快发送"的需求。
