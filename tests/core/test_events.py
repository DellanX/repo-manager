from src.core.events import OperationEventStore, serialize_events


def test_t_events_id_monotonic_and_starts_at_1() -> None:
    """T-EVENTS-ID-MONOTONIC"""
    store = OperationEventStore()

    first = store.record("service", "read_file", "completed", {"path": "a.txt"})
    second = store.record("service", "write_file", "completed", {"path": "a.txt"})

    assert first.id == 1
    assert second.id == 2


def test_t_events_list_since_filters_ids() -> None:
    """T-EVENTS-LIST-SINCE"""
    store = OperationEventStore()
    store.record("service", "op1", "completed", {})
    second = store.record("service", "op2", "completed", {})
    store.record("service", "op3", "completed", {})

    items = store.list_since(second.id)
    assert len(items) == 1
    assert items[0].operation == "op3"


def test_t_events_serialize_shape() -> None:
    """T-EVENTS-SERIALIZE-SHAPE"""
    store = OperationEventStore()
    event = store.record("service", "clone", "completed", {"url": "u"})

    serialized = serialize_events([event])
    assert isinstance(serialized, list)
    assert set(serialized[0].keys()) == {"id", "ts", "layer", "operation", "status", "payload"}
