import React from "react";
import { authAxios, useAuthStore } from "$auth/state/auth";

export const useAuthEffect = () => {
    const authStore = useAuthStore();

    // Restore Authorization header after page refresh (it lives in-memory on authAxios)
    React.useEffect(() => {
        if (authStore.isAuthenticated && authStore.bearerToken) {
            authAxios.defaults.headers.common = {
                Authorization: `Bearer ${authStore.bearerToken}`,
            };
        }
    }, [authStore.bearerToken, authStore.isAuthenticated]);

    return React.useEffect(() => {
        if (authStore.expires && authStore.expires < Date.now()) {
            authStore.logout();
        }
    }, [authStore.expires]);
};
