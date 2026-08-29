<script lang="ts">
	import { browser } from '$app/environment';
	import { page } from '$app/state';
	import { getChapter, getCourse, levelLabel, markChapterGenerating } from '$lib/courses.svelte';

	const course = $derived(getCourse(page.params.id));
	const chapter = $derived(getChapter(page.params.id, page.params.cid));

	$effect(() => {
		if (!browser) return;
		const c = course;
		const ch = chapter;
		if (c && ch && ch.status === 'not_generated') {
			markChapterGenerating(c.id, ch.id);
		}
	});
</script>

<svelte:head>
	<title>{chapter?.title ?? 'Chapter'} · tin-yu-mal</title>
</svelte:head>

<div class="page">
	{#if course && chapter}
		<a class="back" href="/course/{course.id}">← {course.topic}</a>
		<article class="card article">
			<div class="article-meta">
				<span class="badge {course.level}">{levelLabel(course.level)}</span>
				<span class="muted">Chapter {chapter.index + 1} of {course.chapters.length}</span>
			</div>
			<h1>{chapter.title}</h1>
			<p class="lede">{chapter.description}</p>

			{#if chapter.status !== 'ready'}
				<div class="loading-row">
					<span class="dots" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
					Writing this chapter…
				</div>
				<div class="shimmer" aria-hidden="true"></div>
			{:else}
				<div class="prose">
					<p>
						This is a stand-in lesson for <strong>{course.topic}</strong>. When the generator is
						wired up, this page will stream markdown, images, quizzes, and flashcards.
					</p>
					<h2>What you’ll take away</h2>
					<p>{chapter.description}</p>
					<p>
						For now the layout, type, and color system are in place so the reading surface matches
						the home screen.
					</p>
				</div>

				<div class="edit-box">
					<label for="edit">Ask for a change</label>
					<div class="edit-row">
						<input
							id="edit"
							type="text"
							placeholder="Make this simpler, add an example about cars…"
							disabled
						/>
						<button type="button" disabled>Apply</button>
					</div>
					<p class="muted">Editing connects once the chapter API is live.</p>
				</div>
			{/if}
		</article>
	{:else}
		<a class="back" href="/">← Home</a>
		<div class="missing">
			<p>This chapter isn’t on this device anymore.</p>
			<p class="muted">Generate the course again from the home screen.</p>
		</div>
	{/if}
</div>
