import csv
import time
import requests

LEETCODE_GRAPHQL = "https://leetcode.com/graphql/"

QUERY = r"""
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
  problemsetQuestionList: questionList(
    categorySlug: $categorySlug
    limit: $limit
    skip: $skip
    filters: $filters
  ) {
    total: totalNum
    questions: data {
      frontendQuestionId: questionFrontendId
      title
      titleSlug
      difficulty
      paidOnly: isPaidOnly
      acRate
      topicTags { slug name }
    }
  }
}
"""

def fetch_all_easy_questions(
    category_slug="",
    include_paid=True,
    limit=100,
    sleep_sec=0.2,
):
    all_rows = []
    skip = 0
    total = None

    session = requests.Session()
    headers = {
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com/problemset/all/",
        "User-Agent": "Mozilla/5.0",
    }

    while True:
        variables = {
            "categorySlug": category_slug,
            "limit": limit,
            "skip": skip,
            "filters": {
                "difficulty": "EASY",
                # 关键：不要再写 tags 过滤
            },
        }

        resp = session.post(
            LEETCODE_GRAPHQL,
            json={"query": QUERY, "variables": variables},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        if "errors" in data:
            raise RuntimeError(f"GraphQL errors: {data['errors']}")

        block = data["data"]["problemsetQuestionList"]
        if total is None:
            total = block["total"]

        questions = block["questions"] or []
        if not questions:
            break

        for q in questions:
            if (not include_paid) and q.get("paidOnly"):
                continue
            all_rows.append({
                "id": q["frontendQuestionId"],
                "title": q["title"],
                "difficulty": q["difficulty"],
                "acRate": q["acRate"],
                "paidOnly": q["paidOnly"],
                "url": f"https://leetcode.com/problems/{q['titleSlug']}/",
                "tags": ",".join([t["slug"] for t in (q.get("topicTags") or [])]),
            })

        skip += limit
        if skip >= total:
            break

        time.sleep(sleep_sec)

    # 题号去重 + 按题号排序
    uniq = {}
    for r in all_rows:
        uniq[r["id"]] = r
    rows = sorted(uniq.values(), key=lambda x: int(x["id"]))

    return rows

if __name__ == "__main__":
    rows = fetch_all_easy_questions(
        include_paid=True,  # 付费题也保留
        limit=100,
    )

    out_csv = "leetcode_easy_all.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "title", "difficulty", "acRate", "paidOnly", "url", "tags"])
        w.writeheader()
        w.writerows(rows)

    ids = [r["id"] for r in rows]
    print(f"Total EASY: {len(rows)}")
    print("Problem IDs:")
    print(",".join(ids))
    print(f"\nSaved: {out_csv}")
