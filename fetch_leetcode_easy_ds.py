import csv
import requests

API_ALL = "https://leetcode.com/api/problems/all/"

def fetch_all_easy_from_public_api(include_paid=True):
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Referer": "https://leetcode.com/problemset/all/",
    }

    resp = session.get(API_ALL, headers=headers, timeout=60)
    resp.raise_for_status()

    # Robust JSON parsing: LeetCode may return wrong content-type
    try:
        data = resp.json()
    except Exception:
        print("Failed to parse JSON.")
        print("Status:", resp.status_code)
        print("Content-Type:", resp.headers.get("content-type", ""))
        print(resp.text[:500])
        return []

    pairs = data.get("stat_status_pairs", [])
    rows = []

    # difficulty level: 1 easy, 2 medium, 3 hard
    for item in pairs:
        stat = item.get("stat", {})
        diff = item.get("difficulty", {}) or {}
        if diff.get("level") != 1:
            continue

        paid_only = bool(item.get("paid_only", False))
        if (not include_paid) and paid_only:
            continue

        qid = stat.get("frontend_question_id")
        slug = stat.get("question__title_slug")
        title = stat.get("question__title")

        rows.append({
            "id": qid,
            "title": title,
            "difficulty": "EASY",
            "paidOnly": paid_only,
            "url": f"https://leetcode.com/problems/{slug}/" if slug else "",
        })

    rows = [r for r in rows if r.get("id") is not None]
    rows.sort(key=lambda x: int(x["id"]))
    return rows

if __name__ == "__main__":
    rows = fetch_all_easy_from_public_api(include_paid=True)

    out_csv = "leetcode_easy_all.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["id", "title", "difficulty", "paidOnly", "url"]
        )
        w.writeheader()
        w.writerows(rows)

    ids = [str(r["id"]) for r in rows]
    print(f"Total EASY (exported rows): {len(rows)}")
    print("Saved:", out_csv)
