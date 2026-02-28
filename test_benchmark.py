import csv
import io
import unittest

from benchmark import (
    BenchmarkRecord,
    build_csv,
    build_markdown_table,
    build_summary,
    fast_concat_join,
    fast_deque_prepend,
    fast_set_contains,
    generate_string_parts,
    parse_sizes,
    prepare_lookup_data,
    run_all_benchmarks,
    slow_concat_plus_equal,
    slow_list_contains,
    slow_list_prepend,
    validate_n,
)


class TestBenchmark(unittest.TestCase):
    def test_validate_n_rejects_zero_and_negative(self) -> None:
        with self.assertRaises(ValueError):
            validate_n(0)
        with self.assertRaises(ValueError):
            validate_n(-1)

    def test_parse_sizes_accepts_valid_and_rejects_invalid(self) -> None:
        self.assertEqual(parse_sizes("10,100,500"), [10, 100, 500])
        with self.assertRaises(ValueError):
            parse_sizes("")
        with self.assertRaises(ValueError):
            parse_sizes("10,,20")

    def test_prepend_implementations_are_equivalent(self) -> None:
        expected = slow_list_prepend(10)
        actual = fast_deque_prepend(10)
        self.assertEqual(expected, actual)

    def test_contains_implementations_are_equivalent(self) -> None:
        list_data, set_data, target = prepare_lookup_data(50)
        self.assertEqual(
            slow_list_contains(list_data, target),
            fast_set_contains(set_data, target),
        )

    def test_concat_implementations_are_equivalent(self) -> None:
        parts = generate_string_parts(25, seed=123)
        self.assertEqual(slow_concat_plus_equal(parts), fast_concat_join(parts))

    def test_generate_string_parts_is_deterministic(self) -> None:
        left = generate_string_parts(5, seed=42)
        right = generate_string_parts(5, seed=42)
        self.assertEqual(left, right)
        self.assertEqual(len(left[0]), 10)

    def test_run_all_benchmarks_with_small_inputs(self) -> None:
        records = run_all_benchmarks([20, 40], number=1, repeat=1)
        self.assertEqual(len(records), 6)
        for record in records:
            self.assertGreater(record.slow_sec, 0.0)
            self.assertGreater(record.fast_sec, 0.0)
            self.assertGreater(record.speedup_x, 0.0)

    def test_output_rendering(self) -> None:
        records = [
            BenchmarkRecord(
                test_id="T1_PREPEND",
                n=100,
                slow_method="list.insert(0, i)",
                fast_method="deque.appendleft(i)",
                slow_sec=1.5,
                fast_sec=0.5,
            )
        ]
        markdown = build_markdown_table(records)
        csv_text = build_csv(records)
        self.assertIn("Speedup(x)", markdown)
        self.assertIn("T1_PREPEND", markdown)

        parsed = list(csv.reader(io.StringIO(csv_text)))
        self.assertEqual(parsed[0][0], "test_id")
        self.assertEqual(parsed[1][0], "T1_PREPEND")

    def test_build_summary(self) -> None:
        records = [
            BenchmarkRecord("T1_PREPEND", 10, "slow", "fast", 4.0, 2.0),
            BenchmarkRecord("T1_PREPEND", 20, "slow", "fast", 9.0, 3.0),
            BenchmarkRecord("T2_CONTAINS", 10, "slow", "fast", 8.0, 2.0),
        ]
        summary = build_summary(records)
        self.assertAlmostEqual(summary["T1_PREPEND_max_speedup_x"], 3.0)
        self.assertAlmostEqual(summary["T2_CONTAINS_max_speedup_x"], 4.0)
        self.assertAlmostEqual(summary["overall_max_speedup_x"], 4.0)


if __name__ == "__main__":
    unittest.main()
