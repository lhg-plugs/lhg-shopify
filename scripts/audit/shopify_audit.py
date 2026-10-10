#!/usr/bin/env python3
"""lhg-shopify 确定性上线审计：35 条规则，零第三方依赖。

扫描站点交付目录（site_spec.json + pages/*.html），输出 JSON 与人类可读
报告；有 blocker 时以 exit code 2 退出（供 hooks 与 CI 使用）。

用法：
    python3 shopify_audit.py --target <站点目录> [--format json|text]
                             [--fail-on blocker|warning|nit]

规则文案均为本项目原创（"开箱即用建站样板"的方法论思路受
wasp-lang/open-saas 等 MIT 开源项目启发，未复制任何第三方原文与代码；
详见仓库 ATTRIBUTION.md）。
"""

import argparse
import json
import os
import re
import sys

VERSION = "1.0.0"
TOOL = "lhg-shopify/shopify-audit"

SKIP_DIRS = {".git", "__pycache__", "node_modules", "dist", "build", ".bak"}

REQUIRED_PAGES = ("home", "product", "cart", "checkout")
REQUIRED_TRUST = ("refund_policy", "contact", "payment_badges", "privacy_policy")


class Finding:
    __slots__ = ("rule_id", "severity", "category", "title", "file", "line",
                 "snippet", "detail")

    def __init__(self, rule_id, severity, category, title, file, line,
                 snippet, detail):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
        self.title = title
        self.file = file
        self.line = line
        self.snippet = snippet
        self.detail = detail

    def to_dict(self):
        return {
            "rule_id": self.rule_id, "severity": self.severity,
            "category": self.category, "title": self.title,
            "file": self.file, "line": self.line,
            "snippet": self.snippet, "detail": self.detail,
        }


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except UnicodeDecodeError:
        return None
    except OSError:
        return ""


def collect(target):
    specs, htmls = [], []
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            p = os.path.join(root, f)
            fl = f.lower()
            if fl in ("site_spec.json", "site-spec.json") or fl.endswith(".site-spec.json"):
                specs.append(p)
            elif fl.endswith((".html", ".htm")):
                htmls.append(p)
    return {"specs": sorted(specs), "htmls": sorted(htmls)}


def html_files_by_kind(htmls):
    """按文件名粗分页面类型。"""
    prod = [p for p in htmls if "product" in os.path.basename(p).lower()]
    check = [p for p in htmls if "checkout" in os.path.basename(p).lower()]
    if not prod:  # 兜底：含加购按钮的页面当产品页
        prod = [p for p in htmls if "add-to-cart" in (read_text(p) or "").lower()]
    return prod, check


# ---------------------------------------------------------------- 规则注册表
RULES = []
_RULE_BY_ID = {}


def rule(rule_id, severity, category, title, detail):
    def deco(fn):
        r = {"id": rule_id, "severity": severity, "category": category,
             "title": title, "detail": detail}
        _RULE_BY_ID[rule_id] = r
        r["check"] = fn
        RULES.append(r)
        return fn
    return deco


def F(rule_id, path, snippet="", detail=""):
    r = _RULE_BY_ID[rule_id]
    return Finding(rule_id, r["severity"], r["category"], r["title"],
                   path, 0, snippet, detail or r["detail"])


# ================================================================ SPEC（4）
@rule("SPEC-FILE-001", "blocker", "spec", "site_spec.json 存在且为合法 JSON",
      "站点施工图缺失或不是合法 JSON：后续所有检查都无从谈起。")
def _spec_file(ctx):
    specs = ctx["specs"]
    if not specs:
        yield F("SPEC-FILE-001", ctx["target"], "",
                "未找到 site_spec.json：先跑 /lhg-shopify:shopify 定施工图。")
        return
    if len(specs) > 1:
        yield F("SPEC-FILE-001", specs[1], "",
                "发现多个 site_spec.json（%d 个），只保留一个。" % len(specs))
    try:
        json.loads(read_text(specs[0]) or "")
    except Exception as e:
        yield F("SPEC-FILE-001", specs[0], "", "site_spec.json 解析失败：%s" % e)


