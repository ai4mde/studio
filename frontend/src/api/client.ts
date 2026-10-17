import axios from "axios";
import { baseURL } from "$shared/globals";

export const apiClient = axios.create({
    baseURL,
    withCredentials: true,
    xsrfCookieName: "csrftoken",
    xsrfHeaderName: "X-CSRFTOKEN",
    withXSRFToken: true,
});