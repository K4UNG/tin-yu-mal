import { browser } from '$app/environment';
import { mutationOptions, queryOptions } from '@tanstack/svelte-query';
import { axiosInstance } from './client';
import { clearAccessToken, getAccessToken, setAccessToken } from './token.svelte';

export { api, axiosInstance, getApiErrorMessage, isUnauthorized } from './client';
export { getAccessToken, isLoggedIn } from './token.svelte';

export type LoginRequest = {
	email: string;
	password: string;
};

export type SignupRequest = {
	email: string;
	name: string;
	password: string;
};

export type TokenResponse = {
	access_token: string;
	token_type: string;
};

export type User = {
	id: string;
	email: string;
	name: string;
	is_active: boolean;
};

export const authKeys = {
	all: ['auth'] as const,
	me: () => [...authKeys.all, 'me'] as const
};

export async function login(body: LoginRequest): Promise<TokenResponse> {
	const { data } = await axiosInstance.post<TokenResponse>('/auth/login', body);
	setAccessToken(data.access_token);
	return data;
}

export async function signup(body: SignupRequest): Promise<TokenResponse> {
	const { data } = await axiosInstance.post<TokenResponse>('/auth/signup', body);
	setAccessToken(data.access_token);
	return data;
}

export async function getMe(): Promise<User> {
	const { data } = await axiosInstance.get<User>('/auth/me');
	return data;
}

export function logout(): void {
	clearAccessToken();
}

export function meQueryOptions() {
	return queryOptions({
		queryKey: authKeys.me(),
		queryFn: getMe,
		enabled: browser && !!getAccessToken()
	});
}

export function loginMutationOptions() {
	return mutationOptions({
		mutationFn: login
	});
}

export function signupMutationOptions() {
	return mutationOptions({
		mutationFn: signup
	});
}

export function logoutMutationOptions() {
	return mutationOptions({
		mutationFn: async () => {
			logout();
		}
	});
}
