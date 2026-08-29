<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { getApiErrorMessage } from '$lib/api/client';
	import { safeNext } from '$lib/api/paths';
	import { createLoginMutation, createSignupMutation } from '$lib/api/queries.svelte';

	let { mode }: { mode: 'login' | 'signup' } = $props();

	const login = createLoginMutation();
	const signup = createSignupMutation();
	const next = $derived(safeNext(page.url.searchParams.get('next')));
	const pending = $derived(mode === 'login' ? login.isPending : signup.isPending);
	const error = $derived(mode === 'login' ? login.error : signup.error);

	let name = $state('');
	let email = $state('');
	let password = $state('');
	let confirm = $state('');
	let localError = $state('');

	function submit(e: SubmitEvent) {
		e.preventDefault();
		localError = '';
		if (mode === 'signup') {
			if (password.length < 8) {
				localError = 'Password must be at least 8 characters';
				return;
			}
			if (password !== confirm) {
				localError = 'Passwords do not match';
				return;
			}
			signup.mutate(
				{ email, name, password },
				{ onSuccess: () => goto(next) }
			);
			return;
		}
		login.mutate({ email, password }, { onSuccess: () => goto(next) });
	}

	const message = $derived(localError || (error ? getApiErrorMessage(error) : ''));
	const switchHref = $derived(
		mode === 'login'
			? `/signup${next === '/' ? '' : `?next=${encodeURIComponent(next)}`}`
			: `/login${next === '/' ? '' : `?next=${encodeURIComponent(next)}`}`
	);
</script>

<div class="auth-page">
	<form class="card auth-card" onsubmit={submit}>
		<h1>{mode === 'login' ? 'Sign in' : 'Create an account'}</h1>
		<p class="muted">
			{mode === 'login'
				? 'Use your email to continue generating courses.'
				: 'You’ll be signed in after you create an account.'}
		</p>

		{#if message}
			<p class="auth-error" role="alert">{message}</p>
		{/if}

		{#if mode === 'signup'}
			<label class="field">
				<span>Name</span>
				<input type="text" name="name" autocomplete="name" bind:value={name} required />
			</label>
		{/if}

		<label class="field">
			<span>Email</span>
			<input type="email" name="email" autocomplete="email" bind:value={email} required />
		</label>

		<label class="field">
			<span>Password</span>
			<input
				type="password"
				name="password"
				autocomplete={mode === 'login' ? 'current-password' : 'new-password'}
				bind:value={password}
				required
				minlength={mode === 'signup' ? 8 : 1}
			/>
		</label>

		{#if mode === 'signup'}
			<label class="field">
				<span>Confirm password</span>
				<input
					type="password"
					name="confirm"
					autocomplete="new-password"
					bind:value={confirm}
					required
					minlength="8"
				/>
			</label>
		{/if}

		<button class="btn-primary" type="submit" disabled={pending}>
			{pending ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Sign up'}
		</button>

		<p class="auth-switch">
			{#if mode === 'login'}
				No account? <a href={switchHref}>Sign up</a>
			{:else}
				Already have an account? <a href={switchHref}>Sign in</a>
			{/if}
		</p>
	</form>
</div>
