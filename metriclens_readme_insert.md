[![Decomposition](https://img.shields.io/badge/Decomposition-Mix%20%2F%20Rate%20%2F%20Cross-4fc3f7?style=flat-square)](src/)
[![Metric Types](https://img.shields.io/badge/Metrics-Ratio%20%7C%20Sum%20%7C%20Count%20%7C%20Average-42a5f5?style=flat-square)](src/)
[![Tests](https://img.shields.io/badge/Tests-19%2F19_passing-66bb6a?style=flat-square)](tests/)
[![Output](https://img.shields.io/badge/Output-JSON%20%7C%20Markdown%20%7C%20HTML-ab47bc?style=flat-square)](src/)
[![pip](https://img.shields.io/badge/pip_install-metriclens-3776AB?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/metriclens/)

## How it works

```mermaid
flowchart LR
    DF["📊 pandas DataFrame\nDaily segment-level grain"] --> ML

    subgraph ML["MetricLens Engine  src/metriclens/"]
        MT["Metric Type\nRatioMetric · SumMetric\nCountMetric · AverageMetric"]
        VAL["Input Validation\nNull handling · zero-fill convention\nDisappeared + new segment detection"]
        DEC["Decomposition\nmix_effect + rate_effect + cross_term\nSums exactly to total_delta · no residual"]
    end

    MT --> VAL --> DEC

    DEC --> RANK["Segment Ranking\nBy absolute total_effect\nAuto-generated investigation priority order"]

    RANK --> OUT

    subgraph OUT["Output Formats"]
        JSON["result.to_json()\nMachine-readable · LLM-naratable"]
        MD["result.to_markdown()\nContribution table"]
        HTML["result.to_html()\nSelf-contained report"]
    end

    subgraph NOTE["Interpretation Note — mandatory, cannot be suppressed"]
        N1["Reports movement decomposition only"]
        N2["Does NOT claim causality or statistical significance"]
        N3["Outputs are investigation signals, not decisions"]
    end

    OUT --> NOTE
```

---

