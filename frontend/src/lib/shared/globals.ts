export const protocol = import.meta.env.AI4MDE_PROTO ?? "http://";
export const host = import.meta.env.AI4MDE_HOST ?? "api.ai4mde.localhost";
export const port = import.meta.env.AI4MDE_PORT ?? 80;
export const baseURL = `${protocol}${host}:${port}/api`;
export const wsURL = `ws://${host}:${port}`;
export const prototypeProtocol = import.meta.env.RUNNING_PROTOTYPE_PROTO ?? "http://";
export const prototypeHost = import.meta.env.RUNNING_PROTOTYPE_HOST ?? "prototype.ai4mde.localhost";
export const prototypeURL = `${prototypeProtocol}${prototypeHost}`;


export default {
    protocol,
    host,
    port,
    baseURL,
    wsURL,
    prototypeURL
};
