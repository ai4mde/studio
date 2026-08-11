import pytest

from .human_edit_synchronizer import (
    HumanEditSynchronizationError,
    _derive_topology_and_semantics_from_graph,
)


def _linear_graph(*actions: str):
    nodes = [{"id": "initial", "type": "initial"}]
    nodes.extend(
        {"id": f"action_{index}", "type": "action", "name": action}
        for index, action in enumerate(actions, start=1)
    )
    nodes.append({"id": "final", "type": "final"})
    node_ids = ["initial", *(f"action_{index}" for index in range(1, len(actions) + 1)), "final"]
    return {
        "nodes": nodes,
        "edges": [
            {"source": source, "target": target, "type": "control"}
            for source, target in zip(node_ids, node_ids[1:])
        ],
    }


def _decision_graph(*, root_before=(), root_after=()):
    nodes = [{"id": "initial", "type": "initial"}]
    nodes.extend(
        {"id": f"before_{index}", "type": "action", "name": action}
        for index, action in enumerate(root_before, start=1)
    )
    nodes.extend(
        [
            {"id": "decision", "type": "decision", "label": "route request"},
            {"id": "approved", "type": "action", "name": "approve request"},
            {"id": "rejected", "type": "action", "name": "reject request"},
            {"id": "merge", "type": "merge"},
        ]
    )
    nodes.extend(
        {"id": f"after_{index}", "type": "action", "name": action}
        for index, action in enumerate(root_after, start=1)
    )
    nodes.append({"id": "final", "type": "final"})

    before_ids = [f"before_{index}" for index in range(1, len(root_before) + 1)]
    after_ids = [f"after_{index}" for index in range(1, len(root_after) + 1)]
    root_prefix = ["initial", *before_ids, "decision"]
    root_suffix = ["merge", *after_ids, "final"]
    return {
        "nodes": nodes,
        "edges": [
            *(
                {"source": source, "target": target, "type": "control"}
                for source, target in zip(root_prefix, root_prefix[1:])
            ),
            {"source": "decision", "target": "approved", "type": "control", "label": "approved"},
            {"source": "decision", "target": "rejected", "type": "control", "label": "rejected"},
            {"source": "approved", "target": "merge", "type": "control"},
            {"source": "rejected", "target": "merge", "type": "control"},
            *(
                {"source": source, "target": target, "type": "control"}
                for source, target in zip(root_suffix, root_suffix[1:])
            ),
        ],
    }


def _semantic_plan(graph):
    _, semantic_plan, _ = _derive_topology_and_semantics_from_graph(graph)
    return semantic_plan


@pytest.mark.parametrize(
    ("actions", "expected"),
    [
        ((), []),
        (("review request",), [{"action": "review request"}]),
        (
            ("receive request", "review request", "record outcome"),
            [
                {"action": "receive request"},
                {"action": "review request"},
                {"action": "record outcome"},
            ],
        ),
    ],
)
def test_human_sync_supports_zero_one_or_multiple_actions_in_required_root_slot(actions, expected):
    semantic_plan = _semantic_plan(_linear_graph(*actions))

    assert semantic_plan["root_actions"] == [
        {"slot_id": "ROOT_START", "actions": expected}
    ]


def test_human_sync_preserves_shared_continuation_in_root_scope():
    semantic_plan = _semantic_plan(
        _decision_graph(root_before=("receive request",), root_after=("archive request",))
    )

    assert semantic_plan["root_actions"] == [
        {"slot_id": "ROOT_START", "actions": [{"action": "receive request"}]},
        {"slot_id": "AFTER_T1", "actions": [{"action": "archive request"}]},
    ]
    assert all(
        step["action"] != "archive request"
        for branch in semantic_plan["branch_plans"]
        for step in branch["steps"]
    )


def test_human_sync_preserves_consecutive_root_structures_with_empty_slots():
    graph = _decision_graph()
    graph["nodes"].extend(
        [
            {"id": "fork", "type": "fork", "label": "notify in parallel"},
            {"id": "notify_owner", "type": "action", "name": "notify owner"},
            {"id": "notify_auditor", "type": "action", "name": "notify auditor"},
            {"id": "join", "type": "join"},
        ]
    )
    graph["edges"] = [edge for edge in graph["edges"] if edge["source"] != "merge"]
    graph["edges"].extend(
        [
            {"source": "merge", "target": "fork", "type": "control"},
            {"source": "fork", "target": "notify_owner", "type": "control", "label": "owner"},
            {"source": "fork", "target": "notify_auditor", "type": "control", "label": "auditor"},
            {"source": "notify_owner", "target": "join", "type": "control"},
            {"source": "notify_auditor", "target": "join", "type": "control"},
            {"source": "join", "target": "final", "type": "control"},
        ]
    )

    semantic_plan = _semantic_plan(graph)

    assert semantic_plan["root_actions"] == [
        {"slot_id": "ROOT_START", "actions": []},
        {"slot_id": "AFTER_T1", "actions": []},
        {"slot_id": "AFTER_T2", "actions": []},
    ]


def test_human_sync_root_insert_and_delete_keep_ordered_action_list():
    inserted = _semantic_plan(_linear_graph("receive", "new review", "archive"))
    deleted = _semantic_plan(_linear_graph("receive", "archive"))

    assert inserted["root_actions"][0]["actions"] == [
        {"action": "receive"},
        {"action": "new review"},
        {"action": "archive"},
    ]
    assert deleted["root_actions"][0]["actions"] == [
        {"action": "receive"},
        {"action": "archive"},
    ]


def test_human_sync_never_invents_root_scope_placeholders():
    semantic_plan = _semantic_plan(_decision_graph(root_after=("archive request",)))

    assert "root_scope_" not in str(semantic_plan)


def test_human_sync_rejects_disconnected_manual_edit():
    graph = _linear_graph("review request")
    graph["nodes"].append({"id": "detached", "type": "action", "name": "detached review"})

    with pytest.raises(HumanEditSynchronizationError) as exc_info:
        _derive_topology_and_semantics_from_graph(graph)

    assert exc_info.value.diagnostics["issues"][0]["code"] == "graph_validation_failed"
