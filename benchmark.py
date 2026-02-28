from __future__ import annotations

import argparse
import csv
import gc
import random
import string
import sys
import timeit
from collections import deque
from dataclasses import dataclass
from io import StringIO
from typing import Callable, Iterable

DEFAULT_SIZES = (10_000, 100_000, 500_000)
DEFAULT_NUMBER = 100
DEFAULT_REPEAT = 5
_CORRECTNESS_SAMPLE_MAX = 2_000


@dataclass(frozen=True)
class BenchmarkRecord:
    test_id: str
    n: int
    slow_method: str
    fast_method: str
    slow_sec: float
    fast_sec: float

    @property
    def speedup_x(self) -> float:
        if self.fast_sec <= 0.0:
            return float("inf")
        return self.slow_sec / self.fast_sec


def validate_n(n: int) -> None:
    if n <= 0:
        raise ValueError(f"n must be positive: {n}")


def slow_list_prepend(n: int) -> list[int]:
    validate_n(n)
    items: list[int] = []
    for i in range(n):
        items.insert(0, i)
    return items


def fast_deque_prepend(n: int) -> list[int]:
    validate_n(n)
    items: deque[int] = deque()
    for i in range(n):
        items.appendleft(i)
    return list(items)


def prepare_lookup_data(n: int) -> tuple[list[int], set[int], int]:
    validate_n(n)
    list_data = list(range(n))
    set_data = set(list_data)
    target = n - 1
    return list_data, set_data, target


def slow_list_contains(list_data: list[int], target: int) -> bool:
    return target in list_data


def fast_set_contains(set_data: set[int], target: int) -> bool:
    return target in set_data


def generate_string_parts(n: int, seed: int = 42, part_length: int = 10) -> list[str]:
    validate_n(n)
    if part_length <= 0:
        raise ValueError(f"part_length must be positive: {part_length}")
    rand = random.Random(seed)
    alphabet = string.ascii_letters + string.digits
    parts = []
    for _ in range(n):
        parts.append("".join(rand.choice(alphabet) for _ in range(part_length)))
    return parts


def slow_concat_plus_equal(parts: list[str]) -> str:
    result = ""
    for part in parts:
        result += part
    return result


def fast_concat_join(parts: list[str]) -> str:
    return "".join(parts)


def _measure_min_seconds(func: Callable[[], object], number: int, repeat: int) -> float:
    if number <= 0:
        raise ValueError(f"number must be positive: {number}")
    if repeat <= 0:
        raise ValueError(f"repeat must be positive: {repeat}")

    was_enabled = gc.isenabled()
    gc.disable()
    try:
        timer = timeit.Timer(func)
        results = timer.repeat(repeat=repeat, number=number)
        return min(results)
    finally:
        if was_enabled:
            gc.enable()


def _assert_equal_outputs(left: object, right: object, test_id: str) -> None:
    if left != right:
        raise RuntimeError(f"output mismatch in {test_id}")


def benchmark_prepend(n: int, number: int, repeat: int) -> BenchmarkRecord:
    validate_n(n)
    sample_n = min(n, _CORRECTNESS_SAMPLE_MAX)
    _assert_equal_outputs(
        slow_list_prepend(sample_n),
        fast_deque_prepend(sample_n),
        "T1_PREPEND",
    )

    slow_sec = _measure_min_seconds(lambda: slow_list_prepend(n), number, repeat)
    fast_sec = _measure_min_seconds(lambda: fast_deque_prepend(n), number, repeat)
    return BenchmarkRecord(
        test_id="T1_PREPEND",
        n=n,
        slow_method="list.insert(0, i)",
        fast_method="deque.appendleft(i)",
        slow_sec=slow_sec,
        fast_sec=fast_sec,
    )


def benchmark_contains(n: int, number: int, repeat: int) -> BenchmarkRecord:
    list_data, set_data, target = prepare_lookup_data(n)
    _assert_equal_outputs(
        slow_list_contains(list_data, target),
        fast_set_contains(set_data, target),
        "T2_CONTAINS",
    )

    slow_sec = _measure_min_seconds(
        lambda: slow_list_contains(list_data, target),
        number,
        repeat,
    )
    fast_sec = _measure_min_seconds(
        lambda: fast_set_contains(set_data, target),
        number,
        repeat,
    )
    return BenchmarkRecord(
        test_id="T2_CONTAINS",
        n=n,
        slow_method="target in list_data",
        fast_method="target in set_data",
        slow_sec=slow_sec,
        fast_sec=fast_sec,
    )


