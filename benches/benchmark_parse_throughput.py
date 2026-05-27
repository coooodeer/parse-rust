from benchmark_common import (
    THROUGHPUT_RUNS,
    THROUGHPUT_SIZES,
    WORKLOADS,
    finalize_group,
    measure_throughput,
    python_compiled_runner,
    python_parse_runner,
    rust_compiled_parse_runner,
    rust_parse_runner,
)


def main() -> None:
    results = []
    for workload in WORKLOADS:
        baseline = {}
        for count in THROUGHPUT_SIZES:
            py_metrics = measure_throughput(
                "python_parse",
                python_parse_runner(workload.template),
                workload.factory,
                count,
                runs=THROUGHPUT_RUNS,
            )
            baseline[count] = py_metrics["throughput_lines_per_s"]
            results.append({"workload": workload.name, **py_metrics})

            py_compiled = measure_throughput(
                "python_compiled_parse",
                python_compiled_runner(workload.template),
                workload.factory,
                count,
                runs=THROUGHPUT_RUNS,
            )
            py_compiled["speedup"] = (
                py_compiled["throughput_lines_per_s"] / baseline[count]
            )
            results.append({"workload": workload.name, **py_compiled})

            for label, runner in [
                ("rust_parse_cold", rust_parse_runner(workload.template, "cold")),
                ("rust_parse_warm", rust_parse_runner(workload.template, "warm")),
                ("rust_compiled_parse", rust_compiled_parse_runner(workload.template)),
            ]:
                metrics = measure_throughput(label, runner, workload.factory, count, runs=THROUGHPUT_RUNS)
                metrics["speedup"] = (
                    metrics["throughput_lines_per_s"] / baseline[count]
                )
                results.append({"workload": workload.name, **metrics})

    finalize_group("parse-throughput", results)


if __name__ == "__main__":
    main()
