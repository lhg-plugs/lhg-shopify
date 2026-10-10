#!/usr/bin/env python3
"""lhg-shopify 硬门：发布站点前校验 site_spec.json 与信任元素完整性。

触发：PreToolUse / Bash。脚本先判断本次 Bash 命令是否为"发布"
（deploy / publish / wrangler deploy / vercel deploy / shopify 等发布意图），
不是则 0 开销直接放行；是则查找并校验交付目录下的 site_spec.json。

校验项：JSON 合法、必需页面齐全（首页/产品页/购物车/结账页）、
信任四件套声明齐全（退换货政策/联系方式/支付标识/隐私政策）。

逃生方式（按推荐度排序）：
  1. 补齐缺项后重新发布（推荐）。
  2. 紧急情况：LHG_SHOPIFY_HOOKS_OFF=1 <发布命令>（单次豁免本次 hook）。
  3. /plugin disable lhg-shopify（整个插件停用，hooks 不再触发）。

设计原则：脚本内部出错时 fail-open 直接放行，不因插件自身故障骚扰用户；
找不到 site_spec.json 时只做提醒式放行（additionalContext），不拦截——
因为用户可能在发布与本插件无关的项目。零第三方依赖。
"""

import json
import os
import re
import sys

PUBLISH_RE = re.compile(
    r"(?<![\w-])(deploy|publish|release)\b|wrangler\s+deploy|vercel(\s+deploy)?\b|"
    r"netlify\s+deploy|shopify(\s+theme\s+push|\s+deploy)?\b",
    re.I,
)
SPEC_NAMES = ("site_spec.json", "site-spec.json")
REQUIRED_PAGES = ("home", "product", "cart", "checkout")
REQUIRED_TRUST = ("refund_policy", "contact", "payment_badges", "privacy_policy")


def find_spec(project_dir):
    for name in SPEC_NAMES:
        p = os.path.join(project_dir, name)
        if os.path.isfile(p):
            return p
    cands = [f for f in os.listdir(project_dir)
             if f.endswith(".site-spec.json")
             and os.path.isfile(os.path.join(project_dir, f))]
    if len(cands) == 1:
        return os.path.join(project_dir, cands[0])
    return None


def validate_spec(path):
    """返回 (ok, [问题列表])。"""
    problems = []
    try:
        with open(path, encoding="utf-8") as fh:
            spec = json.load(fh)
    except Exception as e:
        return False, ["site_spec 不是合法 JSON：%s" % e]
    pages = spec.get("pages") or {}
    for pg in REQUIRED_PAGES:
        if pg not in pages:
            problems.append("必需页面缺失：%s" % pg)
    trust = spec.get("trust_elements") or {}
    for t in REQUIRED_TRUST:
        if not trust.get(t):
            problems.append("信任元素缺失：%s" % t)
    return (not problems), problems


def main() -> int:
    if os.environ.get("LHG_SHOPIFY_HOOKS_OFF") == "1":
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # 输入解析失败：fail-open

    tool_input = payload.get("tool_input", {}) or {}
    command = tool_input.get("command", "") or ""

    if not PUBLISH_RE.search(command):
        return 0

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    spec_path = find_spec(project_dir)

    if spec_path is None:
        out = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": (
                    "提醒：本次发布未在当前目录找到 site_spec.json。"
                    "如果是用 lhg-shopify 建的独立站，请先定施工图并跑 "
                    "/lhg-shopify:shopify-audit，否则跳过此提醒。"
                ),
            }
        }
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
        return 0

    try:
        ok, problems = validate_spec(spec_path)
    except Exception:
        return 0  # 校验自身出错：fail-open

    if ok:
        return 0

    lines = [
        "发布被 lhg-shopify 硬门拦截：site_spec 校验发现 %d 个缺项，补齐再发布。"
        % len(problems),
        "spec 文件：%s" % spec_path,
        "",
    ]
    for p in problems[:10]:
        lines.append("- " + p)
    if len(problems) > 10:
        lines.append("…另有 %d 个" % (len(problems) - 10))
    lines += [
        "",
        "修复方式：按 lhg-sp-plan 第 2 节补齐页面与信任元素后重新发布；",
        "紧急豁免（单次）：LHG_SHOPIFY_HOOKS_OFF=1 <发布命令>",
    ]
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "\n".join(lines),
        }
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