def benchmark_concat(n: int, number: int, repeat: int) -> BenchmarkRecord:
    parts = generate_string_parts(n)
    _assert_equal_outputs(
        slow_concat_plus_equal(parts),
        fast_concat_join(parts),
        "T3_CONCAT",
    )

    slow_sec = _measure_min_seconds(lambda: slow_concat_plus_equal(parts), number, repeat)
    fast_sec = _measure_min_seconds(lambda: fast_concat_join(parts), number, repeat)
    return BenchmarkRecord(
        test_id="T3_CONCAT",
        n=n,
        slow_method="loop with +=",
        fast_method="''.join(parts)",
        slow_sec=slow_sec,
        fast_sec=fast_sec,
    )


def run_all_benchmarks(
    sizes: Iterable[int] = DEFAULT_SIZES,
    *,
    number: int = DEFAULT_NUMBER,
    repeat: int = DEFAULT_REPEAT,
) -> list[BenchmarkRecord]:
    records: list[BenchmarkRecord] = []
    for n in sizes:
        validate_n(n)
        records.append(benchmark_prepend(n, number, repeat))
        records.append(benchmark_contains(n, number, repeat))
        records.append(benchmark_concat(n, number, repeat))
    return records


def build_markdown_table(records: list[BenchmarkRecord]) -> str:
    lines = [
        "| Test | N | Slow | Fast | Slow(sec) | Fast(sec) | Speedup(x) |",
        "|---|---:|---|---|---:|---:|---:|",
    ]
    for record in records:
        lines.append(
            f"| {record.test_id} | {record.n} | {record.slow_method} | "
            f"{record.fast_method} | {record.slow_sec:.6f} | {record.fast_sec:.6f} | "
            f"{record.speedup_x:.2f} |"
        )
    return "\n".join(lines)


def build_csv(records: list[BenchmarkRecord]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "test_id",
            "n",
            "slow_method",
            "fast_method",
            "slow_sec",
            "fast_sec",
            "speedup_x",
        ]
    )
    for record in records:
        writer.writerow(
            [
                record.test_id,
                record.n,
                record.slow_method,
                record.fast_method,
                f"{record.slow_sec:.9f}",
                f"{record.fast_sec:.9f}",
                f"{record.speedup_x:.6f}",
            ]
        )
    return buffer.getvalue().strip()


def build_summary(records: list[BenchmarkRecord]) -> dict[str, float]:
    if not records:
        return {}

    max_by_test: dict[str, float] = {}
    overall_max = 0.0
    for record in records:
        speedup = record.speedup_x
        current = max_by_test.get(record.test_id)
        if current is None or speedup > current:
            max_by_test[record.test_id] = speedup
        if speedup > overall_max:
            overall_max = speedup

    summary: dict[str, float] = {
        f"{test_id}_max_speedup_x": value for test_id, value in sorted(max_by_test.items())
    }
    summary["overall_max_speedup_x"] = overall_max
    return summary


def print_summary(summary: dict[str, float]) -> None:
    print("Summary")
    for key, value in summary.items():
        print(f"{key}: {value:.2f}")


def parse_sizes(raw: str) -> list[int]:
    parts = [item.strip() for item in raw.split(",")]
    if not parts or any(not p for p in parts):
        raise ValueError("sizes must be a non-empty comma-separated list")
    sizes = [int(p) for p in parts]
    for size in sizes:
        validate_n(size)
    return sizes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Python performance benchmark runner")
    parser.add_argument(
        "--sizes",
        default="10_000,100_000,500_000",
        help="comma-separated list of N values",
    )
    parser.add_argument("--number", type=int, default=DEFAULT_NUMBER)
    parser.add_argument("--repeat", type=int, default=DEFAULT_REPEAT)
    args = parser.parse_args(argv)

    sizes_text = args.sizes.replace("_", "")
    sizes = parse_sizes(sizes_text)
    records = run_all_benchmarks(sizes, number=args.number, repeat=args.repeat)

    print(build_markdown_table(records))
    print()
    print(build_csv(records))
    print()
    print_summary(build_summary(records))
    return 0


if __name__ == "__main__":
    sys.exit(main())
