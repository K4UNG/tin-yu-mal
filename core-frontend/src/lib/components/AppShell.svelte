<script lang="ts">
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { isPublicPath, safeNext } from '$lib/api/paths';
	import { createLogoutMutation, createMeQuery } from '$lib/api/queries.svelte';
	import { isLoggedIn } from '$lib/api/token.svelte';
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();

	const me = createMeQuery();
	const logout = createLogoutMutation();

	const publicRoute = $derived(isPublicPath(page.url.pathname));
	const authed = $derived(isLoggedIn());

	$effect(() => {
		if (!browser) return;
		if (!publicRoute && !authed) {
			const next = safeNext(page.url.pathname + page.url.search);
			goto(next === '/' ? '/login' : `/login?next=${encodeURIComponent(next)}`, {
				replaceState: true
			});
			return;
		}
		if (publicRoute && authed) {
			goto(safeNext(page.url.searchParams.get('next')), { replaceState: true });
		}
	});

	function signOut() {
		logout.mutate(undefined, { onSuccess: () => goto('/login') });
	}
</script>

<header class="topbar">
	<a class="logo" href={authed ? '/' : '/login'}>
		<span class="logo-mark" aria-hidden="true"><i class="b"></i><i class="r"></i><i class="y"></i><i class="g"></i></span>
		<span class="logo-word">tin-yu-mal</span>
	</a>
	{#if authed}
		<div class="topbar-end">
			<span class="who">{me.data?.name ?? me.data?.email ?? ''}</span>
			<button class="text-btn" type="button" onclick={signOut} disabled={logout.isPending}>
				Sign out
			</button>
		</div>
	{/if}
</header>

{#if publicRoute || (browser && authed)}
	{@render children()}
{:else}
	<div class="page">
		<div class="missing">
			<p>Checking your session…</p>
		</div>
	</div>
{/if}
