## Resumo Comparativo

| Estratégia | Modelo | Acurácia | Erros | Latência Média (ms) | Prompt Tokens (média) | Total Tokens (média) | Chamadas LLM | Uso de Tool Esperada |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `prompt_stuffing` | `mistral-small-2603` | 16/16 (100.0%) | 0 | 1002.6 | 783.4 | 840.1 | 1.00 | — |
| `tool_calling` | `mistral-small-2603` | 16/16 (100.0%) | 0 | 1486.8 | 1804.7 | 1893.8 | 1.94 | 100.0% |

## Detalhamento por Caso

| Caso | Categoria | Estratégia | Status | Latência (ms) | Tokens | Tools | Motivo (se falhou) |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `list_all_gpus` | `basic_lookup` | `prompt_stuffing` | PASS | 1414 | 531 | — | — |
| `check_two_a100` | `basic_lookup` | `prompt_stuffing` | PASS | 567 | 487 | — | — |
| `check_vram_l40s` | `basic_lookup` | `prompt_stuffing` | PASS | 585 | 489 | — | — |
| `exceeds_available_h100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 834 | 519 | — | — |
| `partial_usage_a100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 2179 | 486 | — | — |
| `zero_available_4090` | `availability_and_bounds` | `prompt_stuffing` | PASS | 1144 | 496 | — | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 694 | 531 | — | — |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 1136 | 580 | — | — |
| `total_fleet_vram` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 534 | 491 | — | — |
| `nonexistent_b200` | `anti_hallucination` | `prompt_stuffing` | PASS | 1007 | 501 | — | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `prompt_stuffing` | PASS | 646 | 513 | — | — |
| `out_of_scope_reservation` | `anti_hallucination` | `prompt_stuffing` | PASS | 1075 | 546 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `prompt_stuffing` | PASS | 713 | 1777 | — | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `prompt_stuffing` | PASS | 1587 | 1954 | — | — |
| `scaled_zero_l4` | `scaled_stress` | `prompt_stuffing` | PASS | 1084 | 1743 | — | — |
| `scaled_intel_ge_48gb` | `scaled_stress` | `prompt_stuffing` | PASS | 842 | 1798 | — | — |
| `list_all_gpus` | `basic_lookup` | `tool_calling` | PASS | 1745 | 2196 | list_gpus | — |
| `check_two_a100` | `basic_lookup` | `tool_calling` | PASS | 1358 | 1887 | check_availability | — |
| `check_vram_l40s` | `basic_lookup` | `tool_calling` | PASS | 1155 | 1827 | find_gpus | — |
| `exceeds_available_h100` | `availability_and_bounds` | `tool_calling` | PASS | 1477 | 1903 | check_availability | — |
| `partial_usage_a100` | `availability_and_bounds` | `tool_calling` | PASS | 1233 | 1874 | check_availability | — |
| `zero_available_4090` | `availability_and_bounds` | `tool_calling` | PASS | 2103 | 1902 | check_availability | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 1522 | 1984 | find_gpus | — |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 2327 | 2163 | find_gpus | — |
| `total_fleet_vram` | `aggregation_and_filtering` | `tool_calling` | PASS | 1478 | 1790 | get_fleet_summary | — |
| `nonexistent_b200` | `anti_hallucination` | `tool_calling` | PASS | 1168 | 1805 | check_availability | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `tool_calling` | PASS | 1496 | 1910 | find_gpus | — |
| `out_of_scope_reservation` | `anti_hallucination` | `tool_calling` | PASS | 722 | 908 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `tool_calling` | PASS | 1343 | 2036 | check_availability, find_gpus | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `tool_calling` | PASS | 1813 | 2233 | find_gpus | — |
| `scaled_zero_l4` | `scaled_stress` | `tool_calling` | PASS | 1333 | 1857 | check_availability | — |
| `scaled_intel_ge_48gb` | `scaled_stress` | `tool_calling` | PASS | 1516 | 2026 | find_gpus | — |
