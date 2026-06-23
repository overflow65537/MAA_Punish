# 日本語リソース（ja_JP）

## 基本方針

本ディレクトリは **`base` をベース** として動作します。  
`assets/resource/base/pipeline/` にあるノード定義・認識タイプ・アクション・遷移などは **そのまま継承** され、日本語クライアント向けには **差分のみ** をこのディレクトリに置きます。

## ここで変更する項目

| 項目 | 説明 |
|------|------|
| **`expected`** | OCR ノードの期待文字列。ゲーム UI の日本語／繁体字／簡体字表記に合わせて上書きする |
| **`roi`** | テキストが長く、簡体 `base` の領域では切れる場合のみ調整する |

それ以外（`recognition.type`、`action`、`next`、`focus` など）は **`base` に任せ、ここでは触らない** ことを推奨します。  
UI 文言の多言語表示は `assets/i18n/ja_jp.json` の `$focus.*` キーで管理されています。

## ローグライクタスクと `assets/tasks`

次の **5 つの肉鴿** は、難易度・モード・調査団などをタスク JSON の `pipeline_override` で上書きしています。  
日本語／繁中 UI に合わせる場合は、**対応する task ファイル** の `expected` にも言語別の文字列を追加してください（簡体＋繁体の併記を推奨）。

| 肉鴿 | パイプライン | タスク定義 |
|------|-------------|-----------|
| 宣叙妄响 | `pipeline/Roguelike_1/` | `assets/tasks/宣叙妄响.json` |
| 厄愿潮声 | `pipeline/Roguelike_2/` | `assets/tasks/厄愿潮声.json` |
| 矩阵循生 | `pipeline/Roguelike_3/` | `assets/tasks/矩阵循生.json` |
| 寒境曙光 | `pipeline/Roguelike_4/` | `assets/tasks/寒境曙光.json` |
| 神寂启示录 | `pipeline/Roguelike_5/` | `assets/tasks/神寂启示录.json` |

例（難易度の上書き）：

```json
"选择难度_宣叙妄响": {
    "recognition": {
        "param": {
            "expected": ["入门", "入門"]
        }
    }
}
```

`雾夜镇魂曲`（`Roguelike_6`）も同様に `assets/tasks/雾夜镇魂曲.json` でモード・難度を上書きできます。

## 追加・同期の手順

1. `base` にノードや `expected` を追加したら、必要なら本ディレクトリに **同名ノード** で差分だけを書く  
2. 上記 5 肉鴿で難易度などを変える場合は **`assets/tasks/<タスク名>.json`** も更新する  
3. クライアントのリソースパックで **日本語（ja_JP）** が選ばれていることを確認する
