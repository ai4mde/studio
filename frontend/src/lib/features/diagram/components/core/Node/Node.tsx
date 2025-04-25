import {
    ActionNode,
    ActorNode,
    ClassNode,
    DecisionNode,
    EnumNode,
    FinalNode,
    ForkNode,
    InitialNode,
    JoinNode,
    MergeNode,
    PostconditionNode,
    PreconditionNode,
    ScenarioNode,
    SignalNode,
    SystemNode,
    TriggerNode,
    UsecaseNode,
} from "$diagram/components/nodes";
import React from "react";
import { NodeProps, NodeTypes } from "reactflow";

export const Node: React.FC<NodeProps> = () => {
    return <div className="p-4 bg-white">Node</div>;
};

export const nodeTypes: NodeTypes = {
    class: ClassNode,
    enum: EnumNode,
    signal: SignalNode,
    action: ActionNode,
    initial: InitialNode,
    decision: DecisionNode,
    merge: MergeNode,
    fork: ForkNode,
    join: JoinNode,
    final: FinalNode,
    actor: ActorNode,
    postcondition: PostconditionNode,
    precondition: PreconditionNode,
    scenario: ScenarioNode,
    system: SystemNode,
    trigger: TriggerNode,
    usecase: UsecaseNode,
    default: Node,
};

export const PreviewNode: React.FC<NodeProps> = (node) => {
    const Elem = nodeTypes[node.type] ?? Node;
    node.data._preview = true;

    return <Elem {...node} />;
};
