import { authAxios, useAuthStore } from "$auth/state/auth";

// Generator writes use the laboratory's existing Bearer token so they do not
// depend on its cookie authenticator, which currently disables CSRF checks.
export const generatorPost = <T>(url: string, body: unknown) => {
    const { bearerToken, isAuthenticated, expires } = useAuthStore.getState();
    if (!isAuthenticated || !bearerToken || !expires || expires <= Date.now()) {
        return Promise.reject(new Error("Sign in again to use the Generator."));
    }
    return authAxios.post<T>(url, body, {
        headers: { Authorization: `Bearer ${bearerToken}` },
    });
};
