from pathlib import Path
import json, datetime, re

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def sanitize_filename(s: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', '', s).strip()

def now_stamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def save_markdown(title: str, content: str, outdir: Path) -> Path:
    ensure_dir(outdir)
    fname = f"{now_stamp()}_{sanitize_filename(title)}.md"
    fpath = outdir / fname
    fpath.write_text(content, encoding="utf-8")
    return fpath

def append_jsonl(record: dict, logdir: Path) -> Path:
    ensure_dir(logdir)
    fpath = logdir / f"{datetime.datetime.now().strftime('%Y-%m-%d')}.jsonl"
    with fpath.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return fpath
