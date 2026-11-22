## Resumo Comparativo

| Estratégia | Modelo | Acurácia | Erros | Latência Média (ms) | Prompt Tokens (média) | Total Tokens (média) | Chamadas LLM | Uso de Tool Esperada |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `prompt_stuffing` | `deepseek-flash` | 13/15 (86.7%) | 0 | 1355.9 | 658.9 | 741.1 | 1.00 | — |
| `tool_calling` | `deepseek-flash` | 15/15 (100.0%) | 0 | 2498.3 | 2007.1 | 2164.6 | 1.93 | 100.0% |

## Detalhamento por Caso

| Caso | Categoria | Estratégia | Status | Latência (ms) | Tokens | Tools | Motivo (se falhou) |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `list_all_gpus` | `basic_lookup` | `prompt_stuffing` | PASS | 1678 | 577 | — | — |
| `check_two_a100` | `basic_lookup` | `prompt_stuffing` | PASS | 1033 | 453 | — | — |
| `check_vram_l40s` | `basic_lookup` | `prompt_stuffing` | PASS | 1177 | 429 | — | — |
| `exceeds_available_h100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 1581 | 562 | — | — |
| `partial_usage_a100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 956 | 440 | — | — |
| `zero_available_4090` | `availability_and_bounds` | `prompt_stuffing` | PASS | 1339 | 436 | — | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `prompt_stuffing` | FAIL | 1216 | 511 | — | contained forbidden term 'L40S'; contained forbidden term '4090'; contained forbidden term 'A40' |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 1336 | 547 | — | — |
| `total_fleet_vram` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 1256 | 523 | — | — |
| `nonexistent_b200` | `anti_hallucination` | `prompt_stuffing` | PASS | 1573 | 479 | — | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `prompt_stuffing` | PASS | 1025 | 461 | — | — |
| `out_of_scope_reservation` | `anti_hallucination` | `prompt_stuffing` | PASS | 2241 | 579 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `prompt_stuffing` | PASS | 1121 | 1703 | — | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `prompt_stuffing` | FAIL | 1843 | 1745 | — | contained forbidden term 'A100' |
| `scaled_zero_l4` | `scaled_stress` | `prompt_stuffing` | PASS | 963 | 1671 | — | — |
| `list_all_gpus` | `basic_lookup` | `tool_calling` | PASS | 3057 | 2536 | list_gpus | — |
| `check_two_a100` | `basic_lookup` | `tool_calling` | PASS | 2127 | 2183 | check_availability | — |
| `check_vram_l40s` | `basic_lookup` | `tool_calling` | PASS | 2594 | 2125 | find_gpus | — |
| `exceeds_available_h100` | `availability_and_bounds` | `tool_calling` | PASS | 2959 | 2242 | check_availability | — |
| `partial_usage_a100` | `availability_and_bounds` | `tool_calling` | PASS | 2313 | 2169 | check_availability | — |
| `zero_available_4090` | `availability_and_bounds` | `tool_calling` | PASS | 2412 | 2216 | check_availability | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 2114 | 2235 | find_gpus | — |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 2595 | 2473 | find_gpus | — |
| `total_fleet_vram` | `aggregation_and_filtering` | `tool_calling` | PASS | 2552 | 2148 | get_fleet_summary | — |
| `nonexistent_b200` | `anti_hallucination` | `tool_calling` | PASS | 2225 | 2084 | check_availability | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `tool_calling` | PASS | 2580 | 2200 | find_gpus | — |
| `out_of_scope_reservation` | `anti_hallucination` | `tool_calling` | PASS | 1334 | 1023 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `tool_calling` | PASS | 3081 | 2418 | check_availability, find_gpus | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `tool_calling` | PASS | 2549 | 2180 | find_gpus | — |
| `scaled_zero_l4` | `scaled_stress` | `tool_calling` | PASS | 2983 | 2237 | check_availability | — |