@rule("SPEC-NAME-001", "warning", "spec", "店铺名称已声明",
      "店铺连名字都没有，用户不知道这是谁的店。")
def _spec_name(ctx):
    spec = ctx["spec"]
    if not spec:
        return
    if not (spec.get("store_name") or "").strip():
        yield F("SPEC-NAME-001", ctx["spec_path"])


@rule("SPEC-PAGE-001", "blocker", "spec", "必需页面齐全（首页/产品页/购物车/结账页）",
      "缺任何一个页面，购物链路就断了：用户加不了购、结不了账。")
def _spec_page(ctx):
    spec = ctx["spec"]
    if not spec:
        return
    pages = spec.get("pages") or {}
    for pg in REQUIRED_PAGES:
        if pg not in pages:
            yield F("SPEC-PAGE-001", ctx["spec_path"], "",
                    "必需页面缺失：%s（需声明 home/product/cart/checkout）" % pg)


@rule("SPEC-TRUST-001", "blocker", "spec", "信任四件套已声明",
      "退换货政策/联系方式/支付标识/隐私政策缺一件，转化率与合规都翻车。")
def _spec_trust(ctx):
    spec = ctx["spec"]
    if not spec:
        return
    trust = spec.get("trust_elements") or {}
    for t in REQUIRED_TRUST:
        if not trust.get(t):
            yield F("SPEC-TRUST-001", ctx["spec_path"], "",
                    "信任元素缺失：%s（refund_policy/contact/payment_badges/privacy_policy）" % t)


# ================================================================ TRUST（9）
@rule("TRUST-REFUND-001", "blocker", "trust", "退换货政策页存在且写明退货天数",
      "没有白纸黑字的退换货政策，用户不敢下单；只写\"可退换\"不写天数等于没写。")
def _trust_refund(ctx):
    pages = [p for p in ctx["htmls"]
             if "refund" in os.path.basename(p).lower()
             or "return" in os.path.basename(p).lower()]
    if not pages:
        yield F("TRUST-REFUND-001", ctx["target"], "",
                "未找到退换货政策页（文件名应含 refund/return）。")
        return
    text = read_text(pages[0]) or ""
    if not re.search(r"\d+\s*(天|days?)", text, re.I):
        yield F("TRUST-REFUND-001", pages[0], "",
                "退换货政策未写明具体天数（如 7 天/30 天无理由）。")


@rule("TRUST-REFUND-002", "warning", "trust", "退换货政策写明退货联系方式",
      "政策里不写\"找谁退、怎么退\"，用户真要退时会直接给差评。")
def _trust_refund2(ctx):
    pages = [p for p in ctx["htmls"]
             if "refund" in os.path.basename(p).lower()]
    if not pages:
        return
    text = (read_text(pages[0]) or "").lower()
    if ("@" not in text) and ("客服" not in text) and ("support" not in text):
        yield F("TRUST-REFUND-002", pages[0])


@rule("TRUST-CONTACT-001", "blocker", "trust", "联系方式存在（邮箱）",
      "全站找不到一个邮箱，用户有问题只能干瞪眼，信任直接归零。")
def _trust_contact(ctx):
    all_text = " ".join(read_text(p) or "" for p in ctx["htmls"])
    if not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", all_text):
        yield F("TRUST-CONTACT-001", ctx["target"], "",
                "全站未发现邮箱地址：页脚或联系页至少留一个。")


@rule("TRUST-CONTACT-002", "warning", "trust", "联系方式有第二通道（电话/地址）",
      "只有一个邮箱的客服通道太单薄，电话或地址至少再有一个。")
def _trust_contact2(ctx):
    all_text = " ".join(read_text(p) or "" for p in ctx["htmls"])
    has_phone = bool(re.search(r"\+?\d[\d\s-]{6,}\d", all_text))
    has_addr = any(w in all_text for w in ("地址", "address", "路", "号", "Street", "Ave"))
    if not (has_phone or has_addr):
        yield F("TRUST-CONTACT-002", ctx["target"])


