---
description: 上线前体检：31 条确定性规则扫描站点（信任元素/结账/产品页/移动端），输出 blocker/warning/nit 三级报告。
argument-hint: [站点目录] [--fail-on blocker|warning|nit]
---

# /lhg-shopify:shopify-audit —— 上线前体检

用户输入在 `$ARGUMENTS` 中：`[站点目录] [--fail-on 级别]`。跑 `scripts/audit/shopify_audit.py`，再按 `lhg-sp-trust` skill 的人工评审清单过一遍脚本抓不到的。

## 流程

1. 先跑脚本：`python3 scripts/audit/shopify_audit.py --target <站点目录> --format text`（31 条规则：信任 9、产品页 9、结账 8、移动端 5）。
2. 发现分三级：**blocker**（必须修，发布前 hook 会拦截）、**warning**（修或写豁免理由）、**nit**（顺手修）。
3. 脚本之外，人工过一遍 lhg-sp-trust 第 6 节评审清单（首屏 3 秒测试、结账全流程走一遍、手机实测）。
4. blocker 清零才算过；改规则来过检算作弊。

## 用法

```
python3 scripts/audit/shopify_audit.py --target ./site --format json
python3 scripts/audit/shopify_audit.py --target ./site --format text --fail-on warning
```
