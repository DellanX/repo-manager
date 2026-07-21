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
