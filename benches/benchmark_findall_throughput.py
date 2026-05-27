from benchmark_common import (
    THROUGHPUT_RUNS,
    THROUGHPUT_SIZES,
    finalize_group,
    measure_throughput,
    python_compiled_findall_runner,
    python_findall_runner,
    rust_compiled_findall_runner,
    rust_findall_runner,
)

TEXT_TEMPLATE = "{}"
TEXT_FACTORY = lambda n: (f"row {i} value {i + 1}" for i in range(n))


def main() -> None:
    results = []
    for count in THROUGHPUT_SIZES:
        py_metrics = measure_throughput(
            "python_findall",
            python_findall_runner(TEXT_TEMPLATE),
            TEXT_FACTORY,
            count,
            runs=THROUGHPUT_RUNS,
        )
        baseline = py_metrics["throughput_lines_per_s"]
        results.append({"workload": "findall_scan", **py_metrics})

        py_compiled = measure_throughput(
            "python_compiled_findall",
            python_compiled_findall_runner(TEXT_TEMPLATE),
            TEXT_FACTORY,
            count,
            runs=THROUGHPUT_RUNS,
        )
        py_compiled["speedup"] = (
            py_compiled["throughput_lines_per_s"] / baseline
        )
        results.append({"workload": "findall_scan", **py_compiled})

        for label, runner in [
            ("rust_findall_cold", rust_findall_runner(TEXT_TEMPLATE, "cold")),
            ("rust_findall_warm", rust_findall_runner(TEXT_TEMPLATE, "warm")),
            ("rust_compiled_findall", rust_compiled_findall_runner(TEXT_TEMPLATE)),
        ]:
            metrics = measure_throughput(label, runner, TEXT_FACTORY, count, runs=THROUGHPUT_RUNS)
            metrics["speedup"] = (
                metrics["throughput_lines_per_s"] / baseline
            )
            results.append({"workload": "findall_scan", **metrics})

    finalize_group("findall-throughput", results)


if __name__ == "__main__":
    main()
