## Resumo Comparativo

| Estratégia | Modelo | Acurácia | Erros | Latência Média (ms) | Prompt Tokens (média) | Total Tokens (média) | Chamadas LLM | Uso de Tool Esperada |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `prompt_stuffing` | `deepseek-flash` | 13/15 (86.7%) | 0 | 1367.0 | 658.9 | 738.9 | 1.00 | — |
| `tool_calling` | `deepseek-flash` | 14/15 (93.3%) | 0 | 2508.3 | 2017.9 | 2169.7 | 1.93 | 100.0% |

## Detalhamento por Caso

| Caso | Categoria | Estratégia | Status | Latência (ms) | Tokens | Tools | Motivo (se falhou) |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `list_all_gpus` | `basic_lookup` | `prompt_stuffing` | PASS | 1487 | 574 | — | — |
| `check_two_a100` | `basic_lookup` | `prompt_stuffing` | PASS | 1313 | 451 | — | — |
| `check_vram_l40s` | `basic_lookup` | `prompt_stuffing` | PASS | 1423 | 429 | — | — |
| `exceeds_available_h100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 2090 | 563 | — | — |
| `partial_usage_a100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 865 | 440 | — | — |
| `zero_available_4090` | `availability_and_bounds` | `prompt_stuffing` | PASS | 957 | 445 | — | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `prompt_stuffing` | FAIL | 1680 | 511 | — | contained forbidden term 'L40S'; contained forbidden term '4090'; contained forbidden term 'A40' |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 1700 | 547 | — | — |
| `total_fleet_vram` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 1415 | 523 | — | — |
| `nonexistent_b200` | `anti_hallucination` | `prompt_stuffing` | PASS | 974 | 466 | — | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `prompt_stuffing` | PASS | 1091 | 461 | — | — |
| `out_of_scope_reservation` | `anti_hallucination` | `prompt_stuffing` | PASS | 1876 | 567 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `prompt_stuffing` | PASS | 1033 | 1683 | — | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `prompt_stuffing` | FAIL | 1434 | 1753 | — | contained forbidden term 'A100' |
| `scaled_zero_l4` | `scaled_stress` | `prompt_stuffing` | PASS | 1167 | 1671 | — | — |
| `list_all_gpus` | `basic_lookup` | `tool_calling` | PASS | 2479 | 2536 | list_gpus | — |
| `check_two_a100` | `basic_lookup` | `tool_calling` | PASS | 2591 | 2174 | check_availability | — |
| `check_vram_l40s` | `basic_lookup` | `tool_calling` | PASS | 3146 | 2125 | find_gpus | — |
| `exceeds_available_h100` | `availability_and_bounds` | `tool_calling` | PASS | 2601 | 2249 | check_availability | — |
| `partial_usage_a100` | `availability_and_bounds` | `tool_calling` | PASS | 2654 | 2208 | check_availability | — |
| `zero_available_4090` | `availability_and_bounds` | `tool_calling` | PASS | 2129 | 2217 | check_availability | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 2676 | 2235 | find_gpus | — |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 2040 | 2414 | find_gpus | — |
| `total_fleet_vram` | `aggregation_and_filtering` | `tool_calling` | FAIL | 2414 | 2065 | get_fleet_summary | missing required term '1032' |
| `nonexistent_b200` | `anti_hallucination` | `tool_calling` | PASS | 3083 | 2061 | check_availability | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `tool_calling` | PASS | 2162 | 2211 | check_availability | — |
| `out_of_scope_reservation` | `anti_hallucination` | `tool_calling` | PASS | 1720 | 1023 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `tool_calling` | PASS | 2382 | 2381 | check_availability, find_gpus | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `tool_calling` | PASS | 2451 | 2192 | find_gpus | — |
| `scaled_zero_l4` | `scaled_stress` | `tool_calling` | PASS | 3095 | 2454 | check_availability, find_gpus | — |
