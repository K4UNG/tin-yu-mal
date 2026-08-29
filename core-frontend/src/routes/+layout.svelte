<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import { browser } from '$app/environment';
	import { QueryClient, QueryClientProvider } from '@tanstack/svelte-query';
	import { isUnauthorized } from '$lib/api/client';
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
		<header class="topbar">
			<a class="logo" href="/">
				<span class="logo-mark" aria-hidden="true"><i class="b"></i><i class="r"></i><i class="y"></i><i class="g"></i></span>
				<span class="logo-word">tin-yu-mal</span>
			</a>
		</header>
		{@render children()}
	</div>
</QueryClientProvider>
