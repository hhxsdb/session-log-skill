---
description: 在当前工作目录维护中文 session-log.md，并用 /session-log 调用
argument-hint: init | update-ov | status | off
---

# /session-log

你正在执行 Claude Code 个人级自定义命令 `/session-log`。

## 目标

在**当前工作目录**维护一个中文 `session-log.md`，用于记录用户与助手的任务协作过程。

## 参数

- 动作：`$1`
- 原始参数：`$ARGUMENTS`

支持的动作：

- `init`
- `update-ov`
- `status`
- `off`

如果用户没有提供动作，先用中文简短提示可用写法：

- `/session-log init`
- `/session-log update-ov`
- `/session-log status`
- `/session-log off`

## 工作规则

### 通用规则

- 所有面向用户的说明默认使用简体中文
- 日志文件固定为当前工作目录下的 `session-log.md`
- 日志内容应尽量保持 UTF-8 中文可读，避免乱码
- 不记录密码、token、cookie、密钥等敏感信息；如有必要，仅做脱敏摘要

### 推荐工具

优先使用下面的 helper 脚本：

- `python C:\Users\ZNT\.claude\commands\lib\session_log.py init --cwd "<当前工作目录>"`
- `python C:\Users\ZNT\.claude\commands\lib\session_log.py status --cwd "<当前工作目录>"`
- `python C:\Users\ZNT\.claude\commands\lib\session_log.py update-overview --cwd "<当前工作目录>" --status in-progress --phase-code testing`

如果需要追加正文记录，可直接编辑 `session-log.md`，也可按需使用 helper 脚本的 `append-entry` 子命令。

## 动作定义

### 1. `init`

执行步骤：

1. 用 helper 脚本初始化当前目录的 `session-log.md`
2. 如果文件已存在，不覆盖历史内容
3. 告诉用户初始化结果
4. 从当前会话开始，将“记录模式”视为**已开启**

记录模式开启后：

- 对后续**任务相关、能推动问题解决**的对话，自动追加简洁结构化正文记录
- 不记录纯闲聊、寒暄、单句确认、无推进价值的内容
- 概览区不自动更新；只有用户执行 `/session-log update-ov` 或明确要求刷新概览时才更新

如果需要追加正文，请遵守以下结构：

```md
## YYYY-MM-DD HH:mm:ss

- 任务目标：
- 我让你做的事情：
- 你遇到的问题：
- 我给出的解决方式：
- 你的反馈：
- 实际最终解决方式：
- 当前状态：
- 遗留问题 / 下一步：
- 关键命令 / 报错 / 文件：
```

### 2. `update-ov`

执行步骤：

1. 读取当前会话上下文和现有 `session-log.md`
2. 基于当前整体进度，确定：
   - 当前状态：`进行中` / `已完成` / `阻塞中` / `部分完成`
   - 当前阶段：例如 `需求确认` / `实现中` / `测试中` / `已收尾`
3. 优先用 helper 脚本更新概览
4. 只更新概览，不单独追加正文，除非用户明确要求

如果 shell 传中文参数可能有编码风险，优先使用状态英文别名和阶段英文别名：

- 状态：`in-progress` / `completed` / `blocked` / `partial`
- 阶段：`requirements` / `implementing` / `testing` / `wrap-up`

### 3. `status`

执行步骤：

1. 用 helper 脚本检查当前目录 `session-log.md` 状态
2. 用中文向用户汇总：
   - 日志文件路径
   - 文件是否存在
   - 概览是否存在
   - 累计记录数
   - 创建时间
   - 最近更新时间
   - 当前状态
   - 当前阶段
3. 另外补一句：
   - 本会话记录模式是否开启，应根据当前会话上下文判断

### 4. `off`

执行步骤：

1. 告诉用户当前会话的自动记录模式已关闭
2. 从这一条之后，不再自动追加正文记录
3. 不自动修改 `session-log.md`，除非用户另行要求

## 文件结构约束

如果需要创建或修复 `session-log.md`，保持如下结构：

```md
# Session Log

<!-- SESSION_OVERVIEW_START -->
## 会话概览
- 创建时间：
- 最近更新时间：
- 当前项目目录：
- 当前状态：
- 当前阶段：
- 累计记录数：
<!-- SESSION_OVERVIEW_END -->

---

<!-- SESSION_ENTRIES_START -->
<!-- SESSION_ENTRIES_END -->
```

追加正文时，始终插入到 `<!-- SESSION_ENTRIES_END -->` 之前。

## 最终输出要求

- 输出简洁
- 默认中文
- 不重复展示冗长中间过程
- 如果动作无效，直接提示正确用法
