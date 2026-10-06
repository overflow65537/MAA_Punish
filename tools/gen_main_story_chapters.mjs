import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, "../resource/base/pipeline/Auto_Main_Story/Chapters");

const STORY_NEXT = ["[JumpBack]播放剧情", "[JumpBack]主线跳过", "跳过剧情"];
const CLICK_OFFSET = [30, 60, -30, 0];
const SWIPE = { begin: [900, 200], end: [200, 200] };
const POST_FREEZE = { time: 500, timeout: 2000, target: [0, 0, 1280, 720] };
const CHAPTER_ROI = [33, 93, 500, 120];
const LEVEL_SELECT_ROI = [245, 0, 1035, 720];

const CONFIG = [
  ["ER02_枯朽为灯", 24, null],
  ["20_烬海异途", 14, null],
  ["ER03_未语庭言", 13, null],
  ["22_创绘映想", 28, null],
  ["23_凛桎鸣渊", 17, null],
  ["ER04_浮英枕梦行", 17, null],
  ["24_萦森歧路", 16, null],
  ["ER05_怒逐沉沙", 18, null],
  ["25_爝火长明", 21, null],
  ["26_摇篮游行", 27, null],
  ["27_碑火铸脊", 29, null],
  ["28_络勾陈", 38, null],
  ["29_源解信标", 18, null],
  ["30_镜像星尘", 17, null],
  ["ER06_幽塔黎光", 22, null],
  ["ER07_云梁觅影", 17, null],
  ["ER08_暮往长离", 26, null],
  ["ER09_晨昏庭影", 19, null],
  ["32_遥行循星", 25, null],
  ["33_锈夜逐光", 33, null],
  ["ER10_醉狱谲笼", 21, null],
  ["34_梦赴光寥之乡", 18, null],
  ["ER11_逐生复始", 16, null],
  ["ER12_末路燎原", 26, null],
  ["35_覆海离声", 22, null],
  ["36_溯梦归途", 14, null],
  ["ER13_织奏序言", 17, [
    ["_17", "ER13-17", true],
    ["_0", "ER13-0", false],
  ]],
  ["ER14_理想笼", 14, null],
  ["37_眠于厄寐之境", 26, null],
  ["38_推想视限", 21, null],
  ["39_冬冕的凋亡", 24, null],
  ["40_更美好的明天", 23, null],
  ["ER15_烈日将烬", 25, null],
  ["ER16_孑念空行", 20, null],
  ["41_长路归航", 28, null],
  ["42_歧海循光", 32, null],
  // 43_远信回响: hidden-story chapter — hand-maintained (see Chapters/43_远信回响.json)
];

function parseStem(stem) {
  if (stem.startsWith("ER")) {
    const i = stem.indexOf("_");
    const erId = stem.slice(0, i);
    const title = stem.slice(i + 1);
    return [stem, erId, `${erId}\\s*${title}`];
  }
  const i = stem.indexOf("_");
  const num = stem.slice(0, i);
  const title = stem.slice(i + 1);
  return [stem, num, `${num}\\s*${title}`];
}

function levelLabels(prefix, total) {
  const final = `${prefix}-${total}`;
  const listing = [];
  for (let i = total - 1; i >= 1; i--) listing.push(`${prefix}-${i}`);
  return [final, listing];
}

function buildChapter(stem, total, extras) {
  const [chapterKey, prefix, ocrExpected] = parseStem(stem);
  const [finalLabel, listingRaw] = levelLabels(prefix, total);
  let listing = listingRaw;
  let finaleForClear = finalLabel;

  const pickMain = `选择最新关卡_${prefix}`;
  const clearSuffix = prefix;

  const nextEntries = [];
  if (extras) {
    const extraLabels = new Set(extras.map((e) => e[1]));
    listing = listing.filter((x) => !extraLabels.has(x));
    for (const [nodeSuf] of extras) {
      nextEntries.push(`[JumpBack]选择最新关卡_${prefix}${nodeSuf}`);
    }
    finaleForClear = extras[extras.length - 1][1];
  } else {
    nextEntries.push(`[JumpBack]选择最新关卡_${prefix}_${total}`);
  }
  nextEntries.push(`剧情通关_${clearSuffix}`);
  nextEntries.push(`[JumpBack]${pickMain}`);

  const doc = {
    [chapterKey]: {
      recognition: {
        type: "OCR",
        param: { roi: CHAPTER_ROI, expected: ocrExpected },
      },
      action: { type: "Swipe", param: SWIPE },
      post_wait_freezes: POST_FREEZE,
      next: nextEntries,
    },
    [pickMain]: {
      recognition: {
        type: "OCR",
        param: { roi: LEVEL_SELECT_ROI, expected: listing, order_by: "Expected" },
      },
      action: { type: "Click", param: { target_offset: CLICK_OFFSET } },
      next: ["主线_选关后战斗"],
    },
  };

  if (extras) {
    for (const [nodeSuf, ocr, story] of extras) {
      const nodeName = `选择最新关卡_${prefix}${nodeSuf}`;
      doc[nodeName] = {
        max_hit: 1,
        recognition: {
          type: "OCR",
          param: { roi: LEVEL_SELECT_ROI, expected: [ocr] },
        },
        action: { type: "Click", param: { target_offset: CLICK_OFFSET } },
        next: story ? STORY_NEXT : ["主线_选关后战斗"],
      };
    }
    doc[`剧情通关_${clearSuffix}`] = {
      recognition: {
        type: "OCR",
        param: { roi: LEVEL_SELECT_ROI, expected: [finaleForClear] },
      },
      next: ["返回"],
    };
  } else {
    doc[`选择最新关卡_${prefix}_${total}`] = {
      max_hit: 1,
      recognition: {
        type: "OCR",
        param: { roi: LEVEL_SELECT_ROI, expected: [finalLabel] },
      },
      action: { type: "Click", param: { target_offset: CLICK_OFFSET } },
      next: STORY_NEXT,
    };
    doc[`剧情通关_${clearSuffix}`] = {
      recognition: {
        type: "OCR",
        param: { roi: LEVEL_SELECT_ROI, expected: [finalLabel] },
      },
      next: ["返回"],
    };
  }

  return doc;
}

const onlyStem = process.argv.find((a) => a.startsWith("--only="))?.slice(7);

for (const [stem, total, extras] of CONFIG) {
  if (onlyStem && stem !== onlyStem) continue;
  const file = path.join(OUT, `${stem}.json`);
  fs.writeFileSync(file, JSON.stringify(buildChapter(stem, total, extras), null, 4) + "\n", "utf8");
  console.log("wrote", stem);
}