@rule("TRUST-PAY-001", "blocker", "trust", "支付标识展示（≥1 种支付品牌）",
      "结账页看不到 Visa/Mastercard/PayPal 等标识，用户不敢输卡号。")
def _trust_pay(ctx):
    _, checks = html_files_by_kind(ctx["htmls"])
    targets = checks or ctx["htmls"]
    brands = ("visa", "mastercard", "paypal", "apple pay", "google pay",
              "stripe", "支付宝", "微信支付")
    for p in targets:
        text = (read_text(p) or "").lower()
        if any(b in text for b in brands):
            return
    yield F("TRUST-PAY-001", targets[0] if targets else ctx["target"], "",
            "结账页未发现任何支付品牌标识。")


@rule("TRUST-PRIVACY-001", "blocker", "trust", "隐私政策页存在",
      "收用户地址电话却没有隐私政策，合规与信任双翻车。")
def _trust_privacy(ctx):
    pages = [p for p in ctx["htmls"]
             if "privacy" in os.path.basename(p).lower()]
    if not pages:
        yield F("TRUST-PRIVACY-001", ctx["target"], "",
                "未找到隐私政策页（文件名应含 privacy）。")


@rule("TRUST-TERMS-001", "warning", "trust", "服务条款页存在",
      "服务条款是纠纷时的护身符，上线前补上。")
def _trust_terms(ctx):
    pages = [p for p in ctx["htmls"]
             if "terms" in os.path.basename(p).lower()]
    if not pages:
        yield F("TRUST-TERMS-001", ctx["target"], "",
                "未找到服务条款页（文件名应含 terms）。")


@rule("TRUST-ABOUT-001", "nit", "trust", "关于我们页存在",
      "讲清楚\"我们是谁\"，新店信任加分项。")
def _trust_about(ctx):
    pages = [p for p in ctx["htmls"]
             if "about" in os.path.basename(p).lower()]
    if not pages:
        yield F("TRUST-ABOUT-001", ctx["target"])


@rule("TRUST-HTTPS-001", "warning", "trust", "spec 声明启用 HTTPS",
      "结账页没有 HTTPS 等于裸奔，spec 里 https 必须为 true。")
def _trust_https(ctx):
    spec = ctx["spec"]
    if not spec:
        return
    if spec.get("https") is not True:
        yield F("TRUST-HTTPS-001", ctx["spec_path"])


# ================================================================ PROD（9）
@rule("PROD-IMG-001", "warning", "product", "产品页图片 ≥3 张",
      "只有 1 张图的商品页，用户看不到细节，转化率打对折。")
def _prod_img(ctx):
    prods, _ = html_files_by_kind(ctx["htmls"])
    for p in prods:
        text = read_text(p) or ""
        n = len(re.findall(r"<img\b", text, re.I))
        if n < 3:
            yield F("PROD-IMG-001", p, "", "仅 %d 张产品图，要求 ≥3 张。" % n)


@rule("PROD-PRICE-001", "blocker", "product", "产品页展示价格",
      "没有价格的产品页等于没开张：用户第一眼就要看到多少钱。")
def _prod_price(ctx):
    prods, _ = html_files_by_kind(ctx["htmls"])
    for p in prods:
        text = read_text(p) or ""
        if not re.search(r"(¥|\$|€|£|USD|CNY)\s*\d", text):
            yield F("PROD-PRICE-001", p, "", "未发现价格（需含货币符号与数字）。")


@rule("PROD-ATC-001", "blocker", "product", "产品页有加购/购买按钮",
      "连加购按钮都没有的页面，流量来了也接不住。")
def _prod_atc(ctx):
    prods, _ = html_files_by_kind(ctx["htmls"])
    for p in prods:
        text = (read_text(p) or "").lower()
        if not any(w in text for w in ("add-to-cart", "add to cart", "加入购物车",
                                       "立即购买", "buy now")):
            yield F("PROD-ATC-001", p)


@rule("PROD-REVIEW-001", "warning", "product", "产品页有评价区",
      "零评价的商品页信任度垫底：至少留出评价区位置，上线后持续填充。")
