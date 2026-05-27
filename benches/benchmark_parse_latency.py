from benchmark_common import (
    LATENCY_SAMPLES,
    WORKLOADS,
    finalize_group,
    measure_latency,
    python_compiled_call,
    python_parse_call,
    rust_compiled_parse_call,
    rust_parse_call,
)


def main() -> None:
    results = []
    for workload in WORKLOADS:
        sample_input = next(workload.factory(1))
        for label, call_factory, warm_cache in [
            ("python_parse", lambda t=workload.template: python_parse_call(t), False),
            ("python_compiled_parse", lambda t=workload.template: python_compiled_call(t), False),
            ("rust_parse_cold", lambda t=workload.template: rust_parse_call(t), False),
            ("rust_parse_warm", lambda t=workload.template: rust_parse_call(t), True),
            ("rust_compiled_parse", lambda t=workload.template: rust_compiled_parse_call(t), False),
        ]:
            metrics = measure_latency(label, call_factory, sample_input, warm_cache)
            metrics["samples"] = LATENCY_SAMPLES
            results.append({"workload": workload.name, **metrics})

    finalize_group("parse-latency", results)


if __name__ == "__main__":
    main()
