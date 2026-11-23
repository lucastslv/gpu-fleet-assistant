## Resumo Comparativo

| Estratégia | Modelo | Acurácia | Erros | Latência Média (ms) | Prompt Tokens (média) | Total Tokens (média) | Chamadas LLM | Uso de Tool Esperada |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `prompt_stuffing` | `deepseek-flash` | 16/16 (100.0%) | 0 | 2024.8 | 696.5 | 893.1 | 1.00 | — |
| `tool_calling` | `deepseek-flash` | 16/16 (100.0%) | 0 | 3212.1 | 2404.2 | 2614.4 | 2.06 | 100.0% |

## Detalhamento por Caso

| Caso | Categoria | Estratégia | Status | Latência (ms) | Tokens | Tools | Motivo (se falhou) |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `list_all_gpus` | `basic_lookup` | `prompt_stuffing` | PASS | 2134 | 656 | — | — |
| `check_two_a100` | `basic_lookup` | `prompt_stuffing` | PASS | 1959 | 536 | — | — |
| `check_vram_l40s` | `basic_lookup` | `prompt_stuffing` | PASS | 1140 | 487 | — | — |
| `exceeds_available_h100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 2756 | 612 | — | — |
| `partial_usage_a100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 1300 | 557 | — | — |
| `zero_available_4090` | `availability_and_bounds` | `prompt_stuffing` | PASS | 2904 | 824 | — | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 1571 | 602 | — | — |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 2373 | 666 | — | — |
| `total_fleet_vram` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 1371 | 593 | — | — |
| `nonexistent_b200` | `anti_hallucination` | `prompt_stuffing` | PASS | 1686 | 530 | — | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `prompt_stuffing` | PASS | 2064 | 704 | — | — |
| `out_of_scope_reservation` | `anti_hallucination` | `prompt_stuffing` | PASS | 3294 | 787 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `prompt_stuffing` | PASS | 1664 | 1593 | — | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `prompt_stuffing` | PASS | 2724 | 1806 | — | — |
| `scaled_zero_l4` | `scaled_stress` | `prompt_stuffing` | PASS | 1714 | 1641 | — | — |
| `scaled_intel_ge_48gb` | `scaled_stress` | `prompt_stuffing` | PASS | 1743 | 1695 | — | — |
| `list_all_gpus` | `basic_lookup` | `tool_calling` | PASS | 3413 | 2694 | list_gpus | — |
| `check_two_a100` | `basic_lookup` | `tool_calling` | PASS | 4669 | 2388 | check_availability | — |
| `check_vram_l40s` | `basic_lookup` | `tool_calling` | PASS | 2728 | 2370 | find_gpus | — |
| `exceeds_available_h100` | `availability_and_bounds` | `tool_calling` | PASS | 3647 | 2586 | check_availability | — |
| `partial_usage_a100` | `availability_and_bounds` | `tool_calling` | PASS | 3330 | 2465 | check_availability | — |
| `zero_available_4090` | `availability_and_bounds` | `tool_calling` | PASS | 2876 | 2519 | check_availability | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 2709 | 2478 | find_gpus | — |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 2823 | 2610 | find_gpus | — |
| `total_fleet_vram` | `aggregation_and_filtering` | `tool_calling` | PASS | 2591 | 2273 | get_fleet_summary | — |
| `nonexistent_b200` | `anti_hallucination` | `tool_calling` | PASS | 4810 | 4085 | check_availability, list_gpus | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `tool_calling` | PASS | 2898 | 2508 | find_gpus | — |
| `out_of_scope_reservation` | `anti_hallucination` | `tool_calling` | PASS | 3843 | 2667 | check_availability | — |
| `scaled_needle_h200` | `scaled_stress` | `tool_calling` | PASS | 2177 | 2427 | check_availability | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `tool_calling` | PASS | 2874 | 2718 | find_gpus | — |
| `scaled_zero_l4` | `scaled_stress` | `tool_calling` | PASS | 3297 | 2441 | check_availability | — |
| `scaled_intel_ge_48gb` | `scaled_stress` | `tool_calling` | PASS | 2709 | 2602 | find_gpus | — |