def _prod_review(ctx):
    prods, _ = html_files_by_kind(ctx["htmls"])
    for p in prods:
        text = (read_text(p) or "").lower()
        if not any(w in text for w in ("review", "评价", "买家秀", "testimonial")):
            yield F("PROD-REVIEW-001", p)


@rule("PROD-FAQ-001", "warning", "product", "产品页有 FAQ",
      "常见问题前置回答，能挡掉一半的客服咨询与退货。")
def _prod_faq(ctx):
    prods, _ = html_files_by_kind(ctx["htmls"])
    for p in prods:
        text = (read_text(p) or "").lower()
        if "faq" not in text and "常见问题" not in text:
            yield F("PROD-FAQ-001", p)


@rule("PROD-DESC-001", "warning", "product", "产品描述 ≥100 字",
      "描述太短等于没介绍：卖点、规格、使用场景至少讲清楚。")
def _prod_desc(ctx):
    prods, _ = html_files_by_kind(ctx["htmls"])
    for p in prods:
        text = re.sub(r"<[^>]+>", " ", read_text(p) or "")
        text = re.sub(r"\s+", "", text)
        if len(text) < 100:
            yield F("PROD-DESC-001", p, "",
                    "正文仅约 %d 字，要求 ≥100 字。" % len(text))


@rule("PROD-TRUST-001", "warning", "product", "产品页有信任徽章（包邮/退换/正品）",
      "加购按钮旁边的信任徽章是临门一脚：包邮、退换、正品至少占一个。")
def _prod_trust(ctx):
    prods, _ = html_files_by_kind(ctx["htmls"])
    for p in prods:
        text = read_text(p) or ""
        if not any(w in text for w in ("包邮", "退换", "正品", "保修",
                                       "free shipping", "guarantee", "authentic")):
            yield F("PROD-TRUST-001", p)


@rule("PROD-SHIPPING-001", "warning", "product", "产品页说明物流/运费",
      "不写运费与时效，用户会在结账页被\"运费刺客\"吓跑。")
def _prod_shipping(ctx):
    prods, _ = html_files_by_kind(ctx["htmls"])
    for p in prods:
        text = read_text(p) or ""
        if not any(w in text for w in ("运费", "物流", "发货", "配送",
                                       "shipping", "delivery")):
            yield F("PROD-SHIPPING-001", p)


@rule("PROD-SEO-001", "nit", "product", "产品页有 <title>",
      "没有标题的页面，搜索引擎与分享卡片都拿不到名字。")
def _prod_seo(ctx):
    prods, _ = html_files_by_kind(ctx["htmls"])
    for p in prods:
        text = read_text(p) or ""
        if not re.search(r"<title>[^<]{3,}</title>", text, re.I):
            yield F("PROD-SEO-001", p)


# ================================================================ CHECK（8）
@rule("CHECK-GUEST-001", "blocker", "checkout", "支持游客结账",
      "强制注册是结账页第一杀手：不登录也能买，是底线。")
def _check_guest(ctx):
    _, checks = html_files_by_kind(ctx["htmls"])
    for p in checks:
        text = (read_text(p) or "").lower()
        if not any(w in text for w in ("guest", "游客", "无需注册", "免注册",
                                       "continue as guest")):
            yield F("CHECK-GUEST-001", p)


@rule("CHECK-STEPS-001", "warning", "checkout", "结账步骤有进度指示",
      "用户不知道\"还剩几步\"就会焦虑：步骤条是定心丸。")
def _check_steps(ctx):
    _, checks = html_files_by_kind(ctx["htmls"])
    for p in checks:
        text = read_text(p) or ""
        has_steps = bool(re.search(r"(step|步骤)\s*[1-4]", text, re.I))
        has_multi = len(re.findall(r"<li[^>]*>.*?(信息|配送|支付|确认).*?</li>",
                                   text, re.S | re.I)) >= 2
        if not (has_steps or has_multi):
            yield F("CHECK-STEPS-001", p)


@rule("CHECK-SUMMARY-001", "blocker", "checkout", "订单摘要常驻",
      "结账时看不到\"买了啥、花多少\"，用户会怀疑自己被多收钱。")
