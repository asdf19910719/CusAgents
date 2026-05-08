---
name: llm
description: "Skill for the Llm area of CusAgents. 28 symbols across 7 files."
---

# Llm

28 symbols | 7 files | Cohesion: 84%

## When to Use

- Working with code in `app/`
- Understanding how generate_structured, build_transport, build_sequence_transport work
- Modifying llm-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `app/providers/llm/openai_compatible.py` | OpenAICompatibleProvider, generate_structured, _parse_structured_content, _extract_markdown_json, _extract_json_snippet (+6) |
| `tests/providers/test_llm_provider.py` | build_transport, build_sequence_transport, test_generate_text_parses_content_and_usage, test_generate_structured_parses_json_into_schema, test_generate_structured_extracts_json_from_markdown_fence (+4) |
| `app/providers/llm/base.py` | StructuredGenerationResult, BaseLlmProvider, TextGenerationResult |
| `tests/e2e/test_full_pipeline.py` | generate_structured, generate_text |
| `tests/services/test_storyboard_service.py` | generate_structured |
| `app/providers/llm/factory.py` | create_llm_provider |
| `tests/services/test_outline_service.py` | generate_text |

## Entry Points

Start here when exploring this area:

- **`generate_structured`** (Function) — `tests/services/test_storyboard_service.py:21`
- **`build_transport`** (Function) — `tests/providers/test_llm_provider.py:13`
- **`build_sequence_transport`** (Function) — `tests/providers/test_llm_provider.py:21`
- **`test_generate_text_parses_content_and_usage`** (Function) — `tests/providers/test_llm_provider.py:47`
- **`test_generate_structured_parses_json_into_schema`** (Function) — `tests/providers/test_llm_provider.py:79`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `OpenAICompatibleProvider` | Class | `app/providers/llm/openai_compatible.py` | 10 |
| `StructuredGenerationResult` | Class | `app/providers/llm/base.py` | 19 |
| `BaseLlmProvider` | Class | `app/providers/llm/base.py` | 29 |
| `TextGenerationResult` | Class | `app/providers/llm/base.py` | 9 |
| `generate_structured` | Function | `tests/services/test_storyboard_service.py` | 21 |
| `build_transport` | Function | `tests/providers/test_llm_provider.py` | 13 |
| `build_sequence_transport` | Function | `tests/providers/test_llm_provider.py` | 21 |
| `test_generate_text_parses_content_and_usage` | Function | `tests/providers/test_llm_provider.py` | 47 |
| `test_generate_structured_parses_json_into_schema` | Function | `tests/providers/test_llm_provider.py` | 79 |
| `test_generate_structured_extracts_json_from_markdown_fence` | Function | `tests/providers/test_llm_provider.py` | 110 |
| `test_generate_structured_repairs_non_json_with_second_pass` | Function | `tests/providers/test_llm_provider.py` | 139 |
| `generate_structured` | Function | `tests/e2e/test_full_pipeline.py` | 32 |
| `generate_structured` | Function | `app/providers/llm/openai_compatible.py` | 69 |
| `create_llm_provider` | Function | `app/providers/llm/factory.py` | 3 |
| `generate_text` | Function | `tests/services/test_outline_service.py` | 18 |
| `build_timeout_then_success_transport` | Function | `tests/providers/test_llm_provider.py` | 33 |
| `test_estimate_cost_returns_decimal_value` | Function | `tests/providers/test_llm_provider.py` | 189 |
| `test_generate_text_retries_once_on_read_timeout` | Function | `tests/providers/test_llm_provider.py` | 202 |
| `generate_text` | Function | `tests/e2e/test_full_pipeline.py` | 20 |
| `generate_text` | Function | `app/providers/llm/openai_compatible.py` | 56 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Run_configured_job → OpenAICompatibleProvider` | cross_community | 4 |
| `Generate_structured → Get` | cross_community | 4 |
| `Generate_structured → _request` | cross_community | 3 |
| `Generate_structured → TextGenerationResult` | cross_community | 3 |
| `Generate_structured → _extract_markdown_json` | intra_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Routes | 2 calls |

## How to Explore

1. `gitnexus_context({name: "generate_structured"})` — see callers and callees
2. `gitnexus_query({query: "llm"})` — find related execution flows
3. Read key files listed above for implementation details
