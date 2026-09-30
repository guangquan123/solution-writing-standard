# solution-writing-standard 版本沿革

## 融合后

| 版本 | 日期 | 改了什么 | 为什么改 |
|---|---|---|---|
| 2.0.0 | 2026-09-30 | 与 solution-doc-standard v2.1.0 融合为四模式全生命周期助手（A 新写 / B 改稿修编 / C 草稿优化 / D 交付自检）：① 触发词合并去重（原「术语对齐」等两边撞车）② 硬约束 5＋13 条合并为统一编号 14 条 ③ 五组自检单源化到《方案编写通用规范》附录 A ④ 语言层三层归一（SKILL.md 五步入口＋指引母本＋scripts 实现）⑤ C 模式管线细则下沉至 references/草稿优化管线.md，SKILL.md 控制注入体积 ⑥ scripts/ 与 examples/ 工具链迁入本技能 | 两个技能触发词撞车、去AI味指引与自检清单双写漂移风险、方案工作流（写→改→打磨→自检）本为一条链，用户决策融合（沿用本名、旧技能存档后下线） |

## 前身之一：solution-writing-standard（编写类）

| 版本 | 日期 | 改了什么 | 为什么改 |
|---|---|---|---|
| 1.2.0 | （融合前现行版） | 新写/改稿/自检三模式，配套《方案编写通用规范》V1.2、去AI味与术语对齐操作指引、交付模板集 | 源自多个交付型方案的编写、评审与改稿复盘；更早版本沿革无存档记录 |

## 前身之二：solution-doc-standard（优化类，2026-09-30 下线存档）

| 版本 | 日期 | 改了什么 | 为什么改 |
|---|---|---|---|
| 1.0.0 | 2026-09-24 | 初建（时名 solution-optimizer）：语言层五步工作流＋term_scan.py 扫描脚本 | 用户要求把多方案优化经验沉淀为可复用 skill |
| 1.1.0 | 2026-09-24 | 更名 solution-doc-standard；新增 fix_terms.py＋check_terms.py；examples/ 端到端示例 | 补齐替换与验证闭环，对照表之后的执行环节脚本化 |
| 2.0.0 | 2026-09-24 | 升级草稿优化总入口：⓪接稿诊断＋四层管线（结构/内容/语言/格式） | 用户核心目标"先有草稿、不断优化到交付" |
| 2.0.1 | 2026-09-24 | 体检修复：恢复"输入要求"三档节；硬约束统一编号 13 条；建 versions/ 存档与错题本 | skill-doctor 体检黄 68 分，执行处方 |
| 2.0.2 | 2026-09-28 | 全量脱敏：source 与示例语料路径、README 项目指代等 6 处改写 | 为推送公开远程仓库做准备，执行客户敏感信息不入库铁律 |
| 2.1.0 | 2026-09-28 | 开源化自包含改写：内部资产引用全部内联；README 重写为公开通用版；新增 MIT LICENSE | 用户要求书面表达不含项目、产品信息，聚焦表达优化方法本身 |

## 存档与分发说明

- `versions/solution-writing-standard-v1.2.0/`：编写版融合前全文（SKILL.md、references、templates）。
- `versions/solution-doc-standard-v2.1.0/`：优化版下线时全文（SKILL.md、scripts、examples、README、LICENSE、CHANGELOG、versions、内部 references），可整体回滚。
- **分发边界**：`versions/` 为开发工作区内部存档（含历史项目语境），不随公开仓库分发。公开仓库分发范围：README / LICENSE / SKILL.md / CHANGELOG / references / templates / scripts / examples。
- **同步状态**：v2.0.0 起同步至 GitHub 仓库 [guangquan123/solution-writing-standard](https://github.com/guangquan123/solution-writing-standard)（原 v1.2.0 开源版同仓库升版）。工作区版与仓库版仅 `metadata.author` 署名字段不同（工作区 deepworks-user-2fqhuw，仓库 guangquan123），其余内容一致。
