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
    C4ContainerNode,
    C4ComponentNode,
    ObjectNode,
    EventNode,
    ComponentNode,
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
    container: ComponentNode,
    component: ComponentNode,
    system: ComponentNode,
    interface: ClassifierNode,
    action: ActionNode,
    initial: InitialNode,
    decision: DecisionNode,
    merge: MergeNode,
    fork: ForkNode,
    join: JoinNode,
    final: FinalNode,
    object: ObjectNode,
    event: EventNode,
    actor: ActorNode,
    postcondition: PostconditionNode,
    precondition: PreconditionNode,
    scenario: ScenarioNode,
    trigger: TriggerNode,
    usecase: UsecaseNode,
    default: Node,
    swimlanegroup: SwimlaneGroupNode,
    system_boundary: SystemBoundaryNode,
    c4container: C4ContainerNode,
    c4component: C4ComponentNode,
};

export const PreviewNode: React.FC<NodeProps> = (node) => {
    const Elem = nodeTypes[node.type] ?? Node;
    node.data._preview = true;

    return <Elem {...node} />;
};
