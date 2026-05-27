from benchmark_common import (
    THROUGHPUT_RUNS,
    THROUGHPUT_SIZES,
    finalize_group,
    measure_throughput,
    python_fallback_runner,
    rust_fallback_runner,
)


def main() -> None:
    results = []
    lines = lambda n: ("test a" if i % 2 == 0 else "test b" for i in range(n))
    for count in THROUGHPUT_SIZES:
        py_metrics = measure_throughput(
            "python_fallback_extra_types",
            python_fallback_runner(),
            lines,
            count,
            runs=THROUGHPUT_RUNS,
        )
        baseline = py_metrics["throughput_lines_per_s"]
        results.append({"workload": "fallback_extra_types", **py_metrics})

        metrics = measure_throughput(
            "rust_fallback_extra_types",
            rust_fallback_runner(),
            lines,
            count,
            runs=THROUGHPUT_RUNS,
        )
        metrics["speedup"] = metrics["throughput_lines_per_s"] / baseline
        results.append({"workload": "fallback_extra_types", **metrics})

    finalize_group("fallback-throughput", results)


if __name__ == "__main__":
    main()
