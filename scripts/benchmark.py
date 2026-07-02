"""CLI: run the evaluation benchmark and print a report.  python scripts/benchmark.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.rag import KnowledgeEngine
from backend.benchmark import run


def main() -> None:
    engine = KnowledgeEngine()
    r = run(engine)
    s = r["summary"]
    print("=" * 68)
    print(" INDUSTRIAL KNOWLEDGE INTELLIGENCE — Evaluation Benchmark")
    print("=" * 68)
    for row in r["results"]:
        mark = "OK " if row["hit"] else "MISS"
        print(f" [{mark}] {row['time_ms']:>4}ms  {row['question'][:52]:52}  -> {row['expected']}")
    print("-" * 68)
    print(f" Retrieval hit-rate (our system) : {s['retrieval_hit_rate']}%")
    print(f" Answer coverage                 : {s['answer_coverage']}%")
    print(f" Keyword-search baseline hit-rate: {s['baseline_hit_rate']}%")
    print(f" Median time-to-answer           : {s['median_time_ms']} ms")
    print(f" (baseline median                : {s['baseline_median_time_ms']} ms)")
    print("=" * 68)


if __name__ == "__main__":
    main()
