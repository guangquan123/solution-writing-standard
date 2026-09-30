# -*- coding: utf-8 -*-
"""fix_terms.py —— 术语批量替换执行器（solution-doc-standard 技能工具，语言层第 4 步的固化）

用法:
    python -X utf8 fix_terms.py <pairs.json> [--dry-run]

pairs.json 格式（预期次数来自 term_scan.py 扫描结果，禁止拍脑袋填）:
    [
      {"file": "方案.md", "old": "治理三角", "new": "三个模块的分工", "expected": 3},
      {"file": "方案.md", "old": "反哺",     "new": "反馈",           "expected": 2}
    ]

流程（fail-fast，两遍式）:
    第一遍：对每个文件的原文本逐条断言 count(old) == expected；
            任何一条不匹配 → 打印差异、退出码 1、不写任何文件。
    第二遍：按 file 分组、组内按 len(old) 降序（长串先替换，避免子串误伤），
            应用全部替换并写回。

顺序纪律: 替换必须在升版/追加修订历史行之前执行——否则新修订行中的旧词
（历史记录，合法保留）会破坏计数断言。见 SKILL.md 硬约束 7。
"""
import argparse
import io
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs_json")
    ap.add_argument("--dry-run", action="store_true", help="只断言不写回")
    args = ap.parse_args()

    pairs = json.load(io.open(args.pairs_json, encoding="utf-8"))
    if not pairs:
        print("pairs.json 为空，无事可做")
        return

    # --- 第一遍：全量断言（原文本，任何文件都未被改动） ---
    texts = {}
    errors = []
    for p in pairs:
        f, old, exp = p["file"], p["old"], p["expected"]
        if f not in texts:
            try:
                texts[f] = io.open(f, encoding="utf-8").read()
            except UnicodeDecodeError:
                texts[f] = io.open(f, encoding="gbk").read()
        actual = texts[f].count(old)
        if actual != exp:
            errors.append(f"  FAIL {f}: '{old}' 预期 {exp} 处，实际 {actual} 处")
    if errors:
        print("断言失败（文档状态与对照表不符，未改任何文件）：")
        print("\n".join(errors))
        print("处理：核对差异来源（版本漂移/残留/新加修订历史行含旧词），修正 pairs.json 后重跑。")
        sys.exit(1)

    print(f"断言全部通过：{len(pairs)} 条替换对")
    if args.dry_run:
        print("dry-run：未写回。")
        return

    # --- 第二遍：分组替换（组内长串优先）并写回 ---
    groups = {}
    for p in pairs:
        groups.setdefault(p["file"], []).append(p)
    total = 0
    for f, items in groups.items():
        items.sort(key=lambda x: -len(x["old"]))
        s = texts[f]
        for it in items:
            s = s.replace(it["old"], it["new"])
            total += 1
            print(f"  OK {f}: '{it['old']}' -> '{it['new']}' ({it['expected']} 处)")
        io.open(f, "w", encoding="utf-8").write(s)
    print(f"完成：{len(groups)} 个文件、{total} 条替换已写回。")


if __name__ == "__main__":
    main()
