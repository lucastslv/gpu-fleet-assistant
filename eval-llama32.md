## Resumo Comparativo

| Estratégia | Modelo | Acurácia | Erros | Latência Média (ms) | Prompt Tokens (média) | Total Tokens (média) | Chamadas LLM | Uso de Tool Esperada |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `prompt_stuffing` | `llama3.2:3b` | 11/15 (73.3%) | 0 | 1880.7 | 674.5 | 786.5 | 1.00 | — |
| `tool_calling` | `llama3.2:3b` | 11/15 (73.3%) | 0 | 1433.2 | 1227.9 | 1299.1 | 2.00 | 100.0% |

## Detalhamento por Caso

| Caso | Categoria | Estratégia | Status | Latência (ms) | Tokens | Tools | Motivo (se falhou) |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `list_all_gpus` | `basic_lookup` | `prompt_stuffing` | PASS | 1249 | 473 | — | — |
| `check_two_a100` | `basic_lookup` | `prompt_stuffing` | PASS | 360 | 441 | — | — |
| `check_vram_l40s` | `basic_lookup` | `prompt_stuffing` | PASS | 453 | 454 | — | — |
| `exceeds_available_h100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 669 | 474 | — | — |
| `partial_usage_a100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 390 | 441 | — | — |
| `zero_available_4090` | `availability_and_bounds` | `prompt_stuffing` | PASS | 438 | 449 | — | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `prompt_stuffing` | FAIL | 715 | 472 | — | contained forbidden term 'A40' |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `prompt_stuffing` | FAIL | 2647 | 616 | — | missing required term '16' |
| `total_fleet_vram` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 403 | 459 | — | — |
| `nonexistent_b200` | `anti_hallucination` | `prompt_stuffing` | PASS | 584 | 459 | — | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `prompt_stuffing` | PASS | 648 | 468 | — | — |
| `out_of_scope_reservation` | `anti_hallucination` | `prompt_stuffing` | PASS | 1125 | 504 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `prompt_stuffing` | FAIL | 921 | 1678 | — | missing required term '141' |
| `scaled_filter_ge_100gb` | `scaled_stress` | `prompt_stuffing` | FAIL | 16882 | 2722 | — | contained forbidden term 'V100'; contained forbidden term 'T4' |
| `scaled_zero_l4` | `scaled_stress` | `prompt_stuffing` | PASS | 726 | 1688 | — | — |
| `list_all_gpus` | `basic_lookup` | `tool_calling` | PASS | 4365 | 1642 | list_gpus | — |
| `check_two_a100` | `basic_lookup` | `tool_calling` | PASS | 794 | 1191 | check_availability | — |
| `check_vram_l40s` | `basic_lookup` | `tool_calling` | PASS | 975 | 1426 | list_gpus | — |
| `exceeds_available_h100` | `availability_and_bounds` | `tool_calling` | PASS | 1113 | 1236 | check_availability | — |
| `partial_usage_a100` | `availability_and_bounds` | `tool_calling` | FAIL | 1162 | 1215 | check_availability | missing any of ['nao', 'apenas 1', 'somente 1', 'so 1', 'insuficiente'] |
| `zero_available_4090` | `availability_and_bounds` | `tool_calling` | PASS | 1209 | 1241 | check_availability | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 1281 | 1271 | find_gpus | — |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `tool_calling` | FAIL | 2916 | 1302 | list_gpus | missing required term '16' |
| `total_fleet_vram` | `aggregation_and_filtering` | `tool_calling` | FAIL | 1096 | 1449 | list_gpus | missing required term '1032' |
| `nonexistent_b200` | `anti_hallucination` | `tool_calling` | PASS | 859 | 1417 | list_gpus | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `tool_calling` | FAIL | 1141 | 1234 | check_availability | missing required term '80'; missing any of ['nao', '80 gb', '80gb'] |
| `out_of_scope_reservation` | `anti_hallucination` | `tool_calling` | PASS | 1144 | 1232 | check_availability | — |
| `scaled_needle_h200` | `scaled_stress` | `tool_calling` | PASS | 1126 | 1241 | check_availability | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `tool_calling` | PASS | 1149 | 1218 | find_gpus | — |
| `scaled_zero_l4` | `scaled_stress` | `tool_calling` | PASS | 1170 | 1172 | check_availability | — |
