---
name: lhg-sp-plan
description: 独立站建站规划：店铺定位三问、页面清单、site_spec.json 施工图规范。任何建站工作开始前先加载，施工图没定不许画页面。
license: MIT
compatibility: 适用于任何支持 Markdown 指令的 AI 助手（Claude Code、豆包、Workbuddy 等）
metadata:
  version: 1.0.0
  author: 刘洪光
---

# lhg-sp-plan：独立站建站规划

> 目标：把"想开个网店"变成一份机器可读、人类可确认的施工图（`site_spec.json`）。
> 核心纪律：**先定施工图，再画页面**——没有施工图就搭页面的是野路子，返工从这里开始。

## 1. 何时使用

- 用户说"帮我做个独立站/开个网店" → 全流程
- 只想知道"我这个店缺哪些页面" → 跑第 3 步清单对照
- 站点已上线想改版 → 先更新 spec，再动手（spec 是唯一事实源）

## 2. 输入与输出

- **输入**：一句话店铺定位（卖什么、卖给谁），可选：语言、币种、目标市场
- **输出**：`site_spec.json`（见第 4 节格式）+ 一页纸"开店说明书"（给用户看的中文版）
- **不输出**：页面设计稿、装修细节——那是搭建阶段的事

### 输入缺失时的默认走法

用户只说了"卖杯子"，没说别的 → 按默认值走，不许连环追问：

| 没给的信息 | 默认值 |
|---|---|
| 店铺类型 | 单品/少 SKU 精品站（先跑通一条链路） |
| 语言 | 中文 |
| 币种 | 美元（USD，面向跨境）或人民币（按用户所在地） |
| 目标市场 | 用户所在地区 |

默认值要在开店说明书里**明确写出来**让用户确认，而不是悄悄假设。

## 3. 店铺定位三问

施工图之前，先把这三问的答案钉死：

1. **卖什么**：1 个主类目，最多 3 个。贪多等于没定位。"什么都卖"的店，用户 3 秒就关掉。
2. **卖给谁**：一句话人群画像（年龄/场景/痛点）。例："25–35 岁通勤族，保温杯用两年就漏水"。
3. **凭什么买你**：一句话差异化（价格/品质/服务/故事，四选一钉死）。例："同品质比大牌便宜一半，7 天无理由"。

三问答不上来 → 先帮用户想清楚，不许带着模糊定位进施工图。

### 定位速写模板（给用户填空）

```
我卖【1 个主类目】，卖给【一句话人群】，
他们现在的痛点是【一句话痛点】，
凭什么买我：【价格/品质/服务/故事四选一 + 一句话】。
```

例：我卖手工皂，卖给 25–35 岁敏感肌女生，她们现在的痛点是市面香皂洗完紧绷，
凭什么买我：品质——冷制皂，甘油全保留，7 天无理由。

## 4. site_spec.json 施工图规范

```json
{
  "store_name": "杯具小店",
  "language": "zh-CN",
  "currency": "USD",
  "https": true,
  "pages": {
    "home":     {"file": "pages/index.html"},
    "product":  {"file": "pages/product.html"},
    "cart":     {"file": "pages/cart.html"},
    "checkout": {"file": "pages/checkout.html"},
    "refund":   {"file": "pages/refund.html"},
    "privacy":  {"file": "pages/privacy.html"},
    "terms":    {"file": "pages/terms.html"},
    "about":    {"file": "pages/about.html"}
  },
  "trust_elements": {
    "refund_policy": true,
    "contact": true,
    "payment_badges": true,
    "privacy_policy": true
  },
  "checkout": {
    "guest_checkout": true,
    "steps": ["信息填写", "配送方式", "支付", "确认"],
    "payment_methods": ["Visa", "PayPal", "支付宝"]
  }
}
```

字段说明：

- `pages`：必需四页 `home/product/cart/checkout` 缺一不可；`refund/privacy` 是信任页，`terms/about` 是加分项
- `trust_elements`：信任四件套，发布前 hook 会逐项校验（见 hooks 说明）
- `checkout.guest_checkout`：必须为 `true`——强制注册是结账第一杀手
- `https`：必须为 `true`，结账页没有 HTTPS 等于裸奔

施工图有效性（发布前 hook 自动校验）：

- JSON 合法
- `pages` 含 home/product/cart/checkout
- `trust_elements` 四项全为 true

## 5. 页面清单：每页必须回答的问题

| 页面 | 必须回答 | 缺了的后果 |
|---|---|---|
| 首页 | 这家卖什么？凭什么买？ | 用户 3 秒关掉 |
| 选品/类目页 | 怎么快速找到我想要的？（筛选/排序） | SKU 一多就迷路 |
| 产品页 | 值多少钱？靠谱吗？（见 lhg-sp-product 七要素） | 加购率垫底 |
| 购物车 | 我选了啥？一共多少钱？ | 弃购 |
| 结账页 | 几步能买完？安不安全？（见 lhg-sp-checkout） | 弃单 |
| 退换货政策页 | 买错了能退吗？几天？找谁？ | 不敢下单 |

## 6. 反模式

1. **定位贪多**："日用百货什么都卖"——结果是什么都卖不出去。先 1 个类目跑通。
2. **页面先行**：spec 没定就开始装修首页——返工率 100%，因为导航和信任页迟早要加回来。
3. **币种拍脑袋**：目标市场用美元，结账页写人民币——用户以为被多收钱。
4. **信任页后补**："先上线，政策页以后再说"——以后就是永远没有，转化率一直垫底。
5. **抄大牌结构**：把亚马逊的类目树抄到单品站上——单品站要的是"一条路走到底"，不是迷宫。

## 7. 自检与反馈

### 质检门（施工图交付前自查）

- [ ] 定位三问都有**一句话**答案（不是一段话）
- [ ] `site_spec.json` 通过发布 hook 的校验（必需页 + 信任四件套）
- [ ] 默认值在开店说明书里明确列出，用户已确认
- [ ] 结账 `guest_checkout` 为 true

### 标准冒烟用例

1. 输入"卖手工皂" → 输出 spec 含 8 页、信任四件套全 true、checkout 四步
2. 输入只给两个字"杯子" → 用默认值补齐，说明书里明确标注"以下为默认值"

### 反馈

发现 bug 或有改进建议，以 `[QC] <一句话问题>` 为标题提交到 https://github.com/lhg-plugs/lhg-shopify/issues，正文写清"复现步骤 → 实际表现 → 期望表现"。

## 出品：刘洪光

本 skill 由真人出镜 IP「刘洪光」（安徽合肥）出品，归属 [lhg-skills](https://github.com/lhg-skills)。

- GitHub 主页：https://github.com/lhg-skills —— 全部 skill 开源在此，欢迎 star
- 抖音：搜「刘老师讲AI实战」
- 微信：lhgsmsw
