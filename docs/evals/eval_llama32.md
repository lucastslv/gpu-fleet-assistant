## Resumo Comparativo

| Estratégia | Modelo | Acurácia | Erros | Latência Média (ms) | Prompt Tokens (média) | Total Tokens (média) | Chamadas LLM | Uso de Tool Esperada |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `prompt_stuffing` | `llama3.2:3b` | 10/15 (66.7%) | 0 | 1859.8 | 674.5 | 786.5 | 1.00 | — |
| `tool_calling` | `llama3.2:3b` | 11/15 (73.3%) | 0 | 1511.9 | 1241.5 | 1314.5 | 2.00 | 100.0% |

## Detalhamento por Caso

| Caso | Categoria | Estratégia | Status | Latência (ms) | Tokens | Tools | Motivo (se falhou) |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `list_all_gpus` | `basic_lookup` | `prompt_stuffing` | PASS | 1116 | 473 | — | — |
| `check_two_a100` | `basic_lookup` | `prompt_stuffing` | FAIL | 319 | 441 | — | contained forbidden term 'nao,' |
| `check_vram_l40s` | `basic_lookup` | `prompt_stuffing` | PASS | 424 | 454 | — | — |
| `exceeds_available_h100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 724 | 474 | — | — |
| `partial_usage_a100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 397 | 441 | — | — |
| `zero_available_4090` | `availability_and_bounds` | `prompt_stuffing` | PASS | 415 | 449 | — | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `prompt_stuffing` | FAIL | 705 | 472 | — | contained forbidden term 'A40' |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `prompt_stuffing` | FAIL | 2614 | 616 | — | missing required term '16' |
| `total_fleet_vram` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 449 | 459 | — | — |
| `nonexistent_b200` | `anti_hallucination` | `prompt_stuffing` | PASS | 529 | 459 | — | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `prompt_stuffing` | PASS | 632 | 468 | — | — |
| `out_of_scope_reservation` | `anti_hallucination` | `prompt_stuffing` | PASS | 1125 | 504 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `prompt_stuffing` | FAIL | 898 | 1678 | — | missing required term '141' |
| `scaled_filter_ge_100gb` | `scaled_stress` | `prompt_stuffing` | FAIL | 16832 | 2722 | — | contained forbidden term 'V100'; contained forbidden term 'T4' |
| `scaled_zero_l4` | `scaled_stress` | `prompt_stuffing` | PASS | 716 | 1688 | — | — |
| `list_all_gpus` | `basic_lookup` | `tool_calling` | PASS | 4393 | 1642 | list_gpus | — |
| `check_two_a100` | `basic_lookup` | `tool_calling` | PASS | 1176 | 1226 | check_availability | — |
| `check_vram_l40s` | `basic_lookup` | `tool_calling` | PASS | 949 | 1426 | list_gpus | — |
| `exceeds_available_h100` | `availability_and_bounds` | `tool_calling` | PASS | 1024 | 1236 | check_availability | — |
| `partial_usage_a100` | `availability_and_bounds` | `tool_calling` | FAIL | 1190 | 1226 | check_availability | missing any of ['nao', 'apenas 1', 'somente 1', 'so 1', 'insuficiente'] |
| `zero_available_4090` | `availability_and_bounds` | `tool_calling` | PASS | 1215 | 1251 | check_availability | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 1219 | 1271 | find_gpus | — |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `tool_calling` | FAIL | 3050 | 1302 | list_gpus | missing required term '16' |
| `total_fleet_vram` | `aggregation_and_filtering` | `tool_calling` | FAIL | 1216 | 1449 | list_gpus | missing required term '1032' |
| `nonexistent_b200` | `anti_hallucination` | `tool_calling` | PASS | 857 | 1417 | list_gpus | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `tool_calling` | FAIL | 1259 | 1244 | check_availability | missing required term '80'; missing any of ['nao', '80 gb', '80gb'] |
| `out_of_scope_reservation` | `anti_hallucination` | `tool_calling` | PASS | 1197 | 1242 | check_availability | — |
| `scaled_needle_h200` | `scaled_stress` | `tool_calling` | PASS | 1200 | 1251 | check_availability | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `tool_calling` | PASS | 1267 | 1218 | find_gpus | — |
| `scaled_zero_l4` | `scaled_stress` | `tool_calling` | PASS | 1466 | 1316 | check_availability | — |
