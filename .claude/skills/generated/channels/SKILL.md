---
name: channels
description: "Skill for the Channels area of CusAgents. 14 symbols across 3 files."
---

# Channels

14 symbols | 3 files | Cohesion: 68%

## When to Use

- Working with code in `app/`
- Understanding how main, build_client, start work
- Modifying channels-related functionality

## Key Files

| File | Symbols |
|------|---------|
| `app/channels/feishu_long_connection.py` | build_client, start, connect_check, _connect_once, _cancel_pending_tasks (+3) |
| `tests/channels/test_feishu_long_connection.py` | test_long_connection_client_builder_uses_sdk_client_and_registers_handler, test_long_connection_runner_can_connect_check_without_blocking, test_long_connection_runner_connect_check_cancels_pending_tasks, FakeEventDispatcherBuilder, builder |
| `scripts/run_feishu_long_connection.py` | main |

## Entry Points

Start here when exploring this area:

- **`main`** (Function) — `scripts/run_feishu_long_connection.py:13`
- **`build_client`** (Function) — `app/channels/feishu_long_connection.py:84`
- **`start`** (Function) — `app/channels/feishu_long_connection.py:100`
- **`connect_check`** (Function) — `app/channels/feishu_long_connection.py:105`
- **`build_feishu_long_connection_handler`** (Function) — `app/channels/feishu_long_connection.py:132`

## Key Symbols

| Symbol | Type | File | Line |
|--------|------|------|------|
| `FeishuLongConnectionHandler` | Class | `app/channels/feishu_long_connection.py` | 17 |
| `FeishuLongConnectionRunner` | Class | `app/channels/feishu_long_connection.py` | 71 |
| `FakeEventDispatcherBuilder` | Class | `tests/channels/test_feishu_long_connection.py` | 147 |
| `main` | Function | `scripts/run_feishu_long_connection.py` | 13 |
| `build_client` | Function | `app/channels/feishu_long_connection.py` | 84 |
| `start` | Function | `app/channels/feishu_long_connection.py` | 100 |
| `connect_check` | Function | `app/channels/feishu_long_connection.py` | 105 |
| `build_feishu_long_connection_handler` | Function | `app/channels/feishu_long_connection.py` | 132 |
| `test_long_connection_client_builder_uses_sdk_client_and_registers_handler` | Function | `tests/channels/test_feishu_long_connection.py` | 142 |
| `test_long_connection_runner_can_connect_check_without_blocking` | Function | `tests/channels/test_feishu_long_connection.py` | 202 |
| `test_long_connection_runner_connect_check_cancels_pending_tasks` | Function | `tests/channels/test_feishu_long_connection.py` | 254 |
| `builder` | Function | `tests/channels/test_feishu_long_connection.py` | 161 |
| `_connect_once` | Function | `app/channels/feishu_long_connection.py` | 120 |
| `_cancel_pending_tasks` | Function | `app/channels/feishu_long_connection.py` | 124 |

## Execution Flows

| Flow | Type | Steps |
|------|------|-------|
| `Main → Settings` | cross_community | 3 |
| `Main → FeishuLongConnectionHandler` | cross_community | 3 |

## Connected Areas

| Area | Connections |
|------|-------------|
| Commands | 3 calls |
| Workers | 1 calls |
| Scripts | 1 calls |

## How to Explore

1. `gitnexus_context({name: "main"})` — see callers and callees
2. `gitnexus_query({query: "channels"})` — find related execution flows
3. Read key files listed above for implementation details
