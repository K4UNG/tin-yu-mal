import { createMutation, createQuery, useQueryClient } from '@tanstack/svelte-query';
import {
	authKeys,
	loginMutationOptions,
	logoutMutationOptions,
	meQueryOptions
} from './auth';

/** Call from a component `<script>` (needs QueryClient context). */
export function createMeQuery() {
	return createQuery(() => meQueryOptions());
}

/** Call from a component `<script>` (needs QueryClient context). */
export function createLoginMutation() {
	const queryClient = useQueryClient();
	return createMutation(() => ({
		...loginMutationOptions(),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: authKeys.me() });
		}
	}));
}

/** Call from a component `<script>` (needs QueryClient context). */
export function createLogoutMutation() {
	const queryClient = useQueryClient();
	return createMutation(() => ({
		...logoutMutationOptions(),
		onSuccess: () => {
			queryClient.removeQueries({ queryKey: authKeys.all });
		}
	}));
}
