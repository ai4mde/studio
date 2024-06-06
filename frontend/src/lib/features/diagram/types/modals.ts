export type NewNodeModalState = {
    active: boolean;
    open: () => void;
    close: () => void;
};

export type NewConnectionModalState = {
    active: boolean;
    source?: string;
    target?: string;
    open: (source: string, target: string) => void;
    close: () => void;
};

export type EditNodeModalState = {
    active: boolean;
    node?: string;
    open: (node: string) => void;
    close: () => void;
};

export type EditConnectionModalState = {
    active: boolean;
    edge?: string;
    open: (edge: string) => void;
    close: () => void;
};
