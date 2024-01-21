import axios from "axios";
import { create } from "zustand";

type AuthStore = {
    isAuthenticated: boolean;
    expires?: number;
    user?: {
        id: string;
        email: string;
        username: string;
    };
    login: (username: string, password: string) => void;
    logout: () => void;
};

export const authAxios = axios.create({
    baseURL: "http://api.ai4mde.localhost/api/",
    withCredentials: true,
    xsrfCookieName: 'csrftoken',
    xsrfHeaderName: 'X-CSRFTOKEN',
});

export const useAuthStore = create<AuthStore>((set) => {
    const defaultState: AuthStore = {
        isAuthenticated: false,

        // Action to set authentication status and user data
        login: (username, password) => {
            authAxios.post('v1/auth/token', {
                username: username,
                password: password,
            }).then(({ data }) => {
                set(() => ({
                    isAuthenticated: true,
                    expires: Date.now() + 1000 * 3600,
                    user: {
                        ...data
                    },
                }))
            }).catch(() => {
                set(() => ({
                    isAuthenticated: false,
                    expires: undefined,
                    user: undefined,
                }))
            })
        },

        // Action to reset authentication status and user data
        logout: () => {
            authAxios.post('v1/auth/logout')
            set(() => ({
                isAuthenticated: false,
                expires: undefined,
                user: undefined,
            }))
        },
    }

    authAxios.get('v1/auth/status').then(({ data }) => {
        set(() => ({
            ...defaultState,
            isAuthenticated: true,
            expires: Date.now() + 1000 * 3600,
            user: {
                id: data.id,
                email: data.email,
                username: data.username,
            }
        }))
    }).catch(() => {
        set(() => defaultState)
    })

    return defaultState
});
