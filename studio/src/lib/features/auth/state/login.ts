import { create } from "zustand";

type LoginStore = {
    loading: boolean;
    page: "login" | "register" | "forgot";
    setPage: (page: "login" | "register" | "forgot") => void;
    setLoading: (loading: boolean) => void;
};

export const useLoginStore = create<LoginStore>((set) => ({
    loading: false,
    page: "login",
    setPage: (page) => set({ page }),
    setLoading: (loading) => set({ loading }),
}));
