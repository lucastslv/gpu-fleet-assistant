## Resumo Comparativo

| Estratégia | Modelo | Acurácia | Erros | Latência Média (ms) | Prompt Tokens (média) | Total Tokens (média) | Chamadas LLM | Uso de Tool Esperada |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `prompt_stuffing` | `mistral-large-4` | 15/16 (93.8%) | 0 | 3794.6 | 632.5 | 956.1 | 1.00 | — |
| `tool_calling` | `mistral-large-4` | 16/16 (100.0%) | 0 | 5347.8 | 1767.5 | 2040.1 | 2.06 | 100.0% |

## Detalhamento por Caso

| Caso | Categoria | Estratégia | Status | Latência (ms) | Tokens | Tools | Motivo (se falhou) |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| `list_all_gpus` | `basic_lookup` | `prompt_stuffing` | PASS | 2896 | 620 | — | — |
| `check_two_a100` | `basic_lookup` | `prompt_stuffing` | PASS | 2661 | 577 | — | — |
| `check_vram_l40s` | `basic_lookup` | `prompt_stuffing` | PASS | 1553 | 507 | — | — |
| `exceeds_available_h100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 3316 | 630 | — | — |
| `partial_usage_a100` | `availability_and_bounds` | `prompt_stuffing` | PASS | 1695 | 521 | — | — |
| `zero_available_4090` | `availability_and_bounds` | `prompt_stuffing` | PASS | 1809 | 531 | — | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 2296 | 650 | — | — |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 3800 | 805 | — | — |
| `total_fleet_vram` | `aggregation_and_filtering` | `prompt_stuffing` | PASS | 12397 | 798 | — | — |
| `nonexistent_b200` | `anti_hallucination` | `prompt_stuffing` | PASS | 2531 | 587 | — | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `prompt_stuffing` | PASS | 2235 | 580 | — | — |
| `out_of_scope_reservation` | `anti_hallucination` | `prompt_stuffing` | PASS | 5721 | 844 | — | — |
| `scaled_needle_h200` | `scaled_stress` | `prompt_stuffing` | PASS | 2681 | 1638 | — | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `prompt_stuffing` | PASS | 8885 | 2562 | — | — |
| `scaled_zero_l4` | `scaled_stress` | `prompt_stuffing` | PASS | 2039 | 1564 | — | — |
| `scaled_intel_ge_48gb` | `scaled_stress` | `prompt_stuffing` | FAIL | 4200 | 1883 | — | contained forbidden term 'Flex 170'; contained forbidden term 'Flex 140'; contained forbidden term 'A770'; contained forbidden term 'A750' |
| `list_all_gpus` | `basic_lookup` | `tool_calling` | PASS | 3103 | 2134 | list_gpus | — |
| `check_two_a100` | `basic_lookup` | `tool_calling` | PASS | 2467 | 1779 | check_availability | — |
| `check_vram_l40s` | `basic_lookup` | `tool_calling` | PASS | 2881 | 1778 | find_gpus | — |
| `exceeds_available_h100` | `availability_and_bounds` | `tool_calling` | PASS | 3437 | 1908 | check_availability | — |
| `partial_usage_a100` | `availability_and_bounds` | `tool_calling` | PASS | 17686 | 1873 | check_availability | — |
| `zero_available_4090` | `availability_and_bounds` | `tool_calling` | PASS | 5929 | 1836 | check_availability | — |
| `filter_ge_80gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 15887 | 2041 | find_gpus | — |
| `count_available_ge_48gb` | `aggregation_and_filtering` | `tool_calling` | PASS | 4154 | 2162 | find_gpus | — |
| `total_fleet_vram` | `aggregation_and_filtering` | `tool_calling` | PASS | 2953 | 1776 | get_fleet_summary | — |
| `nonexistent_b200` | `anti_hallucination` | `tool_calling` | PASS | 5815 | 3240 | check_availability, find_gpus, list_gpus | — |
| `wrong_vram_a100_40gb` | `anti_hallucination` | `tool_calling` | PASS | 3173 | 1935 | check_availability, find_gpus | — |
| `out_of_scope_reservation` | `anti_hallucination` | `tool_calling` | PASS | 4719 | 2085 | check_availability, find_gpus | — |
| `scaled_needle_h200` | `scaled_stress` | `tool_calling` | PASS | 2982 | 2023 | check_availability, find_gpus | — |
| `scaled_filter_ge_100gb` | `scaled_stress` | `tool_calling` | PASS | 3532 | 2227 | find_gpus | — |
| `scaled_zero_l4` | `scaled_stress` | `tool_calling` | PASS | 2694 | 1808 | check_availability | — |
| `scaled_intel_ge_48gb` | `scaled_stress` | `tool_calling` | PASS | 4152 | 2036 | find_gpus | — |
