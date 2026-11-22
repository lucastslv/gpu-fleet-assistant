## Resumo Comparativo

| Estratégia | Modelo | Acurácia | Erros | Latência Média (ms) | Prompt Tokens (média) | Total Tokens (média) | Chamadas LLM | Uso de Tool Esperada |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `prompt_stuffing` | `llama3.2:3b` | 10/15 (66.7%) | 0 | 1960.7 | 674.5 | 785.0 | 1.00 | — |
| `tool_calling` | `llama3.2:3b` | 11/15 (73.3%) | 0 | 1455.5 | 1224.5 | 1295.0 | 2.00 | 100.0% |

## Detalhamento por Caso

| Caso | Categoria | Estratégia | Status | Latência (ms) | Tokens | Tools | Motivo (se falhou) |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `list_all_gpus` | `basic_lookup` | `prompt_stuffing` | PASS | 3183 | 473 | — | — |
| `check_two_a100` | `basic_lookup` | `prompt_stuffing` | FAIL | 282 | 441 | — | contained forbidden term 'nao,' |
| `check_vram_l40s` | `basic_lookup` | `prompt_stuffing` | PASS | 395 | 454 | — | — |
| `exceeds_available_h100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 648 | 474 | — | — |
| `partial_usage_a100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 340 | 441 | — | — |
| `zero_available_4090` | `availability_and_bounds` | `prompt_stuffing` | PASS | 366 | 449 | — | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `prompt_stuffing` | FAIL | 700 | 472 | — | contained forbidden term 'A40' |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `prompt_stuffing` | FAIL | 2640 | 616 | — | missing required term '16' |
| `total_fleet_vram` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 416 | 459 | — | — |
| `nonexistent_b200` | `anti_hallucination` | `prompt_stuffing` | PASS | 520 | 459 | — | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `prompt_stuffing` | PASS | 585 | 468 | — | — |
| `out_of_scope_reservation` | `anti_hallucination` | `prompt_stuffing` | PASS | 809 | 484 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `prompt_stuffing` | FAIL | 938 | 1678 | — | missing required term '141' |
| `scaled_filter_ge_100gb` | `scaled_stress` | `prompt_stuffing` | FAIL | 16889 | 2722 | — | contained forbidden term 'V100'; contained forbidden term 'T4' |
| `scaled_zero_l4` | `scaled_stress` | `prompt_stuffing` | PASS | 701 | 1685 | — | — |
| `list_all_gpus` | `basic_lookup` | `tool_calling` | PASS | 4352 | 1642 | list_gpus | — |
| `check_two_a100` | `basic_lookup` | `tool_calling` | PASS | 730 | 1191 | check_availability | — |
| `check_vram_l40s` | `basic_lookup` | `tool_calling` | PASS | 878 | 1426 | list_gpus | — |
| `exceeds_available_h100` | `availability_and_bounds` | `tool_calling` | PASS | 1111 | 1236 | check_availability | — |
| `partial_usage_a100` | `availability_and_bounds` | `tool_calling` | FAIL | 1118 | 1215 | check_availability | missing any of ['nao', 'apenas 1', 'somente 1', 'so 1', 'insuficiente'] |
| `zero_available_4090` | `availability_and_bounds` | `tool_calling` | PASS | 1235 | 1241 | check_availability | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 1267 | 1271 | find_gpus | — |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `tool_calling` | FAIL | 2989 | 1302 | list_gpus | missing required term '16' |
| `total_fleet_vram` | `aggregation_and_filtering` | `tool_calling` | FAIL | 1194 | 1449 | list_gpus | missing required term '1032' |
| `nonexistent_b200` | `anti_hallucination` | `tool_calling` | PASS | 851 | 1417 | list_gpus | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `tool_calling` | FAIL | 1013 | 1172 | check_availability | missing required term '80' |
| `out_of_scope_reservation` | `anti_hallucination` | `tool_calling` | PASS | 1177 | 1232 | check_availability | — |
| `scaled_needle_h200` | `scaled_stress` | `tool_calling` | PASS | 1224 | 1241 | check_availability | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `tool_calling` | PASS | 1326 | 1218 | find_gpus | — |
| `scaled_zero_l4` | `scaled_stress` | `tool_calling` | PASS | 1369 | 1172 | check_availability | — |
