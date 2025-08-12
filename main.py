import json
import requests
from time import sleep
from pathlib import Path
from famgz_utils import json_, Cookies

src_dir = Path(__file__).parent.resolve()
data_dir = src_dir / "data"
cookies_dir = src_dir / "cookies"

data_dir.mkdir(exist_ok=True)
cookies_dir.mkdir(exist_ok=True)


def get_transactions():
    file_path = data_dir / "coin_transactions.json"
    if not file_path.exists():
        json_(file_path, create_file=True)
    file = json_(file_path)
    return file


def main():
    transactions = get_transactions()
    previous_transactions_qty = len(transactions.keys())
    COOKIE_KEY = "SPC_EC"
    _cookies = Cookies(cookies_dir)
    _cookies.check_expired_cookies()
    cookies = _cookies.get_cookies()
    cookies = {COOKIE_KEY: cookies[COOKIE_KEY]}
    per_type = {}
    total = {"+": 0, "-": 0}
    infos = {"name": [], "content": []}
    LIMIT = 1000
    items_count = 0
    offset = 0
    while True:
        params = {
            "type": "all",
            "offset": offset,
            "limit": LIMIT,
        }
        print(f"Requesting offset {offset}", end=" -> ")
        response = requests.get(
            "https://shopee.com.br/api/v4/coin/get_user_coin_transaction_list",
            params=params,
            cookies=cookies,
        )
        data = response.json()
        items = data["items"]
        print(f"{len(items)} items")
        if not items:
            break
        items_count += len(items)
        parsed_items = {str(item["id"]): item for item in items}
        transactions.update(parsed_items)
        for item in items:
            reason = item["info"]["reason"]
            name = item["name"].strip()
            content = item["content"].strip()
            if name not in infos["name"]:
                infos["name"].append(name)
            if content not in infos["content"]:
                infos["content"].append(content)
            amount = int(item["coin_amount"].replace(".", ""))
            key = reason or content or name
            key = key.strip()
            per_type.setdefault(key, {"+": 0, "-": 0})
            if amount > 0:
                per_type[key]["+"] += amount
                total["+"] += amount
            else:
                per_type[key]["-"] += amount
                total["-"] += amount
        offset += LIMIT
        sleep(response.elapsed.total_seconds())

    new_transactions_qty = len(transactions.keys()) - previous_transactions_qty
    print(f"{items_count} transactions found")
    print(f"{new_transactions_qty} new transactions saved")
    print(f"\n{total['+']} coins earned")
    print(f"{total['-']} coins redeemed")
    print(f"{total['+'] - abs(total['-'])} coins available")

    per_type = dict(sorted(per_type.items(), key=lambda x: x[1]["+"], reverse=True))
    summary = {"total": total, "per_type": per_type}
    json_(
        data_dir / "summary.json",
        summary,
        create_file=True,
        ensure_ascii=False,
        indent=2,
    )
    json_(
        data_dir / "coin_transactions.json",
        transactions,
        create_file=True,
        ensure_ascii=False,
        backup=True,
    )


if __name__ == "__main__":
    main()
