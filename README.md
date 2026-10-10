<!-- About 简介（推送后填写到仓库 About 栏）：
独立站建站专家：从选品页到结账的开店流水线 ｜ 一键安装：/plugin marketplace add lhg-plugs/lhg-shopify
-->
<!-- topics（推送后打）：claude-code, claude-plugin, agent-skills, shopify, ecommerce -->

# lhg-shopify：独立站建站专家

> **一句话介绍**：从选品页到结账的开店流水线——店铺定位→施工图→产品页七要素→四步结账→信任四件套→发布自检，35 条确定性规则把关，缺信任元素不许上线。
>
> **一键安装**：在 Claude Code 里运行
> ```
> /plugin marketplace add lhg-plugs/lhg-shopify
> /plugin install lhg-shopify@lhg-plugs
> ```

## 它是什么

`lhg-shopify` 是一个 Claude Code 插件（plugin 为主、skill 为辅），专为"想开独立站的小白"设计：

- **3 个命令**（小白入口）：`shopify` 一句话开店（规划→产品页→结账→信任→自检），`product-page` 单品打磨（七要素逐项落实），`shopify-audit` 上线前体检
- **4 个平台中立 skill**（方法论，可移植到豆包/Workbuddy 等 agent 平台）：建站规划、产品页七要素、四步结账、信任元素与移动端
- **3 个专家 agent**：搭建师、体验质检员、结账流程测试员
- **1 个硬门 hook**：发布前自动校验 `site_spec.json` 完整性与信任元素（可一键豁免，不骚扰）
- **35 条确定性自查规则**：信任 9、产品页 9、结账 8、移动端 5、施工图 4，纯 Python、零第三方依赖，5 秒出结果

工作流：`shopify`（一条龙）→ `shopify-audit`（查一遍），也可以只用 `product-page` 打磨单个产品页。

## 3 个命令用法

| 命令 | 作用 | 示例 |
|---|---|---|
| `/lhg-shopify:shopify` | 一句话开店：定位→施工图→产品页→结账→信任→自检 | `/lhg-shopify:shopify "卖手工皂" --lang zh` |
| `/lhg-shopify:product-page` | 单品打磨：七要素逐项落实 | `/lhg-shopify:product-page ./pages/product.html` |
| `/lhg-shopify:shopify-audit` | 上线前体检（脚本 + 人工评审清单） | `/lhg-shopify:shopify-audit ./site` |

## 自查说明

自查 = 确定性脚本（机器）+ 人工评审清单（人）：

1. 先跑 `scripts/audit/shopify_audit.py`（35 条规则：施工图 4、信任 9、产品页 9、结账 8、移动端 5），零 LLM 成本；
2. 发现分三级：**blocker**（必须修，发布前 hook 会拦截）、**warning**（修或写豁免理由）、**nit**（顺手修）；
3. 再按 `lhg-sp-trust` skill 第 6 节评审清单过一遍脚本抓不到的（首屏 3 秒测试、结账全流程、手机实测）。

blocker 清零才算做完；为清零改规则算作弊，不许。

## 目录结构

```
lhg-shopify/
├── .claude-plugin/          # plugin.json（插件清单）+ marketplace.json（本仓即市场）
├── commands/                # 3 个命令：shopify / product-page / shopify-audit
├── skills/                  # 4 个平台中立 skill（规划/产品页/结账/信任与移动端）
├── agents/                  # 3 个专家 agent（site-builder / ux-reviewer / checkout-tester）
├── hooks/                   # 1 个硬门（发布前 site_spec 校验）+ 豁免说明
├── scripts/audit/           # 35 条确定性自查规则（零第三方依赖）
├── fixtures/                # 冒烟测试用例（坏/好对照）
├── smoke_test.py            # 一键冒烟测试
├── ATTRIBUTION.md           # 灵感来源与许可声明
└── LICENSE                  # MIT
```

## 什么时候用 / 什么时候不用（FAQ）

**什么时候用：**

- 你想开个独立站，但不知道从哪下手（选品页？产品页？先装哪个？）时 → 用 `/lhg-shopify:shopify`，一句话走完开店流水线
- 你的产品页有流量没转化时 → 用 `/lhg-shopify:product-page`，七要素逐项找洞
- 你要上线前怕翻车（没退换货政策、结账页强制注册、手机打不开）时 → 跑 `/lhg-shopify:shopify-audit`
- 你想给团队立一套"缺信任元素不许上线"的纪律时 → 它的 hook 硬门与审计脚本开箱即用

**什么时候不用：**

- 你做的是亚马逊/eBay/淘宝等平台店 → 本插件是"独立站"专家，平台店规则完全不同
- 你要的是品牌官网（不卖货）→ 结账流程部分用不上，直接用 lhg-fullstack 更合适

**风险点诚实说明：**

- **支付与物流要自己接**：本插件只管"页面与流程齐不齐"，真实的支付通道（Stripe/PayPal）与物流对接需要你自己去申请，本插件不碰你的银行卡与密钥
- **合规因地而异**：退换货政策模板是通用版，欧盟/美国加州等地区有特殊消费者保护要求，上线前请按目标市场复核
- **审计规则是启发式**：35 条规则覆盖的是"常见翻车点"，不是全部；首屏 3 秒测试这类主观项必须人眼过，不能只信脚本
- **Shopify 是商标**：本插件教你"开独立站的方法论"，与 Shopify 官方无关，不依赖其 API

## lhg-plugs 插件矩阵

| 插件 | 一句话 | 安装 |
|---|---|---|
| [lhg-video-edit](https://github.com/lhg-plugs/lhg-video-edit) | 一句话把口播素材剪成爆款短视频（+口播脚本子命令） | `/plugin install lhg-video-edit@lhg-plugs` |
| [lhg-fullstack](https://github.com/lhg-plugs/lhg-fullstack) | 小白一句话 → 高质量全栈应用 | `/plugin install lhg-fullstack@lhg-plugs` |
| [lhg-shopify](https://github.com/lhg-plugs/lhg-shopify) | 独立站建站专家：从选品页到结账的开店流水线 | `/plugin install lhg-shopify@lhg-plugs` |

## 自检与反馈

本插件自带质检：每次使用后可跑 `python3 smoke_test.py` 一键验证（JSON 合法、skill/command/agent 完整性、35 条规则、fixtures 命中、hooks 行为）。

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-shopify/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

## 出品：刘洪光

本插件由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 视频号：搜「刘洪光实名上网」
- 微信：lhgsmsw
