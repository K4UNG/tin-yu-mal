import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { env } from '$env/dynamic/public';
import { clearAccessToken, getAccessToken } from './token.svelte';

/** Use this for API calls. JWT is attached automatically when the user is logged in. */
export const axiosInstance = axios.create({
	baseURL: env.PUBLIC_API_URL ?? 'http://localhost:8000'
});

axiosInstance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
	const token = getAccessToken();
	if (token) {
		config.headers.Authorization = `Bearer ${token}`;
	}
	if (config.data instanceof FormData) {
		delete config.headers['Content-Type'];
	} else {
		config.headers['Content-Type'] = 'application/json';
	}
	return config;
});

axiosInstance.interceptors.response.use(
	(response) => response,
	(error: AxiosError) => {
		if (isUnauthorized(error) && !isPublicAuthRequest(error)) {
			clearAccessToken();
		}
		return Promise.reject(error);
	}
);

export const api = axiosInstance;

export function isUnauthorized(error: unknown): boolean {
	return axios.isAxiosError(error) && error.response?.status === 401;
}

export function getApiErrorMessage(error: unknown): string {
	if (axios.isAxiosError(error)) {
		const data = error.response?.data;
		if (data !== null && typeof data === 'object' && 'detail' in data) {
			if (typeof data.detail === 'string') return data.detail;
			if (Array.isArray(data.detail) && data.detail[0]?.msg) {
				return String(data.detail[0].msg);
			}
		}
		return error.message;
	}
	if (error instanceof Error) return error.message;
	return 'Request failed';
}

function isPublicAuthRequest(error: AxiosError): boolean {
	const url = error.config?.url ?? '';
	return url.includes('/auth/login') || url.includes('/auth/signup');
}
