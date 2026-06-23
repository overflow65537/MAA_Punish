---
name: maa-punish-log-analysis
description: 分析用户给出的本地日志目录或日志文件路径，结合 MAA_Punish（MaaFramework + Python 自定义 + MFW-cfa）仓库定位任务卡死、识别失败、Pipeline 与自定义逻辑问题。主日志为 gui.log（cfa 图形界面）、custom.log（Python/agent 自定义）、debug/maa.log（框架运行时）。不下载或解压 zip；在用户给出日志路径、贴日志片段、反馈 bug、排查识别或流水线问题时使用。
---

# MAA_Punish 本地日志分析

## 适用范围

- 仓库：`MAA_Punish`（战双帕弥什小助手，Python 自定义 + MaaFramework）。
- **输入**：用户提供的**目录路径**（推荐）或具体 `.log` 文件路径。**不**处理 GitHub issue 附件 zip、不假设必须先解压压缩包。
- 若用户只给目录，在该目录下按下方 **Log Map** 查找标准文件名；若路径不存在或缺少关键文件，先列出目录再说明缺什么证据。

## 标准日志文件（按优先级阅读）

| 文件 | 含义 |
|------|------|
| `gui.log` | **MFW-cfa** 图形界面侧日志：配置加载、任务发起、界面与编排相关线索。 |
| `custom.log` | **Python 自定义**（`assets/agent`）侧日志：自定义识别/动作的打印与异常。 |
| `maa.log` | **MaaFramework** 核心运行时（仓库 README 反馈问题时常用 `debug/maa.log`）：Pipeline 节点、识别、动作、控制器、`task_id` 等。 |

说明：`agent/logger_component.py` 默认可能写入 `debug/custom_YYYYMMDD.log`；若用户统一导出为 `custom.log`，以用户约定为准，并在分析时兼容两种命名。

## 工作流

1. **解析路径**
   - 若是目录：列出该目录下与日志相关的文件（`*.log`、`on_error/`、`config/` 等），不要假定除 `gui.log` / `custom.log` / `maa.log` 以外还有固定结构。
   - 若是单个文件：先判断属于上表哪一类；必要时请用户补全同目录下其它日志。

2. **建立时间线**
   - 从用户描述中取出：版本、平台、控制器类型、任务名、现象与时间锚点。
   - 在 `gui.log` 中查找任务提交、实例/界面侧关键事件（措辞以实际文件为准）。
   - 在 `maa.log` 中用 `task_id`、`Tasker.Task`、`Node.` 等串起同一次运行。
   - 在 `custom.log` 中查找同一时段的 Python 扩展输出。

3. **关联代码与资源**
   - 任务入口与选项：`assets/interface.json`、`assets/tasks/*.json`。
   - Pipeline 节点：`assets/resource/**/pipeline/**/*.jsonc`（含 `base`、`zh_TW` 等变体）。
   - 自定义逻辑：`agent/**/*.py`。
   - Pipeline 协议与术语不确定时：本仓库 `protocol-3.1-task-pipeline.md`、上游 [PipelineProtocol](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/en_us/3.1-PipelineProtocol.md)。

4. **过滤证据**
   - 高价值关键词示例：`Tasker.Task.Starting` / `Succeeded` / `Failed`，`Node.Recognition.Failed`，`Node.Action.Failed`，`timeout`，`Warn` / `Error` / `Fatal`，`post_task`，`task_id`。
   - 只引用支撑结论的片段，勿全文粘贴大日志。

5. **可选材料**
   - `on_error/` 下的截图：用于核对实际画面与识别是否一致。
   - 用户目录下的配置快照（若存在）：核对选项是否与口述一致。

## 根因与输出

- 先区分：框架层（`maa.log`）、界面层（`gui.log`）、自定义扩展（`custom.log`）哪一层最先出现异常或矛盾。
- 若日志显示任务成功但用户描述失败，明确写出「该份日志是否覆盖复现场景」。
- 结论需有日志摘录或节点名/Pipeline 路径级依据；需要改 Pipeline 时指向具体 `jsonc` 节点名。

### 建议的回答结构

```markdown
## 现象与范围
## 日志证据（gui / custom / maa）
## 时间线与 task 关联（若有）
## 根因判断
## 建议（配置 / 资源 / 代码 / 升级）
## 置信度与缺失证据
```

## 注意事项

- 默认**不**分析 `.dmp`；若用户附带崩溃转储，说明需要专用符号化环境再判断。
- 用户任务名、选项名若要友好展示，可在 `assets` 内查找与 `interface.json`/任务 JSON 对应的文案；找不到再写原始 id。
- 引用本仓库代码时使用仓库内路径；引用 MaaFramework 行为可指向上游文档链接。
