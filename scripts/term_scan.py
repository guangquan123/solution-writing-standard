# -*- coding: utf-8 -*-
"""term_scan.py —— 方案生造词/AI味扫描器（solution-doc-standard 技能工具）

用法:
    python -X utf8 term_scan.py <目标文档.md/.txt/.docx> <语料目录> [--min-freq 2] [--top 30] [--industry manufacturing]

输出: markdown 报告（stdout），包含六部分：
  1. 生造词候选（文档>=min-freq 且语料零命中的中文片段，已去重叠子串）
  2. 后缀造词（XX化/XX性/XX感 且语料零命中）
  3. 隐喻词表语料命中（零命中=候选）
  4. 破折号清单（行号）
  5. 绝对化断言清单
  6. 行业语境歧义词（可选）

原则: 语料是唯一裁判。本脚本只出证据，改不改由对照表与用户确认决定。
"""
import argparse
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 含任意虚词的片段直接排除（降噪，实测最有效的手段）
FUNC_CHARS = set("的了着呢吧吗我们你是他她它们这那个也就在和与或但对于中被从把给让使向往之其各每某另则都还又再已经要可以上下来去出入如")
SUFFIXES = ("化", "性", "感")
METAPHOR_WORDS = ["引擎", "抓手", "赋能", "载体", "反哺", "穿透", "沉淀", "底座", "中台", "闭环", "治理三角", "颗粒度", "画像"]
ASSERTIVE_WORDS = ["必然", "必将", "一定会", "毫无疑问", "显著提升", "大幅提升", "极大提升", "彻底解决", "根本解决", "全面覆盖", "完美"]
INDUSTRY_AMBIG = {
    "manufacturing": {"生产": "IT义(生产环境/生产告警)与制造义歧义"},
    "finance": {"清算": "批处理义与结算业务义歧义", "对账": "技术对账与业务对账歧义"},
}
CN = re.compile(r"[\u4e00-\u9fff]")


def is_pure_cn(s):
    return bool(s) and all("\u4e00" <= c <= "\u9fff" for c in s)


