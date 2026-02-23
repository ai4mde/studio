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
    ClassifierNode,
    TriggerNode,
    UsecaseNode,
    SwimlaneGroupNode,
    SystemBoundaryNode,
} from "$diagram/components/nodes";
import React from "react";
import { NodeProps, NodeTypes } from "reactflow";

export const Node: React.FC<NodeProps> = () => {
    return <div className="p-4 bg-white">Node</div>;
};

export const nodeTypes: NodeTypes = {
    class: ClassNode,
    enum: EnumNode,
    signal: ClassifierNode,
    container: ClassifierNode,
    component: ClassifierNode,
    system: ClassifierNode,
    interface: ClassifierNode,
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
    trigger: TriggerNode,
    usecase: UsecaseNode,
    default: Node,
    swimlanegroup: SwimlaneGroupNode,
    system_boundary: SystemBoundaryNode,
};

export const PreviewNode: React.FC<NodeProps> = (node) => {
    const Elem = nodeTypes[node.type] ?? Node;
    node.data._preview = true;

    return <Elem {...node} />;
};
