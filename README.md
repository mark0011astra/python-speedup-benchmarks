# Python Speedup Benchmarks

A compact benchmark project that compares common "slow" Python patterns with faster alternatives.

This repository focuses on three practical optimizations:

1. `list.insert(0, i)` vs `deque.appendleft(i)`
2. `target in list_data` vs `target in set_data`
3. Loop string concatenation (`+=`) vs `"".join(parts)`

## Why This Project

Many performance issues in production Python code come from data-structure and idiom choices, not advanced optimization techniques.
This project is designed to provide:

- Reproducible benchmark scripts
- Unit tests for correctness and boundary conditions
- Markdown + CSV outputs for reporting and visualization
- Real measured results that can be reused in technical articles

## Repository Structure

- `benchmark.py`: Benchmark runner and output generator (Markdown table, CSV, summary)
- `test_benchmark.py`: Unit tests
- `benchmark_results.txt`: Captured benchmark output (sample run)
- `test_specification.md`: Benchmark specification
- `qiita_article.md`: Article draft based on the measured data
- `README.md`: Project documentation
- `LICENSE`: MIT license

## Requirements

- Python 3.10+
- Standard library only (no third-party dependencies)

## How to Run

### Quick Run (same conditions used for the published result)

```bash
python3 benchmark.py --sizes 10000,30000,50000 --number 10 --repeat 5
```

### Full/Custom Run

```bash
python3 benchmark.py --sizes 10000,100000,500000 --number 100 --repeat 5
```

Arguments:

- `--sizes`: Comma-separated list of `N` values
- `--number`: Number of executions per repeat
- `--repeat`: Number of repeat sets (minimum value is used)

## Test Execution

```bash
python3 -m unittest -v
```

## Benchmark Methodology

- Timing module: `timeit`
- Garbage collector: disabled during each timing block (`gc.disable()`), then restored
- Adopted value: minimum over repeated measurements
- Input validation: `N <= 0` is rejected
- Correctness check: slow and fast implementations must produce equivalent outputs before timing

## Measured Results (from `benchmark_results.txt`)

### Max Speedup by Category

| Optimization | Max Speedup |
|---|---:|
| `target in list_data` -> `target in set_data` | 2985.11x |
| `list.insert(0, i)` -> `deque.appendleft(i)` | 380.95x |
| String `+=` -> `"".join(parts)` | 8.72x |

### Detailed Results

| Test | N | Slow | Fast | Slow(sec) | Fast(sec) | Speedup(x) |
|---|---:|---|---|---:|---:|---:|
| T1_PREPEND | 10000 | list.insert(0, i) | deque.appendleft(i) | 0.229309 | 0.002925 | 78.39 |
| T2_CONTAINS | 10000 | target in list_data | target in set_data | 0.000374 | 0.000001 | 598.33 |
| T3_CONCAT | 10000 | loop with += | ''.join(parts) | 0.003342 | 0.000387 | 8.65 |
| T1_PREPEND | 30000 | list.insert(0, i) | deque.appendleft(i) | 2.062963 | 0.008935 | 230.90 |
| T2_CONTAINS | 30000 | target in list_data | target in set_data | 0.001120 | 0.000001 | 1792.05 |
| T3_CONCAT | 30000 | loop with += | ''.join(parts) | 0.009965 | 0.001146 | 8.69 |
| T1_PREPEND | 50000 | list.insert(0, i) | deque.appendleft(i) | 5.709706 | 0.014988 | 380.95 |
| T2_CONTAINS | 50000 | target in list_data | target in set_data | 0.001866 | 0.000001 | 2985.11 |
| T3_CONCAT | 50000 | loop with += | ''.join(parts) | 0.016599 | 0.001903 | 8.72 |

## Notes on Interpretation

- Absolute times vary by machine and OS.
- Relative speedup trends are the key signal.
- The `in set` result can become dramatically larger than `in list` as data grows.

## License

Released under the MIT License.
See [LICENSE](LICENSE) for details.
