# 端到端最小示例

演示三件套工具链的完整链路：**扫描 → 对照表 → 替换 → 验证**。从本 skill 根目录（`.opencode/skills/solution-writing-standard/`）执行。

## 0. 示例内容

| 文件 | 角色 |
|---|---|
| `target/sample_doc.md` | 待优化方案稿：含生造词"治理三角"（2 处）、"反哺"（2 处）、破折号（1 处）、绝对化断言"必然存在"（1 处） |
| `corpus/委托方数据管理办法_示例.md` | A 级语料（委托方制度）：含替换词"三个模块的分工""反馈"的出处 |
| `corpus/行业参考_示例.md` | C 级语料：含"闭环"（演示行业词不被误杀） |
| `pairs.json` | 替换表（对照表经用户批准后的产物） |
| `target/sample_doc_v1.1.md` | 优化后的定稿：含新修订历史行（行内保留旧词"治理三角"，演示排除逻辑） |

## 1. 扫描（term_scan.py）

```powershell
python -X utf8 scripts/term_scan.py examples/target/sample_doc.md examples/corpus --top 10
```

预期：主表出现 `治理三角`、`反哺`（语料零命中）；隐喻词表中 `闭环` 语料命中 → 保留；破折号 1 行；绝对化断言 `必然存在` 1 次。

## 2. 对照表 → 用户确认（人工步骤）

据扫描结果编对照表（候选词｜次数｜改后｜语料出处｜判定），**经用户逐条批准后**固化为本目录 `pairs.json`。替换词出处：`三个模块的分工`←委托方办法第 12/15 条（2 次）；`反馈`←委托方办法（4 次）；`通常会有`/冒号改写←句式层断言弱化与破折号规则。

## 3. 替换（fix_terms.py）

```powershell
# 演示时先复制到临时目录，避免改动示例初始态：
Copy-Item examples/target/sample_doc.md $env:TEMP\fix_demo.md
# （pairs.json 中 file 需指向副本路径，或直接在真实场景对源文件执行）
python -X utf8 scripts/fix_terms.py examples/pairs.json --dry-run   # 先断言
```

预期：4 条断言全过；`--dry-run` 不写回。去掉 `--dry-run` 执行写回。

## 4. 验证（check_terms.py）

```powershell
python -X utf8 scripts/check_terms.py examples/check.json
```

预期：全部 PASS。要点——`sample_doc_v1.1.md` 的修订历史 V1.1 行含旧词"治理三角"，但 `body_start: "一、建设背景"` 把文档控制区排除在 ABSENT 检查之外，旧词作为历史记录合法保留。

## 顺序纪律（真实项目）

1. `fix_terms.py` 必须在**追加新修订历史行之前**执行（否则历史行里的旧词会破坏计数断言）；
2. 替换完成后追加修订历史行（行内可含旧词名，属历史记录）；
3. `check_terms.py` 用 `body_start` 排除文档控制区做零残留检查。
