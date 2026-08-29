import axios, { type AxiosError } from 'axios';
import { env } from '$env/dynamic/public';
import { clearAccessToken, getAccessToken } from './token.svelte';

export const api = axios.create({
	baseURL: env.PUBLIC_API_URL ?? 'http://localhost:8000',
	headers: { 'Content-Type': 'application/json' }
});

api.interceptors.request.use((config) => {
	const token = getAccessToken();
	if (token) {
		config.headers.set('Authorization', `Bearer ${token}`);
	}
	return config;
});

api.interceptors.response.use(
	(response) => response,
	(error: AxiosError) => {
		if (isUnauthorized(error) && !isLoginRequest(error)) {
			clearAccessToken();
		}
		return Promise.reject(error);
	}
);

export function isUnauthorized(error: unknown): boolean {
	return axios.isAxiosError(error) && error.response?.status === 401;
}

export function getApiErrorMessage(error: unknown): string {
	if (axios.isAxiosError(error)) {
		const data = error.response?.data;
		if (
			data !== null &&
			typeof data === 'object' &&
			'detail' in data &&
			typeof data.detail === 'string'
		) {
			return data.detail;
		}
		return error.message;
	}
	if (error instanceof Error) return error.message;
	return 'Request failed';
}

function isLoginRequest(error: AxiosError): boolean {
	const url = error.config?.url ?? '';
	return url.includes('/auth/login');
}
