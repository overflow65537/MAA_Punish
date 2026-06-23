# 繁體中文資源（zh_TW）

## 基本方針

本目錄以 **`base` 為基準** 運作。  
`assets/resource/base/pipeline/` 中的節點定義、識別類型、動作、跳轉等 **一律沿用 base**，繁體中文客戶端僅在此目錄放置 **差異覆蓋**。

## 在此修改的欄位

| 欄位 | 說明 |
|------|------|
| **`expected`** | OCR 節點的預期文字，需對應遊戲介面的繁體（或簡繁混排）顯示 |
| **`roi`** | 僅在文字過長、base 的識別區域會裁切時再調整 |

其餘欄位（`recognition.type`、`action`、`next`、`focus` 等）**建議不要在此重寫**，由 base 統一維護。  
介面提示的多語言文案由 `assets/i18n/zh_tw.json` 的 `$focus.*` 鍵負責。

## 肉鴿任務與 `assets/tasks`

以下 **5 個肉鴿** 會在對應的 task JSON 裡用 `pipeline_override` 覆寫難度、模式、調查團等選項。  
台服／Steam 繁中客戶端除 pipeline 覆蓋外，還需在 **對應 task 檔** 的 `expected` 中補上繁體（建議簡體與繁體並列，防禦 OCR 誤識為簡體）。

| 肉鴿 | 流水線 | 任務定義 |
|------|--------|----------|
| 宣敘妄響 | `pipeline/Roguelike_1/` | `assets/tasks/宣叙妄响.json` |
| 厄願潮聲 | `pipeline/Roguelike_2/` | `assets/tasks/厄愿潮声.json` |
| 矩陣循生 | `pipeline/Roguelike_3/` | `assets/tasks/矩阵循生.json` |
| 寒境曙光 | `pipeline/Roguelike_4/` | `assets/tasks/寒境曙光.json` |
| 神寂啟示錄 | `pipeline/Roguelike_5/` | `assets/tasks/神寂启示录.json` |

範例（難度覆蓋）：

```json
"选择难度_宣叙妄响": {
    "recognition": {
        "param": {
            "expected": ["入门", "入門"]
        }
    }
}
```

`雾夜镇魂曲`（`Roguelike_6`）亦可在 `assets/tasks/雾夜镇魂曲.json` 中覆寫模式與難度。

## 新增與同步步驟

1. base 新增或調整節點後，視需要在本目錄以 **同名節點** 只寫差分  
2. 若涉及上述 5 個肉鴿的難度等選項，同步更新 **`assets/tasks/<任務名>.json`**  
3. 請在客戶端資源包中選擇 **繁體中文（zh_TW）**，否則 OCR 可能按簡體匹配導致任務卡死
