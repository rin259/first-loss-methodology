# Real-model RCA baseline

- Prompt version: `llm-rca-v1.1.1`
- Requested model: `glm-5.3-flash`
- Provider-reported model: `glm-5-3-flash`
- Cases / repeated runs: `60` / `300`
- Response format: `json_object` with exact field validation

| Metric | Result |
|---|---:|
| Attribution accuracy | 0.920 |
| Exact-path FLA | 0.987 |
| Exact-path ILA | 0.813 |
| Exact-path RCA | 0.973 |
| Status accuracy | 0.927 |
| Risky-case overclaim rate | 0.047 |
| Five-run exact agreement | 0.200 |
| Schema adherence | 1.000 |

Two compatibility pilots are excluded. The final prompt was frozen only after those pilots, so this is not a preregistered model comparison. The endpoint is OpenAI-compatible; it is not evidence that the model was served by OpenAI.
