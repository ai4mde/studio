import React from "react";
import { useAuthStore } from "$auth/state/auth";

export const useAuthEffect = () => {
    const authStore = useAuthStore();

    return React.useEffect(() => {
        if (authStore.expires && authStore.expires < Date.now()) {
            authStore.logout();
        }
    }, [authStore.expires]);
};
