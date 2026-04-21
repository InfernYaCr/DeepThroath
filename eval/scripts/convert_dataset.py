#!/usr/bin/env python3
"""
Конвертирует top_k JSON-файл в датасет для DeepEval-тестов.

Входные поля  : user_query, intent, expected_answer, actual_answer, error
Выходные поля : id, category, question, expected_output, actual_output

Использование:
  python eval/scripts/convert_dataset.py eval/top_k/20260329_173829_exp_top_k_10.json
  python eval/scripts/convert_dataset.py eval/top_k/some_file.json --out eval/datasets/my_dataset.json
"""

import argparse
import json
import sys
from pathlib import Path


def convert(src: Path, dst: Path) -> None:
    with open(src, encoding="utf-8") as f:
        records = json.load(f)

    dataset = []
    for i, rec in enumerate(records, 1):
        # Пропускаем записи с ошибками
        if rec.get("error"):
            print(f"[skip] #{i} error: {rec['error']}")
            continue
        if not rec.get("user_query") or not rec.get("actual_answer"):
            print(f"[skip] #{i} missing query or answer")
            continue

        dataset.append(
            {
                "id": f"TC-{i:03d}",
                "category": rec["intent"],  # API-compatible intent key
                "question": rec["user_query"],
                "expected_output": rec.get("expected_answer") or "",
                "actual_output": rec.get("actual_answer") or "",
                "_source_session": rec.get("session_id"),
                "_source_category": rec.get("category"),  # human-readable category
            }
        )

    dst.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Конвертировано: {len(dataset)} записей → {dst}")

    # Статистика по категориям
    from collections import Counter

    cats = Counter(d["category"] for d in dataset)
    for cat, cnt in sorted(cats.items()):
        print(f"  {cat:<20} {cnt}")


def main():
    parser = argparse.ArgumentParser(description="Convert top_k JSON to eval dataset")
    parser.add_argument("input", help="Path to top_k JSON file")
    parser.add_argument("--out", default=None, help="Output path (default: eval/datasets/<stem>_dataset.json)")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        print(f"File not found: {src}")
        sys.exit(1)

    if args.out:
        dst = Path(args.out)
    else:
        datasets_dir = Path(__file__).parent.parent / "datasets"
        datasets_dir.mkdir(exist_ok=True)
        dst = datasets_dir / (src.stem + "_dataset.json")

    convert(src, dst)


if __name__ == "__main__":
    main()
