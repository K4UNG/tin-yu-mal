<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import { browser } from '$app/environment';
	import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
	import { isUnauthorized } from '$lib/api/client';
	import AppShell from '$lib/components/AppShell.svelte';
	import '../app.css';

	let { children } = $props();

	const queryClient = new QueryClient({
		defaultOptions: {
			queries: {
				enabled: browser,
				retry: (failureCount, error) => {
					if (isUnauthorized(error)) return false;
					return failureCount < 1;
				}
			}
		}
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>tin-yu-mal</title>
</svelte:head>

<QueryClientProvider client={queryClient}>
	<div class="app">
		<AppShell>{@render children()}</AppShell>
	</div>
</QueryClientProvider>
