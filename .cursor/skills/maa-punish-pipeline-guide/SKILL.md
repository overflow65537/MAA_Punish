---
name: maa-punish-pipeline-guide
description: MAA_Punish 任务流水线 JSON/JSONC 编写与审查指南。含 Pipeline 速查表（识别类型、动作类型、节点字段默认值、JumpBack/Anchor、Custom）。基于 MaaFramework 协议与本仓库 protocol-3.1-task-pipeline.md。在编写或审查 pipeline、排查超时/on_error、或使用 TemplateMatch/OCR/Custom 时使用。
---

# MAA_Punish Pipeline 编写指南

## 文档索引

| 需求 | 优先看 |
|------|--------|
| **速查表（本节下方）** | 识别/动作/字段默认值/节点属性 |
| 完整语义与边界情况 | 仓库根目录 `protocol-3.1-task-pipeline.md` |
| 上游原文 | [3.1-PipelineProtocol](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/en_us/3.1-PipelineProtocol.md) |
| JSON Schema 校验 | `tools/schema/pipeline.schema.json`、`custom.*.schema.json` |
| 自动战斗专项 | `docs/自动战斗框架开发指南.md` |
| Python 自定义实现 | `assets/MPAcustom/recognition/`、`assets/MPAcustom/action/` |

---

## Pipeline 速查表

### v1 / v2 写法

- **v1**：`"recognition": "TemplateMatch"`，参数字段与节点平级混写（老写法）。
- **v2（推荐）**：`"recognition": { "type": "TemplateMatch", "param": { ... } }`，`action` 同理；**除 recognition/action 外**的字段（`next`、`timeout`、`pre_delay` 等）仍在节点根上，与协议一致。

### `roi` / `box` / `target`（易混）

| 字段 | 含义 |
|------|------|
| `roi` | 识别搜索区域 [x,y,w,h]，可与 `roi_offset` 叠加 |
| `box` | 识别**命中结果**区域（运行时产生） |
| `target` | 动作作用区域；默认 `true` 表示用当前识别结果的 box |

### 节点通用字段 · 默认值速查

以下为协议常见内置默认（节点未写时使用；实际可能被 `assets/resource/**/default_pipeline.json` 覆盖，见下节）。

| 字段 | 典型默认 | 说明 |
|------|----------|------|
| `rate_limit` | 1000 ms | 每轮识别间隔下限 |
| `timeout` | 20000 ms | 本节点 `next` 整轮识别超时；**-1** 表示无限等 **(v5.5)** |
| `pre_delay` / `post_delay` | 200 ms | 识别→动作前、动作→截下一帧前；易引入隐性等待，按需显式写 0 |
| `pre_wait_freezes` / `post_wait_freezes` | 0 | 画面静止再前进；对象形式见协议「等待画面静止」 |
| `repeat` | 1 | 动作重复次数 **(v5.3)** |
| `repeat_delay` / `repeat_wait_freezes` | 0 | 重复间隔 **(v5.3)** |
| `inverse` | false | 反转识别结果 |
| `enabled` | true | false 时其他节点 next 里会跳过该节点 |
| `max_hit` | 无限制 | 命中次数上限 **(v5.1)** |

### 执行顺序（单节点内）

`pre_wait_freezes` → `pre_delay` → `action`（及 repeat 分支）→ `post_wait_freezes` → `post_delay` → **截图** → 识别 `next`。

### `next` / `on_error`

| 机制 | 说明 |
|------|------|
| `next` | 按**顺序**尝试子节点识别，**第一个命中**则执行其 action 并进入该子节点上下文 |
| 全未命中 | 循环等待直到 `timeout`（或无限），再进**当前节点**的 `on_error` |
| 动作失败 | 进**命中子节点**的 `on_error`（若写了） |
| 任务结束 | `next` 为空且无需 JumpBack；或 `StopTask`；或外部 `post_stop` |

### 节点属性（next / on_error 列表里）

| 写法 | 作用 |
|------|------|
| `[JumpBack]节点名` 或 `{ "name": "节点名", "jump_back": true }` | 子链跑完后回到**父节点**，从父 `next` 头再扫；用于弹窗/加载。**在 on_error 路径上不回跳 (v5.9)** |
| `[Anchor]锚点名` | 解析为**最后一次被赋值**的锚点指向的节点；`anchor` 字段可在节点上设为字符串 / 数组 / 对象 **(v5.7)** |

---

## 识别算法速查表

`recognition.type`（v2）或 v1 的 `recognition` 字符串。

