import csv
import re
from typing import Dict, List, Pattern

RAW_CSV = "leetcode_easy_all.csv"   # 你已经生成的全量 EASY（不动它）
OUT_CSV = "leetcode_easy_ds.csv"    # 新生成的 DS/统计聚焦子集

# 至少命中多少个 focus tag 才收录到子集。1 表示命中任意一个就收录。
MIN_TAGS = 1

# 如果你想强制包含某些题（即使标题关键词不命中），可以把题号加进来；
# 你说不想手动找题号，所以默认留空即可。
INCLUDE_IDS = set()

TAG_RULES = {
    # 概率统计 / 分布 / 抽样 / 指标口径
    "stats-prob": [
        r"\bprob\b", r"\bprobability\b", r"\brandom\b",
        r"\bexpected\b", r"\bexpectation\b",
        r"\bmean\b", r"\bmedian\b", r"\bmode\b", r"\baverage\b",
        r"\bpercent\b", r"\bpercentage\b", r"\brate\b", r"\bratio\b",
        r"\bvariance\b", r"standard deviation", r"\bstd\b",
        r"\bdistribution\b", r"\bsample\b", r"\bsampling\b",
        r"\bconfidence\b", r"\binterval\b",
    ],

    # 数据清洗 / 数据质量 / 规则校验
    "data-cleaning": [
        r"\bduplicate\b", r"\bduplicates\b",
        r"\bremove\b", r"\bdelete\b", r"\btrim\b",
        r"\bvalid\b", r"\binvalid\b",
        r"\bunique\b", r"\bdistinct\b",
        r"\bmissing\b", r"\bnull\b", r"\bempty\b",
        r"\bformat\b", r"\bemail\b", r"\bdate\b",
        r"\bfix\b", r"\breplace\b",
    ],

    # 聚合 / 分组统计 / 排名 / Top-K（很像 SQL/pandas groupby）
    "agg-ranking": [
        r"\brank\b", r"\btop\b", r"\bkth\b", r"\bnth\b",
        r"\bmost\b", r"\bleast\b", r"\bmaximum\b", r"\bminimum\b",
        r"\bcount\b", r"\bnumber of\b", r"\bfrequency\b",
        r"\btotal\b", r"\bsum\b",
        r"\bhighest\b", r"\blowest\b", r"\bsecond\b", r"\bthird\b",
        r"\bgroup\b", r"\bcategory\b",
    ],

    # 时间序列 / 连续段 / 滑动窗口 / 按天汇总
    "time-series": [
        r"\bdaily\b", r"\bweekly\b", r"\bmonthly\b",
        r"\bconsecutive\b", r"\bcontinuous\b",
        r"moving average", r"\brolling\b", r"\bwindow\b",
        r"\baverage time\b", r"\btime spent\b", r"\bduration\b",
        r"\bday\b", r"\bdate\b", r"\byear\b", r"\bmonth\b",
    ],

    # KPI/业务指标常见措辞（acceptance rate / conversion / bonus / score）
    "kpi-metrics": [
        r"\brate\b", r"\bacceptance\b", r"\bconversion\b",
        r"\bpercentage\b", r"\bpercent\b",
        r"\baverage\b", r"\bmean\b", r"\btotal\b",
        r"\bscore\b", r"\bbonus\b",
    ],

    # 表格/业务数据语境（更像 DS 真实数据：customer, salary, department...）
    "tabular-business": [
        r"\bemployee\b", r"\bcustomer\b", r"\buser\b", r"\bclient\b",
        r"\bsalary\b", r"\bdepartment\b", r"\btransaction\b",
        r"\border\b", r"\bsales\b", r"\bproduct\b",
        r"\bvisit\b", r"\bviews\b", r"\bclick\b",
        r"\baccount\b", r"\bid\b", r"\bidentifier\b",
    ],

    # 轻量数学/数值（面试基础题常出现）
    "basic-math": [
        r"\bsqrt\b", r"\bprime\b", r"\bpower\b",
        r"\broman\b", r"\bbinary\b",
        r"\badd\b", r"\bplus\b", r"\bsubtract\b", r"\bdivide\b",
        r"\bpalindrome\b",
    ],
}

def compile_rules(tag_rules: Dict[str, List[str]]) -> Dict[str, List[Pattern]]:
    compiled: Dict[str, List[Pattern]] = {}
    for tag, patterns in tag_rules.items():
        compiled[tag] = [re.compile(p, re.IGNORECASE) for p in patterns]
    return compiled

def tag_title(title: str, compiled_rules: Dict[str, List[Pattern]]) -> List[str]:
    tags: List[str] = []
    for tag, regs in compiled_rules.items():
        for rgx in regs:
            if rgx.search(title):
                tags.append(tag)
                break
    return tags

def main() -> None:
    compiled_rules = compile_rules(TAG_RULES)

    with open(RAW_CSV, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    out_rows = []
    for r in raw_rows:
        qid = str(r.get("id", "")).strip()
        title = (r.get("title") or "").strip()

        tags = tag_title(title, compiled_rules)

        keep = (qid in INCLUDE_IDS) or (len(tags) >= MIN_TAGS)
        if not keep:
            continue

        out_rows.append({
            "id": qid,
            "title": title,
            "difficulty": r.get("difficulty", ""),
            "paidOnly": r.get("paidOnly", ""),
            "url": r.get("url", ""),
            "focus_tags": ",".join(tags),
            "done": "",   # 导入 Google Sheets 后把这一列设置为 checkbox
            "note": "",   # 你可以写：思路、坑点、复盘
        })

    def sort_key(x):
        return int(x["id"]) if x["id"].isdigit() else 10**18

    out_rows.sort(key=sort_key)

    with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
        fieldnames = ["id", "title", "difficulty", "paidOnly", "url", "focus_tags", "done", "note"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print("Raw rows:", len(raw_rows))
    print("DS-focused rows:", len(out_rows))
    print("Saved:", OUT_CSV)
    if out_rows:
        print("Example row:", out_rows[0])

if __name__ == "__main__":
    main()
