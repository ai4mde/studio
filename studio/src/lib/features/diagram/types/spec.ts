type ClassNode = {
    type: "class";
    name: string;
    properties: string[];
};

type EnumNode = {
    type: "enum";
    name: string;
};

type ClassDiagramNode = {
    diagram: "class";
} & (ClassNode | EnumNode);

type ActorNode = {
    type: "actor";
    name: string;
    usecase: string;
};

type UsecaseDiagramNode = {
    diagram: "usecase";
} & ActorNode;

type DiagramNode = UsecaseDiagramNode | ClassDiagramNode;

export const node: DiagramNode = {
    name: "className",
    diagram: "class",
    type: "class",
    properties: [""],
};
