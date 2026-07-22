from src.core import events


def test_t_ws_welcome_first_message(client) -> None:
    """T-WS-WELCOME-200"""
    with client.websocket_connect("/ws/operations") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "welcome"
        assert "message" in msg
        assert "note" in msg


def test_t_ws_events_envelope_and_order(client) -> None:
    """T-WS-EVENTS-ORDER"""
    events.operation_events.record("service", "one", "completed", {})
    events.operation_events.record("service", "two", "completed", {})

    with client.websocket_connect("/ws/operations") as ws:
        welcome = ws.receive_json()
        assert welcome["type"] == "welcome"

        batch = ws.receive_json()
        assert batch["type"] == "events"

        items = batch["items"]
        ids = [item["id"] for item in items]
        assert ids == sorted(ids)
        assert len(ids) == len(set(ids))


def test_t_ws_disconnect_handled(client) -> None:
    """T-WS-DISCONNECT - WebSocket disconnect is handled gracefully"""
    ws = client.websocket_connect("/ws/operations")
    ws.__enter__()
    msg = ws.receive_json()
    assert msg["type"] == "welcome"
    # Close the connection to trigger WebSocketDisconnect on the server
    ws.close()
    # If we reach here without exception, disconnect was handled gracefully


def test_t_ws_no_duplicate_ids_per_session(client) -> None:
    """T-WS-NO-DUP-IDS: No duplicate event IDs within a session."""
    events.operation_events.record("service", "op1", "completed", {})
    events.operation_events.record("service", "op2", "completed", {})
    events.operation_events.record("service", "op3", "completed", {})

    with client.websocket_connect("/ws/operations") as ws:
        welcome = ws.receive_json()
        assert welcome["type"] == "welcome"

        batch = ws.receive_json()
        assert batch["type"] == "events"

        all_ids = [item["id"] for item in batch["items"]]
        # Verify all IDs are unique
        assert len(all_ids) == len(set(all_ids)), "Duplicate IDs found in event stream"