def load_target(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        from docx import Document
        d = Document(path)
        parts = [p.text for p in d.paragraphs]
        for t in d.tables:
            for r in t.rows:
                for c in r.cells:
                    parts.append(c.text)
        return "\n".join(parts)
    for enc in ("utf-8", "gbk"):
        try:
            return io.open(path, encoding=enc).read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise SystemExit(f"无法读取目标文档（utf-8/gbk 均失败）: {path}")


def iter_corpus_files(root):
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if os.path.splitext(fn)[1].lower() in (".md", ".txt", ".docx"):
                yield os.path.join(dirpath, fn)


def load_corpus(root):
    texts = {}
    for fp in iter_corpus_files(root):
        try:
            if fp.lower().endswith(".docx"):
                from docx import Document
                d = Document(fp)
                buf = [p.text for p in d.paragraphs]
                for t in d.tables:
                    for r in t.rows:
                        for c in r.cells:
                            buf.append(c.text)
                texts[fp] = "\n".join(buf)
            else:
                for enc in ("utf-8", "gbk"):
                    try:
                        texts[fp] = io.open(fp, encoding=enc).read()
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue
        except Exception as e:  # 单文件失败不阻断
            print(f"<!-- 语料跳过 {fp}: {e} -->", file=sys.stderr)
    return texts


def ngram_positions(text, n):
    pos = {}
    for i in range(len(text) - n + 1):
        frag = text[i:i + n]
        if is_pure_cn(frag):
            pos.setdefault(frag, []).append(i)
    return pos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("corpus_dir")
    ap.add_argument("--min-freq", type=int, default=2)
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--industry", default=None, help="manufacturing / finance")
    args = ap.parse_args()

    text = load_target(args.target)
    corpus = load_corpus(args.corpus_dir)
    corpus_all = "\n".join(corpus.values())
    n_files = len(corpus)

    def corpus_count(w):
        return corpus_all.count(w)

    # --- 1. 生造词候选: 文档>=min-freq & 语料0 & 无虚词 & 去重叠子串 ---
    cands = {}  # frag -> (count, positions)
    for n in range(2, 7):
        for frag, poss in ngram_positions(text, n).items():
            if len(poss) >= args.min_freq and not (set(frag) & FUNC_CHARS):
                cands.setdefault(frag, (len(poss), poss))
    # 去重叠: 长词位置区间完全覆盖短词的全部出现 → 短词弃
    final = []
    for frag in sorted(cands, key=lambda f: (-len(f), -cands[f][0])):
        cnt, poss = cands[frag]
        covered = True
        for p in poss:
            if not any(p >= q and p + len(frag) <= q + len(big)
                       for big in final for q in cands[big][1]):
                covered = False
                break
        if not covered:
            final.append(frag)

    # 覆盖过滤: 候选的全部出现位置被"语料命中的更长片段"覆盖 → 多为跨词切片伪候选
    def covered_by_corpus_word(p, L):
        s0, e0 = max(0, p - 6), min(len(text), p + L + 6)
        window = text[s0:e0]
        for a in range(len(window)):
            for b in range(a + L + 1, min(len(window), a + L + 6) + 1):
                sub = window[a:b]
                if not is_pure_cn(sub):
                    continue
                if s0 + a <= p and s0 + b >= p + L and corpus_count(sub) > 0:
                    return True
        return False

    def is_compound(frag, thresh=5):
        # 任意二分切分，两部分均语料高频 → 语义透明的组合词，通常保留
        for i in range(2, len(frag) - 1):
            if corpus_count(frag[:i]) >= thresh and corpus_count(frag[i:]) >= thresh:
                return True
        return False

    zero_hits, compounds = [], []
    for frag in final:
        if corpus_count(frag) > 0:
            continue
        cnt, poss = cands[frag]
        if all(covered_by_corpus_word(p, len(frag)) for p in poss):
            continue
        if len(frag) >= 4 and is_compound(frag):
            compounds.append((frag, cnt))
        else:
            zero_hits.append((frag, cnt))
    zero_hits.sort(key=lambda x: -x[1])
    compounds.sort(key=lambda x: -x[1])

    # --- 2. 后缀造词 ---
    suffix_cands = []
    seen = {f for f, _ in zero_hits}
    for frag, (cnt, _p) in cands.items():
        if len(frag) >= 3 and frag.endswith(SUFFIXES) and corpus_count(frag) == 0 and frag not in seen:
            suffix_cands.append((frag, cnt))
    suffix_cands.sort(key=lambda x: -x[1])

    # --- 3. 隐喻词表 ---
    metaphors = [(w, text.count(w), corpus_count(w)) for w in METAPHOR_WORDS if text.count(w) > 0]

    # --- 4. 破折号 ---
    dash_lines = [i + 1 for i, line in enumerate(text.splitlines()) if "——" in line]

    # --- 5. 绝对化断言 ---
    assertives = [(w, text.count(w)) for w in ASSERTIVE_WORDS if text.count(w) > 0]

    # --- 6. 行业歧义词 ---
    industry_rows = []
    if args.industry and args.industry in INDUSTRY_AMBIG:
        for w, note in INDUSTRY_AMBIG[args.industry].items():
            industry_rows.append((w, text.count(w), corpus_count(w), note))

    # --- 输出 ---
    out = []
    out.append("# term_scan 扫描报告")
    out.append("")
    out.append(f"- 目标: `{args.target}`（{len(text)} 字符）")
    out.append(f"- 语料: `{args.corpus_dir}`（{n_files} 份，{len(corpus_all)} 字符）")
    out.append(f"- 参数: min_freq={args.min_freq}, top={args.top}, industry={args.industry or '未指定'}")
    out.append("")
    out.append("> 本报告只出证据；候选词是否修改由对照表确认决定。")
    out.append("")
    out.append("## 1. 生造词候选（文档高频 + 语料零命中）")
    out.append("")
    out.append("| 候选词 | 文档次数 | 长度 |")
    out.append("|---|---|---|")
    for frag, cnt in zero_hits[:args.top]:
        out.append(f"| {frag} | {cnt} | {len(frag)} |")
    if not zero_hits:
        out.append("| （无） | | |")
    out.append("")
    out.append("## 2. 组合词（语料高频词的直接拼接，通常保留）")
    out.append("")
    out.append("| 词 | 文档次数 | 说明 |")
    out.append("|---|---|---|")
    for frag, cnt in compounds[:args.top]:
        out.append(f"| {frag} | {cnt} | 二分切分双高频，语义透明 |")
    if not compounds:
        out.append("| （无） | | |")
    out.append("")
    out.append("## 3. 后缀造词（XX化/XX性/XX感，语料零命中）")
    out.append("")
    out.append("| 候选词 | 文档次数 |")
    out.append("|---|---|")
    for frag, cnt in suffix_cands[:args.top]:
        out.append(f"| {frag} | {cnt} |")
    if not suffix_cands:
        out.append("| （无） | |")
    out.append("")
    out.append("## 4. 隐喻词表命中（语料命中即放行）")
    out.append("")
    out.append("| 词 | 文档次数 | 语料次数 | 判定 |")
    out.append("|---|---|---|---|")
    for w, dc, cc in metaphors:
        out.append(f"| {w} | {dc} | {cc} | {'保留（语料在用）' if cc > 0 else '候选（语料零命中）'} |")
    out.append("")
    out.append("## 5. 破折号（——）")
    out.append("")
    out.append(f"- 共 {len(dash_lines)} 行含有破折号" + (f"：行 {', '.join(map(str, dash_lines[:30]))}{'...' if len(dash_lines) > 30 else ''}" if dash_lines else ""))
    out.append("")
    out.append("## 6. 绝对化断言")
    out.append("")
    out.append("| 词 | 次数 |")
    out.append("|---|---|")
    for w, c in assertives:
        out.append(f"| {w} | {c} |")
    if not assertives:
        out.append("| （无） | |")
    out.append("")
    if industry_rows:
        out.append("## 7. 行业语境歧义词")
        out.append("")
        out.append("| 词 | 文档次数 | 语料次数 | 说明 |")
        out.append("|---|---|---|---|")
        for w, dc, cc, note in industry_rows:
            out.append(f"| {w} | {dc} | {cc} | {note}（需人工判读语料义项） |")
        out.append("")
    print("\n".join(out))


if __name__ == "__main__":
    main()
