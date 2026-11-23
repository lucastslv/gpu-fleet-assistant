## Resumo Comparativo

| Estratégia | Modelo | Acurácia | Erros | Latência Média (ms) | Prompt Tokens (média) | Total Tokens (média) | Chamadas LLM | Uso de Tool Esperada |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `prompt_stuffing` | `qwen3.5:4b` | 14/16 (87.5%) | 0 | 21512.4 | 742.6 | 1718.1 | 1.00 | — |
| `tool_calling` | `qwen3.5:4b` | 16/16 (100.0%) | 0 | 7587.4 | 2029.6 | 2360.7 | 1.94 | 100.0% |

## Detalhamento por Caso

| Caso | Categoria | Estratégia | Status | Latência (ms) | Tokens | Tools | Motivo (se falhou) |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `list_all_gpus` | `basic_lookup` | `prompt_stuffing` | PASS | 27257 | 1348 | — | — |
| `check_two_a100` | `basic_lookup` | `prompt_stuffing` | FAIL | 17219 | 1238 | — | contained forbidden term 'nao,' |
| `check_vram_l40s` | `basic_lookup` | `prompt_stuffing` | PASS | 16303 | 1199 | — | — |
| `exceeds_available_h100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 19892 | 1366 | — | — |
| `partial_usage_a100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 17233 | 1232 | — | — |
| `zero_available_4090` | `availability_and_bounds` | `prompt_stuffing` | PASS | 14247 | 1094 | — | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `prompt_stuffing` | FAIL | 19854 | 1362 | — | contained forbidden term 'L40S'; contained forbidden term '4090'; contained forbidden term 'A40' |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 33218 | 2006 | — | — |
| `total_fleet_vram` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 15778 | 1177 | — | — |
| `nonexistent_b200` | `anti_hallucination` | `prompt_stuffing` | PASS | 22751 | 1494 | — | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `prompt_stuffing` | PASS | 18209 | 1286 | — | — |
| `out_of_scope_reservation` | `anti_hallucination` | `prompt_stuffing` | PASS | 30274 | 1852 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `prompt_stuffing` | PASS | 14655 | 2299 | — | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `prompt_stuffing` | PASS | 40183 | 3530 | — | — |
| `scaled_zero_l4` | `scaled_stress` | `prompt_stuffing` | PASS | 13110 | 2244 | — | — |
| `scaled_intel_ge_48gb` | `scaled_stress` | `prompt_stuffing` | PASS | 24014 | 2762 | — | — |
| `list_all_gpus` | `basic_lookup` | `tool_calling` | PASS | 12072 | 2789 | list_gpus | — |
| `check_two_a100` | `basic_lookup` | `tool_calling` | PASS | 4936 | 2266 | check_availability | — |
| `check_vram_l40s` | `basic_lookup` | `tool_calling` | PASS | 4286 | 2204 | find_gpus | — |
| `exceeds_available_h100` | `availability_and_bounds` | `tool_calling` | PASS | 7283 | 2395 | check_availability | — |
| `partial_usage_a100` | `availability_and_bounds` | `tool_calling` | PASS | 6296 | 2334 | check_availability | — |
| `zero_available_4090` | `availability_and_bounds` | `tool_calling` | PASS | 5994 | 2329 | check_availability | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 5469 | 2332 | find_gpus | — |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 13657 | 2863 | find_gpus | — |
| `total_fleet_vram` | `aggregation_and_filtering` | `tool_calling` | PASS | 4961 | 2209 | get_fleet_summary | — |
| `nonexistent_b200` | `anti_hallucination` | `tool_calling` | PASS | 4022 | 2168 | check_availability | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `tool_calling` | PASS | 8922 | 2472 | check_availability | — |
| `out_of_scope_reservation` | `anti_hallucination` | `tool_calling` | PASS | 7196 | 1277 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `tool_calling` | PASS | 8224 | 2456 | check_availability | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `tool_calling` | PASS | 10726 | 2732 | find_gpus | — |
| `scaled_zero_l4` | `scaled_stress` | `tool_calling` | PASS | 7759 | 2397 | check_availability | — |
| `scaled_intel_ge_48gb` | `scaled_stress` | `tool_calling` | PASS | 9596 | 2548 | find_gpus | — |
