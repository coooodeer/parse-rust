from benchmark_common import (
    THROUGHPUT_RUNS,
    SEARCH_THROUGHPUT_SIZES,
    SEARCH_WORKLOADS,
    finalize_group,
    measure_throughput,
    python_compiled_search_runner,
    python_search_runner,
    rust_compiled_search_match_runner,
    rust_compiled_search_runner,
    rust_search_match_runner,
    rust_search_runner,
)


def main() -> None:
    results = []
    for workload in SEARCH_WORKLOADS:
        baseline = {}
        for count in SEARCH_THROUGHPUT_SIZES:
            py_metrics = measure_throughput(
                "python_search",
                python_search_runner(workload.template),
                workload.factory,
                count,
                runs=THROUGHPUT_RUNS,
            )
            baseline[count] = py_metrics["throughput_lines_per_s"]
            results.append({"workload": workload.name, **py_metrics})

            py_compiled = measure_throughput(
                "python_compiled_search",
                python_compiled_search_runner(workload.template),
                workload.factory,
                count,
                runs=THROUGHPUT_RUNS,
            )
            py_compiled["speedup"] = (
                py_compiled["throughput_lines_per_s"] / baseline[count]
            )
            results.append({"workload": workload.name, **py_compiled})

            for label, runner in [
                ("rust_search_cold", rust_search_runner(workload.template, "cold")),
                ("rust_search_warm", rust_search_runner(workload.template, "warm")),
                ("rust_search_match_warm", rust_search_match_runner(workload.template, "warm")),
                ("rust_compiled_search", rust_compiled_search_runner(workload.template)),
                ("rust_compiled_search_match", rust_compiled_search_match_runner(workload.template)),
            ]:
                metrics = measure_throughput(label, runner, workload.factory, count, runs=THROUGHPUT_RUNS)
                metrics["speedup"] = (
                    metrics["throughput_lines_per_s"] / baseline[count]
                )
                results.append({"workload": workload.name, **metrics})

    finalize_group("search-throughput", results)


if __name__ == "__main__":
    main()
