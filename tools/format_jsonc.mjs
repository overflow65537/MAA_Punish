import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { format, applyEdits } from "jsonc-parser";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");

const SKIP_DIRS = new Set([".git", "node_modules", "__pycache__", ".venv", "venv"]);

/** 移除 JSONC 中 ] / } 前的尾逗号（不触碰字符串与注释）。 */
function stripTrailingCommas(text) {
    const out = [];
    let index = 0;
    let inString = false;
    let escape = false;
    let inLineComment = false;
    let inBlockComment = false;

    while (index < text.length) {
        const char = text[index];
        const next = text[index + 1];

        if (inLineComment) {
            out.push(char);
            if (char === "\n") inLineComment = false;
            index += 1;
            continue;
        }

        if (inBlockComment) {
            out.push(char);
            if (char === "*" && next === "/") {
                out.push(next);
                index += 2;
                inBlockComment = false;
                continue;
            }
            index += 1;
            continue;
        }

        if (inString) {
            out.push(char);
            if (escape) {
                escape = false;
            } else if (char === "\\") {
                escape = true;
            } else if (char === '"') {
                inString = false;
            }
            index += 1;
            continue;
        }

        if (char === '"') {
            inString = true;
            out.push(char);
            index += 1;
            continue;
        }

        if (char === "/" && next === "/") {
            inLineComment = true;
            out.push(char, next);
            index += 2;
            continue;
        }

        if (char === "/" && next === "*") {
            inBlockComment = true;
            out.push(char, next);
            index += 2;
            continue;
        }

        if (char === ",") {
            let probe = index + 1;
            while (probe < text.length && " \t\r\n".includes(text[probe])) {
                probe += 1;
            }
            if (probe < text.length && (text[probe] === "]" || text[probe] === "}")) {
                index += 1;
                continue;
            }
        }

        out.push(char);
        index += 1;
    }

    return out.join("");
}

function walkJsonc(dir, out = []) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        if (SKIP_DIRS.has(entry.name)) continue;
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) walkJsonc(full, out);
        else if (entry.name.endsWith(".jsonc")) out.push(full);
    }
    return out;
}

function formatJsonc(text) {
    const edits = format(text, undefined, {
        tabSize: 4,
        insertSpaces: true,
        eol: "\n",
    });
    return stripTrailingCommas(applyEdits(text, edits));
}

function main() {
    const files = walkJsonc(ROOT);
    let changed = 0;

    for (const file of files.sort()) {
        const text = fs.readFileSync(file, "utf8");
        const formatted = formatJsonc(text);
        const normalized = formatted.endsWith("\n") ? formatted : `${formatted}\n`;
        if (normalized !== text) {
            fs.writeFileSync(file, normalized, "utf8");
            changed += 1;
            console.log(path.relative(ROOT, file));
        }
    }

    console.log(`formatted ${changed} / ${files.length} jsonc files`);
}

main();
