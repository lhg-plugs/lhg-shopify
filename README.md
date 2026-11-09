<!-- About 简介（推送后填写到仓库 About 栏）：
独立站建站专家：从选品页到结账的开店流水线——选品页/产品页/结账流程/信任元素逐项搭建与检查，31 条确定性规则把关，发布前硬门拦截缺项。 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-shopify
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, shopify, ecommerce, independent-station, product-page, checkout -->

<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="lhg-shopify — 独立站建站专家">
</p>

> **一句话介绍**：独立站建站专家：从选品页到结账的开店流水线——选品页/产品页/结账流程/信任元素逐项搭建与检查，31 条确定性规则把关，发布前硬门拦截缺项。

**一键安装**：在 Claude Code 里运行

```bash
/plugin marketplace add lhg-plugs/lhg-shopify
/plugin install lhg-shopify@lhg-plugs
```

## 它能帮你做出什么

每条产出先过确定性脚本自查，再交人工复核清单——数字全部数自仓库里的审计脚本，不靠模型"自觉"。

| 自查脚本 | 规则数 | blocker | warning | nit | 覆盖 |
|---|---|---|---|---|---|
| `scripts/audit/shopify_audit.py` | 35 | 12 | 18 | 5 | spec、trust、product、checkout、mobile |
| **合计** | **35** | **12** | **18** | **5** | |

- **零 LLM 成本**：规则是纯 Python 脚本，零第三方依赖，本地运行。
- **坏 / 好对照可验**：`fixtures/` 里备有坏/好用例，冒烟测试断言命中情况。
- **冒烟全绿**：`python3 smoke_test.py` 46 项全部通过（JSON 合法、frontmatter 完整、命令/skill/agent 齐全）。

## 它是什么

`lhg-shopify` 是一个 Claude Code 插件（plugin 为主、skill 为辅）：

- **3 个命令**（小白入口）：`product-page` 单品打磨、`shopify` 一句话开店、`shopify-audit` 上线前体检
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：lhg-sp-checkout, lhg-sp-plan, lhg-sp-product, lhg-sp-trust
- **3 个专家 agent**：checkout-tester, site-builder, ux-reviewer
- **1 个 hooks**（`hooks/`：validate_site_before_publish.py），关键操作前自动把关
- **35 条确定性自查规则**：纯 Python 脚本，见上表

## 为什么是它

不是一个 prompt，而是一套互相兜底的机制：

1. **确定性脚本（机器）+ 人工复核清单（人）**：先跑 `scripts/` 下的审计脚本（共 35 条规则），发现分三级：**blocker**（必须修）、**warning**（修或写豁免理由）、**nit**（顺手修）；再按对应 skill 的复核清单过一遍脚本抓不到的（内容真实性、越权、口径一致）。blocker 清零才算做完；为清零改规则算作弊，不许。
2. **硬门，不是提醒**：hooks 在关键操作前自动拦截或警告（见 `hooks/`），而不是只在文档里写一句"请注意"。
3. **方法论沉淀在 skill 里**：流程、检查清单、口径都写在 `skills/` 的方法论里，命令只是入口；换个 agent 平台也能复用同一套做法。
4. **可验，不是可信**：`fixtures/` 备有坏/好对照用例，`smoke_test.py` 一键验证，规则有没有生效、自己跑一遍就知道。

## 快速上手

```bash
# 1. 安装（Claude Code 里运行）
/plugin marketplace add lhg-plugs/lhg-shopify
/plugin install lhg-shopify@lhg-plugs

# 2. 一句话开店：选品页→产品页→结账流程→信任元素逐项搭建，最后跑发布自检，缺项不许
/lhg-shopify:shopify "卖手工皂" --lang zh
```

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-shopify:product-page` | 单品打磨：把一个产品页按七要素逐项落实（多图/价格锚点/评价/FAQ/加购/信任徽章/物流），改完跑审计。 | `/lhg-shopify:product-page ./pages/product.html` |
| `/lhg-shopify:shopify` | 一句话开店：选品页→产品页→结账流程→信任元素逐项搭建，最后跑发布自检，缺项不许上线。 | `/lhg-shopify:shopify "卖手工皂" --lang zh` |
| `/lhg-shopify:shopify-audit` | 上线前体检：31 条确定性规则扫描站点（信任元素/结账/产品页/移动端）… | `/lhg-shopify:shopify-audit ./site` |

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你需要单品打磨时 → 用 `/lhg-shopify:product-page`
- 你需要一句话开店时 → 用 `/lhg-shopify:shopify`
- 你需要上线前体检时 → 用 `/lhg-shopify:shopify-audit`

**什么时候不用：**

- 你只需要其中一个零散能力时 → 本插件是成套流程，单点需求用更轻量的 skill 更合适
- 你希望 AI 完全自由发挥、不接受任何自查与硬门时 → 它的规则审计与 hooks 会介入（可关，但那就别装它）
- 你的场景不在上面命令表覆盖范围内时 → 先看命令表，没有对应命令就别硬套

## 目录结构

```
lhg-shopify/
├── smoke_test.py          # 一键冒烟测试
├── ATTRIBUTION.md         # 灵感来源与许可声明
├── LICENSE                # MIT
├── README.md              # 本文件
├── .claude-plugin/
├── agents/
├── commands/
├── fixtures/
├── hooks/
├── scripts/
├── skills/
```

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（本次实测 46 项全部通过）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-shopify/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

同门插件见 [lhg-plugs](https://github.com/lhg-plugs)，86 个插件的完整矩阵在 [marketplace](https://github.com/lhg-plugs/marketplace) 维护。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
