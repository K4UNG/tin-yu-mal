<script lang="ts">
	import IconArrowLeft from '~icons/lucide/arrow-left';
	import IconArrowUp from '~icons/lucide/arrow-up';
	import { browser } from '$app/environment';
	import { page } from '$app/state';
	import { getApiErrorMessage } from '$lib/api/client';
	import {
		createChapterQuery,
		createCourseQuery,
		createEditChapterMutation,
		createGenerateChapterMutation
	} from '$lib/api/queries.svelte';
	import ChapterView from '$lib/components/ChapterView.svelte';
	import { getChapterContent, getCourse } from '$lib/courses.svelte';

	const courseQ = createCourseQuery(() => page.params.id);
	const course = $derived(courseQ.data ?? getCourse(page.params.id));
	const chapter = $derived(course?.chapters.find((ch) => ch.id === page.params.cid));
	const generate = createGenerateChapterMutation();
	const editMut = createEditChapterMutation();
	const contentQ = createChapterQuery(
		() => page.params.id,
		() => page.params.cid,
		() => chapter?.status === 'ready'
	);
	const content = $derived(contentQ.data ?? getChapterContent(page.params.cid));

	let edit = $state('');
	const kicked = new Set<string>();

	$effect(() => {
		if (!browser) return;
		const courseId = page.params.id;
		const ch = chapter;
		if (!courseId || !ch || ch.status !== 'not_generated') return;
		if (kicked.has(ch.id)) return;
		kicked.add(ch.id);
		generate.mutate({ courseId, chapterId: ch.id });
	});

	function applyEdit() {
		const courseId = page.params.id;
		const ch = chapter;
		const prompt = edit.trim();
		if (!courseId || !ch || !prompt) return;
		editMut.mutate({ courseId, chapterId: ch.id, prompt });
		edit = '';
	}

	function retryGenerate() {
		const courseId = page.params.id;
		const ch = chapter;
		if (!courseId || !ch) return;
		generate.mutate({ courseId, chapterId: ch.id });
	}

	const writing = $derived(
		!content || chapter?.status !== 'ready' || generate.isPending || editMut.isPending
	);
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

		{#if generate.isError}
			<div class="missing">
				<p>{getApiErrorMessage(generate.error)}</p>
				<button class="text-btn" type="button" onclick={retryGenerate}>Try again</button>
			</div>
		{:else if writing}
			<div class="loading-row">
				<span class="dots" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
				Writing this chapter…
			</div>
			<div class="shimmer" aria-hidden="true"></div>
		{:else if content}
			<ChapterView blocks={content.blocks} />
		{/if}
	{:else if course && course.chapters.length > 0}
		<a class="back" href="/"><IconArrowLeft width="16" height="16" /> Home</a>
		<div class="missing">
			<p>This chapter isn’t in the course.</p>
			<p class="muted">Pick a chapter from the course page.</p>
		</div>
	{:else if courseQ.isError}
		<a class="back" href="/"><IconArrowLeft width="16" height="16" /> Home</a>
		<div class="missing">
			<p>{getApiErrorMessage(courseQ.error)}</p>
			<p class="muted">Generate the course again from the home screen.</p>
		</div>
	{:else}
		<a class="back" href="/"><IconArrowLeft width="16" height="16" /> Home</a>
		<div class="loading-row">
			<span class="dots" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
			Loading chapter…
		</div>
	{/if}
</div>

{#if course && chapter && chapter.status === 'ready' && content && !editMut.isPending}
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