def _check_summary(ctx):
    _, checks = html_files_by_kind(ctx["htmls"])
    for p in checks:
        text = (read_text(p) or "").lower()
        if not any(w in text for w in ("order summary", "订单摘要", "小计",
                                       "subtotal", "总计", "total")):
            yield F("CHECK-SUMMARY-001", p)


@rule("CHECK-SHIPPING-001", "warning", "checkout", "配送方式可选择",
      "只有一种配送方式等于没得选：标准/加急至少给两个选项。")
def _check_shipping(ctx):
    _, checks = html_files_by_kind(ctx["htmls"])
    for p in checks:
        text = read_text(p) or ""
        opts = len(re.findall(r"<option|radio", text, re.I))
        if opts < 2 and "配送" not in text and "shipping method" not in text.lower():
            yield F("CHECK-SHIPPING-001", p, "",
                    "未发现多个配送选项。")


@rule("CHECK-PAYMETHOD-001", "warning", "checkout", "支付方式 ≥2 种",
      "只支持一种支付方式，会把用其他方式的用户直接送走。")
def _check_paymethod(ctx):
    _, checks = html_files_by_kind(ctx["htmls"])
    for p in checks:
        text = (read_text(p) or "").lower()
        brands = ("visa", "mastercard", "paypal", "apple pay", "支付宝", "微信支付")
        n = sum(1 for b in brands if b in text)
        if n < 2:
            yield F("CHECK-PAYMETHOD-001", p, "",
                    "仅发现 %d 种支付方式，要求 ≥2 种。" % n)


@rule("CHECK-BACK-001", "warning", "checkout", "每步可回退",
      "结账页没有回退按钮，填错一步就得重来，用户直接弃单。")
def _check_back(ctx):
    _, checks = html_files_by_kind(ctx["htmls"])
    for p in checks:
        text = (read_text(p) or "").lower()
        if not any(w in text for w in ("返回", "back", "上一步", "previous")):
            yield F("CHECK-BACK-001", p)


@rule("CHECK-FIELDS-001", "warning", "checkout", "必填字段有明确标签",
      "姓名/地址/电话连标签都没有，用户不知道该填什么。")
def _check_fields(ctx):
    _, checks = html_files_by_kind(ctx["htmls"])
    for p in checks:
        text = read_text(p) or ""
        labels = sum(1 for w in ("姓名", "地址", "电话", "name", "address", "phone")
                     if w in text.lower())
        if labels < 2:
            yield F("CHECK-FIELDS-001", p, "",
                    "仅发现 %d 类字段标签，要求姓名/地址/电话至少其二。" % labels)


@rule("CHECK-SECURE-001", "nit", "checkout", "安全支付提示",
      "\"安全支付\"四个字不值钱，但没有它用户会多想一秒。")
def _check_secure(ctx):
    _, checks = html_files_by_kind(ctx["htmls"])
    for p in checks:
        text = (read_text(p) or "").lower()
        if not any(w in text for w in ("安全支付", "secure", "ssl", "加密")):
            yield F("CHECK-SECURE-001", p)


# ================================================================ MOB（5）
@rule("MOB-VIEWPORT-001", "blocker", "mobile", "所有页面有 viewport meta",
      "没有 viewport 的页面在手机上会缩成一团：移动流量直接作废。")
def _mob_viewport(ctx):
    for p in ctx["htmls"]:
        text = read_text(p) or ""
        if not re.search(r'<meta[^>]+name=["\']viewport["\']', text, re.I):
            yield F("MOB-VIEWPORT-001", p, "", "缺少 viewport meta 标签。")


@rule("MOB-FONTSIZE-001", "warning", "mobile", "无过小字号（内联 <12px）",
      "手机上小于 12px 的字基本看不清：放大或删掉。")
def _mob_fontsize(ctx):
    for p in ctx["htmls"]:
        text = read_text(p) or ""
        for m in re.finditer(r"font-size\s*:\s*(\d+(?:\.\d+)?)px", text, re.I):
            if float(m.group(1)) < 12:
                yield F("MOB-FONTSIZE-001", p, m.group(0)[:40])
                break


