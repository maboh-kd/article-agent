import argparse, json
from article_agent.pipeline import run_once

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="ダミーモデルで実行しSlack未設定でも成功させる")
    args = ap.parse_args()

    rec = run_once(use_dummy_model=True, try_webhook_first=not args.dry_run)
    print(json.dumps(rec, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
