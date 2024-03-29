import { baseURL } from "$shared/globals";
import axios from "axios";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import { decodeJwt } from "jose";

type AuthStore = {
    isAuthenticated: boolean;
    bearerToken?: string;
    expires?: number;
    user?: {
        id: string;
        email: string;
        username: string;
    };
    tokenData?: any;
    login: (username: string, password: string) => void;
    logout: () => void;
};

axios.defaults.withCredentials = true;
axios.defaults.withXSRFToken = true;

export const authAxios = axios.create({
    baseURL: baseURL,
    withCredentials: true,
    xsrfCookieName: "csrftoken",
    xsrfHeaderName: "X-CSRFTOKEN",
    withXSRFToken: true,
});

export const useAuthStore = create(
    persist<AuthStore>(
        (set) => {
            return {
                isAuthenticated: false,

                // Action to set authentication status and user data
                login: (username, password) => {
                    authAxios
                        .post("v1/auth/token", {
                            username: username,
                            password: password,
                        })
                        .then(({ data }) => {
                            authAxios.defaults.headers.common = {
                                Authorization: `Bearer ${data.token}`,
                            };
                            set(() => ({
                                isAuthenticated: true,
                                bearerToken: data.token,
                                expires: Date.now() + 1000 * 3600,
                                user: {
                                    ...data,
                                },
                                tokenData: decodeJwt(data.token),
                            }));
                        })
                        .catch(() => {
                            set(() => ({
                                isAuthenticated: false,
                                expires: undefined,
                                user: undefined,
                            }));
                        });
                },

                // Action to reset authentication status and user data
                logout: () => {
                    authAxios.post("v1/auth/logout");
                    authAxios.defaults.headers.common = {
                        Authorization: null,
                    };
                    set(() => ({
                        isAuthenticated: false,
                        expires: undefined,
                        user: undefined,
                        tokenData: undefined,
                    }));
                },
            };
        },
        {
            name: "auth-storage",
            storage: createJSONStorage(() => localStorage), // TODO: Make this localStorage
        },
    ),
);
