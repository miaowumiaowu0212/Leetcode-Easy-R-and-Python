import csv
import time
import requests

LEETCODE_HOME = "https://leetcode.com/"
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

def fetch_all_easy_questions(include_paid=True, limit=100, sleep_sec=0.2):
    session = requests.Session()

    # 关键：先访问主页拿到 csrftoken 等 cookie
    home_headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    r0 = session.get(LEETCODE_HOME, headers=home_headers, timeout=30)
    r0.raise_for_status()

    csrftoken = session.cookies.get("csrftoken", "")
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://leetcode.com/problemset/all/",
        "Origin": "https://leetcode.com",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-CSRFToken": csrftoken,
        "X-Requested-With": "XMLHttpRequest",
    }

    all_rows = []
    skip = 0
    total = None

    while True:
        variables = {
            "categorySlug": "",
            "limit": limit,
            "skip": skip,
            "filters": {
                "difficulty": "EASY",
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
        if total is not None and skip >= total:
            break
        time.sleep(sleep_sec)

    uniq = {r["id"]: r for r in all_rows}
    rows = sorted(uniq.values(), key=lambda x: int(x["id"]))
    return rows, (total or 0)

if __name__ == "__main__":
    rows, total_from_api = fetch_all_easy_questions(include_paid=True, limit=100)

    out_csv = "leetcode_easy_all.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "title", "difficulty", "acRate", "paidOnly", "url", "tags"])
        w.writeheader()
        w.writerows(rows)

    ids = [r["id"] for r in rows]
    print(f"Total EASY (api reported): {total_from_api}")
    print(f"Total EASY (exported rows): {len(rows)}")
    print("Problem IDs:")
    print(",".join(ids))
    print(f"\nSaved: {out_csv}")
