## Resumo Comparativo

| Estratégia | Modelo | Acurácia | Erros | Latência Média (ms) | Prompt Tokens (média) | Total Tokens (média) | Chamadas LLM | Uso de Tool Esperada |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `prompt_stuffing` | `llama3.2:3b` | 10/16 (62.5%) | 0 | 840.5 | 682.9 | 733.8 | 1.00 | — |
| `tool_calling` | `llama3.2:3b` | 11/16 (68.8%) | 0 | 1193.1 | 1366.4 | 1427.2 | 2.00 | 100.0% |

## Detalhamento por Caso

| Caso | Categoria | Estratégia | Status | Latência (ms) | Tokens | Tools | Motivo (se falhou) |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `list_all_gpus` | `basic_lookup` | `prompt_stuffing` | PASS | 1195 | 473 | — | — |
| `check_two_a100` | `basic_lookup` | `prompt_stuffing` | FAIL | 263 | 441 | — | contained forbidden term 'nao,' |
| `check_vram_l40s` | `basic_lookup` | `prompt_stuffing` | PASS | 385 | 454 | — | — |
| `exceeds_available_h100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 631 | 474 | — | — |
| `partial_usage_a100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 303 | 441 | — | — |
| `zero_available_4090` | `availability_and_bounds` | `prompt_stuffing` | PASS | 360 | 449 | — | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `prompt_stuffing` | FAIL | 633 | 472 | — | contained forbidden term 'A40' |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `prompt_stuffing` | FAIL | 2559 | 616 | — | missing required term '16' |
| `total_fleet_vram` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 377 | 459 | — | — |
| `nonexistent_b200` | `anti_hallucination` | `prompt_stuffing` | PASS | 491 | 459 | — | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `prompt_stuffing` | PASS | 561 | 468 | — | — |
| `out_of_scope_reservation` | `anti_hallucination` | `prompt_stuffing` | PASS | 1037 | 504 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `prompt_stuffing` | FAIL | 938 | 1481 | — | missing required term '141' |
| `scaled_filter_ge_100gb` | `scaled_stress` | `prompt_stuffing` | FAIL | 3028 | 1637 | — | missing required term 'H200'; contained forbidden term 'Arc A750' |
| `scaled_zero_l4` | `scaled_stress` | `prompt_stuffing` | PASS | 228 | 1447 | — | — |
| `scaled_intel_ge_48gb` | `scaled_stress` | `prompt_stuffing` | FAIL | 460 | 1465 | — | missing required term 'Max 1550'; missing required term 'Max 1100' |
| `list_all_gpus` | `basic_lookup` | `tool_calling` | PASS | 2045 | 1634 | list_gpus | — |
| `check_two_a100` | `basic_lookup` | `tool_calling` | PASS | 681 | 1348 | check_availability | — |
| `check_vram_l40s` | `basic_lookup` | `tool_calling` | PASS | 985 | 1357 | find_gpus | — |
| `exceeds_available_h100` | `availability_and_bounds` | `tool_calling` | PASS | 1058 | 1384 | check_availability | — |
| `partial_usage_a100` | `availability_and_bounds` | `tool_calling` | FAIL | 950 | 1363 | check_availability | missing any of ['nao', 'apenas 1', 'somente 1', 'so 1', 'insuficiente'] |
| `zero_available_4090` | `availability_and_bounds` | `tool_calling` | PASS | 968 | 1385 | check_availability | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 1173 | 1419 | find_gpus | — |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `tool_calling` | FAIL | 1047 | 1320 | list_gpus | missing required term '16' |
| `total_fleet_vram` | `aggregation_and_filtering` | `tool_calling` | FAIL | 879 | 1583 | list_gpus | missing required term '1032' |
| `nonexistent_b200` | `anti_hallucination` | `tool_calling` | PASS | 1588 | 1620 | list_gpus | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `tool_calling` | FAIL | 850 | 1327 | check_availability | missing required term '80' |
| `out_of_scope_reservation` | `anti_hallucination` | `tool_calling` | PASS | 1201 | 1398 | check_availability | — |
| `scaled_needle_h200` | `scaled_stress` | `tool_calling` | PASS | 1195 | 1389 | find_gpus | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `tool_calling` | PASS | 2101 | 1616 | find_gpus | — |
| `scaled_zero_l4` | `scaled_stress` | `tool_calling` | PASS | 895 | 1366 | check_availability | — |
| `scaled_intel_ge_48gb` | `scaled_stress` | `tool_calling` | FAIL | 1476 | 1327 | find_gpus | missing required term 'Max 1550'; missing required term 'Max 1100' |
