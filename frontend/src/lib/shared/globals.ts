export const protocol = import.meta.env.AI4MDE_PROTO ?? "http://";
export const host = import.meta.env.AI4MDE_HOST ?? "api.ai4mde.localhost";
export const port = import.meta.env.AI4MDE_PORT ?? 80;
export const baseURL = `${protocol}${host}:${port}/api`;
export const wsURL = `ws://${host}:${port}`;

export default {
    protocol,
    host,
    port,
    baseURL,
    wsURL,
};
