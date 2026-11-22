## Resumo Comparativo

| Estratégia | Modelo | Acurácia | Erros | Latência Média (ms) | Prompt Tokens (média) | Total Tokens (média) | Chamadas LLM | Uso de Tool Esperada |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `prompt_stuffing` | `deepseek-flash` | 13/15 (86.7%) | 0 | 1556.6 | 658.9 | 743.9 | 1.00 | — |
| `tool_calling` | `deepseek-flash` | 15/15 (100.0%) | 0 | 2605.0 | 2018.9 | 2165.5 | 1.93 | 100.0% |

## Detalhamento por Caso

| Caso | Categoria | Estratégia | Status | Latência (ms) | Tokens | Tools | Motivo (se falhou) |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `list_all_gpus` | `basic_lookup` | `prompt_stuffing` | PASS | 2019 | 577 | — | — |
| `check_two_a100` | `basic_lookup` | `prompt_stuffing` | PASS | 1436 | 451 | — | — |
| `check_vram_l40s` | `basic_lookup` | `prompt_stuffing` | PASS | 962 | 431 | — | — |
| `exceeds_available_h100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 2266 | 595 | — | — |
| `partial_usage_a100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 1396 | 437 | — | — |
| `zero_available_4090` | `availability_and_bounds` | `prompt_stuffing` | PASS | 936 | 436 | — | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `prompt_stuffing` | FAIL | 1401 | 511 | — | contained forbidden term 'L40S'; contained forbidden term '4090'; contained forbidden term 'A40' |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 1864 | 547 | — | — |
| `total_fleet_vram` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 1830 | 523 | — | — |
| `nonexistent_b200` | `anti_hallucination` | `prompt_stuffing` | PASS | 1169 | 493 | — | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `prompt_stuffing` | PASS | 1640 | 461 | — | — |
| `out_of_scope_reservation` | `anti_hallucination` | `prompt_stuffing` | PASS | 1784 | 570 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `prompt_stuffing` | PASS | 1146 | 1702 | — | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `prompt_stuffing` | FAIL | 1958 | 1753 | — | contained forbidden term 'A100' |
| `scaled_zero_l4` | `scaled_stress` | `prompt_stuffing` | PASS | 1542 | 1672 | — | — |
| `list_all_gpus` | `basic_lookup` | `tool_calling` | PASS | 3130 | 2544 | list_gpus | — |
| `check_two_a100` | `basic_lookup` | `tool_calling` | PASS | 2354 | 2172 | check_availability | — |
| `check_vram_l40s` | `basic_lookup` | `tool_calling` | PASS | 2600 | 2125 | find_gpus | — |
| `exceeds_available_h100` | `availability_and_bounds` | `tool_calling` | PASS | 3663 | 2266 | check_availability | — |
| `partial_usage_a100` | `availability_and_bounds` | `tool_calling` | PASS | 2153 | 2179 | check_availability | — |
| `zero_available_4090` | `availability_and_bounds` | `tool_calling` | PASS | 2468 | 2249 | check_availability | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 2623 | 2232 | find_gpus | — |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 2217 | 2400 | find_gpus | — |
| `total_fleet_vram` | `aggregation_and_filtering` | `tool_calling` | PASS | 2437 | 2065 | get_fleet_summary | — |
| `nonexistent_b200` | `anti_hallucination` | `tool_calling` | PASS | 3295 | 2076 | check_availability | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `tool_calling` | PASS | 2483 | 2181 | find_gpus | — |
| `out_of_scope_reservation` | `anti_hallucination` | `tool_calling` | PASS | 1369 | 1025 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `tool_calling` | PASS | 2793 | 2416 | check_availability, find_gpus | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `tool_calling` | PASS | 2610 | 2161 | find_gpus | — |
| `scaled_zero_l4` | `scaled_stress` | `tool_calling` | PASS | 2878 | 2392 | check_availability | — |