@rule("MOB-FIXEDWIDTH-001", "warning", "mobile", "无桌面端固定宽度（内联 ≥960px）",
      "写死的 1200px 宽度在手机上会撑出横向滚动条：改用自适应。")
def _mob_fixedwidth(ctx):
    for p in ctx["htmls"]:
        text = read_text(p) or ""
        for m in re.finditer(r"width\s*:\s*(\d+)px", text, re.I):
            if int(m.group(1)) >= 960:
                yield F("MOB-FIXEDWIDTH-001", p, m.group(0)[:40])
                break


@rule("MOB-IMGALT-001", "nit", "mobile", "图片有 alt",
      "图片加载失败时 alt 是最后的体面，也利于搜索。")
def _mob_imgalt(ctx):
    for p in ctx["htmls"]:
        text = read_text(p) or ""
        imgs = re.findall(r"<img\b[^>]*>", text, re.I)
        if imgs and any("alt=" not in i.lower() for i in imgs):
            yield F("MOB-IMGALT-001", p, "",
                    "%d 张图片中有缺 alt 的。" % len(imgs))
            break


@rule("MOB-LANG-001", "nit", "mobile", "html 声明 lang",
      "lang 声明影响读屏软件与翻译：一行代码的事。")
def _mob_lang(ctx):
    for p in ctx["htmls"]:
        text = read_text(p) or ""
        if not re.search(r"<html[^>]+lang=", text, re.I):
            yield F("MOB-LANG-001", p)


# ---------------------------------------------------------------- 主流程
def build_ctx(target):
    files = collect(target)
    spec = None
    spec_path = files["specs"][0] if files["specs"] else None
    if spec_path:
        try:
            spec = json.loads(read_text(spec_path) or "")
        except Exception:
            spec = None
    return {"target": target, "specs": files["specs"], "htmls": files["htmls"],
            "spec": spec, "spec_path": spec_path or target}


def run_audit(target):
    ctx = build_ctx(target)
    findings = []
    for r in RULES:
        try:
            for f in r["check"](ctx):
                findings.append(f)
        except Exception as e:  # 单规则出错不炸整轮
            findings.append(Finding(r["id"], "warning", r["category"],
                                    r["title"], target, 0, "",
                                    "规则执行异常（已降级）：%s" % e))
    return findings


def summarize(findings):
    s = {"blocker": 0, "warning": 0, "nit": 0, "rules_run": len(RULES),
         "rules_hit": len({_RULE_BY_ID[f.rule_id]["id"] for f in findings})}
    for f in findings:
        if f.severity in s:
            s[f.severity] += 1
    return s


def main(argv=None):
    ap = argparse.ArgumentParser(description="lhg-shopify 上线审计（35 条规则）")
    ap.add_argument("--target", required=True)
    ap.add_argument("--format", choices=("json", "text"), default="text")
    ap.add_argument("--fail-on", choices=("blocker", "warning", "nit"),
                    default="blocker")
    args = ap.parse_args(argv)

    findings = run_audit(args.target)
    summary = summarize(findings)

    if args.format == "json":
        print(json.dumps({"tool": TOOL, "version": VERSION, "target": args.target,
                          "summary": summary,
                          "findings": [f.to_dict() for f in findings]},
                         ensure_ascii=False, indent=2))
    else:
        print("lhg-shopify 上线审计 v%s  target=%s" % (VERSION, args.target))
        print("blocker=%d warning=%d nit=%d  规则 %d/%d 命中"
              % (summary["blocker"], summary["warning"], summary["nit"],
                 summary["rules_hit"], summary["rules_run"]))
        for f in findings:
            print("[%s] %s %s\n      %s" % (f.severity.upper(), f.rule_id,
                                            f.title, f.file))

    order = {"blocker": 0, "warning": 1, "nit": 2}
    worst = min([order[f.severity] for f in findings], default=3)
    if worst <= order[args.fail_on]:
        return 2 if worst == 0 else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
