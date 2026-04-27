import { baseURL } from "$shared/globals";
import axios from "axios";
import type { AxiosError } from "axios";
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
    login: (username: string, password: string) => Promise<{ ok: boolean; message?: string }>;
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
                login: async (username, password) => {
                    try {
                        const { data } = await authAxios
                        .post("v1/auth/token", {
                            username: username.trim(),
                            password,
                        });

                        const tokenData = decodeJwt(data.token);
                        authAxios.defaults.headers.common = {
                            Authorization: `Bearer ${data.token}`,
                        };
                        set(() => ({
                            isAuthenticated: true,
                            bearerToken: data.token,
                            expires: typeof tokenData.exp === "number" ? tokenData.exp * 1000 : undefined,
                            user: {
                                ...data,
                            },
                            tokenData,
                        }));

                        return { ok: true };
                    } catch (error) {
                        const responseMessage = (error as AxiosError<{ message?: string }>).response?.data?.message;
                        set(() => ({
                            isAuthenticated: false,
                            bearerToken: undefined,
                            expires: undefined,
                            user: undefined,
                            tokenData: undefined,
                        }));
                        return { ok: false, message: responseMessage || "Login failed." };
                    }
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