| 类型 | 用途提要 | 关键 `param`（节选） |
|------|----------|------------------------|
| **DirectHit** | 不识别，直接当命中 | `roi` |
| **TemplateMatch** | 模板找图 | `template`（`image/` 相对路径）、`roi`、`threshold`（默认 0.7）、`method`（如 5 常用）、`green_mask`、`index` / `order_by` |
| **FeatureMatch** | 特征点匹配，透视/尺度变化 | `template`、`count`、`detector`（如 SIFT） |
| **ColorMatch** | 找色 | `method`（如 40=HSV）、`lower`、`upper`、`count`、`connected` |
| **OCR** | 文字 | `expected`（可正则）、`model`、`only_rec`、`color_filter`（引用 ColorMatch 节点名）**v5.8** |
| **NeuralNetworkClassify** | 固定区域分类 | `model`（`model/classify`）、`labels`、`expected`（类下标） |
| **NeuralNetworkDetect** | 检测框 | `model`（`model/detect`）、`expected`、`threshold` |
| **And** **v5.3** | 逻辑与 | `all_of`（节点名字符串 **v5.7** 或内联识别）、`box_index` |
| **Or** **v5.3** | 逻辑或，首个命中即停 | `any_of` |
| **Custom** | 自定义识别（本项目为 Python 注册） | `custom_recognition`、`custom_recognition_param`、`roi` |

---

## 动作类型速查表

`action.type`（v2）或 v1 的 `action` 字符串。

| 类型 | 用途提要 | 关键 `param`（节选） |
|------|----------|------------------------|
| **DoNothing** | 无操作 | — |
| **Click** | 点击 | `target`（true / 节点名 / `[Anchor]名` / 坐标 / 区域）、`target_offset`、`contact`、`pressure` **v5.0** |
| **LongPress** | 长按 | `duration`、`target` 等同 Click |
| **Swipe** | 滑动 | `begin`、`end`（支持折线列表）、`duration`、`only_hover` |
| **MultiSwipe** | 多指滑动 | `swipes[]`：`begin`/`end`/`starting`/… |
| **TouchDown / TouchMove / TouchUp** **v5.0** | 细分触控 | `contact`、`target` |
| **Scroll** **v5.1** | 滚轮（Win/mac 等） | `target`、`dx`、`dy`（建议 Win 下取 120 倍数） |
| **ClickKey** / **LongPressKey** | 按键 | `key`（虚拟键码） |
| **KeyDown** / **KeyUp** **v5.0** | 组合键时序 | `key` |
| **InputText** | 文本 | `input_text` |
| **StartApp** / **StopApp** | 启停应用 | `package` |
| **StopTask** | 停止当前任务链 | — |
| **Command** | 外部进程 | `exec`、`args`（支持 `{ENTRY}` `{NODE}` `{IMAGE}` 等占位） |
| **Shell** **v5.3** | ADB shell | `cmd`、`shell_timeout`（原 timeout **v5.8** 改名） |
| **Screencap** | 保存截图到 log 目录 | `filename`、`format`、`quality` |
| **Custom** | 自定义动作（本项目 Python） | `custom_action`、`custom_action_param`、`target` |

---

## 本项目约定

1. **分辨率**：ROI / 模板均以 **1280×720** 为基准（与 README 模拟器说明一致）。
2. **资源路径**：`assets/resource/**/pipeline/**/*.jsonc`；图片相对各自 bundle 的 `image/` 等目录。
3. **默认值文件**：例如 `assets/resource/base/default_pipeline.json` 会与框架 `default_pipeline.json` 机制合并；改全局默认时注意多 bundle 加载顺序（见协议「多 Bundle」）。
4. **Python Custom（v2 示例骨架）**

```jsonc
"MyStep": {
    "recognition": {
        "type": "Custom",
        "param": {
            "custom_recognition": "YourRecoName",
            "custom_recognition_param": {},
            "roi": [0, 0, 1280, 720]
        }
    },
    "action": {
        "type": "Custom",
        "param": {
            "custom_action": "YourActionName",
            "custom_action_param": {},
            "target": true
        }
    },
    "next": ["NextNode"]
}
```

注册名必须与 `assets/MPAcustom` 内实现一致；调试看 **`custom.log`** 或 `debug/custom_*.log`。

---

## 核心原则（审查时自检）

1. **状态驱动**：识别 → 操作 → 再识别；少凭假设点击后的画面。
2. **高命中率**：`next` 覆盖分支（含弹窗、加载、异常界面）。
3. **慎用纯延迟**：优先加识别节点与 `*_wait_freezes`；需要「无等待」时对默认敏感字段显式 `0`。
4. **Schema**：提交前用仓库工具/IDE 校验 `tools/schema/pipeline.schema.json`。
5. **勿照搬其他项目**：Custom 名称以本仓库为准。

---

## 审查清单

- [ ] 字段符合 schema；Custom 与 Python 注册名一致
- [ ] `next` / `on_error` 覆盖主要分支；JumpBack 用于可恢复中断
- [ ] ROI / 模板基于 720p
- [ ] 任务入口与 `assets/interface.json`、`assets/tasks` 一致
- [ ] 需要文案展示时对照 interface / 任务定义

---

## 参考（本仓库）

- `protocol-3.1-task-pipeline.md`（权威细节）
- `docs/自动战斗框架开发指南.md`
- `tools/schema/pipeline.schema.json`
- 成熟范例：同目录其它 `*.jsonc`（如 `Role_Selection.jsonc`）
