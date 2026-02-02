import csv
import time
import requests

API_ALL = "https://leetcode.com/api/problems/all/"

def fetch_all_easy_from_public_api(include_paid=True, sleep_sec=0.2):
    """
    Pull all problems from LeetCode public JSON endpoint,
    then filter difficulty == EASY locally.
    """
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json,text/plain,*/*",
        "Referer": "https://leetcode.com/problemset/all/",
    }

    # GET the full dataset
    resp = session.get(API_ALL, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    pairs = data.get("stat_status_pairs", [])
    rows = []

    # Difficulty mapping used by this endpoint: 1 easy, 2 medium, 3 hard
    for item in pairs:
        stat = item.get("stat", {})
        diff = item.get("difficulty", {}) or {}
        level = diff.get("level", None)

        if level != 1:
            continue

        paid_only = bool(item.get("paid_only", False))
        if (not include_paid) and paid_only:
            continue

        qid = stat.get("frontend_question_id")
        slug = stat.get("question__title_slug")
        title = stat.get("question__title")

        topic_tags = item.get("topic_tags", []) or []
        tag_slugs = ",".join([t.get("slug", "") for t in topic_tags if t.get("slug")])

        rows.append({
            "id": qid,
            "title": title,
            "difficulty": "EASY",
            "paidOnly": paid_only,
            "url": f"https://leetcode.com/problems/{slug}/" if slug else "",
            "tags": tag_slugs,
        })

    # Sort by numeric id
    rows = [r for r in rows if r.get("id") is not None]
    rows.sort(key=lambda x: int(x["id"]))

    # Gentle sleep (not required, but keeps behavior polite if you extend this later)
    time.sleep(sleep_sec)

    return rows

if __name__ == "__main__":
    rows = fetch_all_easy_from_public_api(include_paid=True)

    out_csv = "leetcode_easy_all.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["id", "title", "difficulty", "paidOnly", "url", "tags"]
        )
        w.writeheader()
        w.writerows(rows)

    ids = [str(r["id"]) for r in rows]
    print(f"Total EASY (exported rows): {len(rows)}")
    print("Problem IDs:")
    print(",".join(ids))
    print(f"\nSaved: {out_csv}")
