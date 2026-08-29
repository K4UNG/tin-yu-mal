<script lang="ts">
	import IconArrowLeft from '~icons/lucide/arrow-left';
	import IconArrowUp from '~icons/lucide/arrow-up';
	import { browser } from '$app/environment';
	import { page } from '$app/state';
	import ChapterView from '$lib/components/ChapterView.svelte';
	import {
		getChapter,
		getChapterContent,
		getCourse,
		markChapterGenerating,
		requestChapterEdit
	} from '$lib/courses.svelte';

	const course = $derived(getCourse(page.params.id));
	const chapter = $derived(getChapter(page.params.id, page.params.cid));
	const content = $derived(getChapterContent(page.params.cid));

	let edit = $state('');

	$effect(() => {
		if (!browser) return;
		const c = course;
		const ch = chapter;
		if (c && ch && ch.status === 'not_generated') {
			markChapterGenerating(c.id, ch.id);
		}
	});

	function applyEdit() {
		const c = course;
		const ch = chapter;
		const prompt = edit.trim();
		if (!c || !ch || !prompt) return;
		requestChapterEdit(c.id, ch.id, prompt);
		edit = '';
	}
</script>

<svelte:head>
	<title>{chapter?.title ?? 'Chapter'} · tin-yu-mal</title>
</svelte:head>

<div class="page reader">
	{#if course && chapter}
		<div class="chapter-bar">
			<a class="back" href="/course/{course.id}"><IconArrowLeft width="16" height="16" /> Back</a>
			<p class="chapter-now">Chapter {chapter.index + 1}: {chapter.title}</p>
		</div>

		{#if chapter.status !== 'ready' || !content}
			<div class="loading-row">
				<span class="dots" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
				Writing this chapter…
			</div>
			<div class="shimmer" aria-hidden="true"></div>
		{:else}
			<ChapterView blocks={content.blocks} />
		{/if}
	{:else}
		<a class="back" href="/"><IconArrowLeft width="16" height="16" /> Home</a>
		<div class="missing">
			<p>This chapter isn’t on this device anymore.</p>
			<p class="muted">Generate the course again from the home screen.</p>
		</div>
	{/if}
</div>

{#if course && chapter && chapter.status === 'ready' && content}
	<div class="composer-dock edit-dock">
		<form
			class="composer edit-composer"
			onsubmit={(e) => {
				e.preventDefault();
				applyEdit();
			}}
		>
			<input type="text" bind:value={edit} placeholder="Request changes..." aria-label="Request changes" />
			<button class="send" type="submit" disabled={!edit.trim()} aria-label="Apply changes">
				<IconArrowUp width="18" height="18" />
			</button>
		</form>
	</div>
{/if}
