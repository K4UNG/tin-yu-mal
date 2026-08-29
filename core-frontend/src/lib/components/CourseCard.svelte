<script lang="ts">
	import IconChevronDown from '~icons/lucide/chevron-down';
	import IconChevronRight from '~icons/lucide/chevron-right';
	import IconDownload from '~icons/lucide/download';
	import IconTrash from '~icons/lucide/trash-2';
	import { deleteCourse, exportCourse, levelLabel } from '$lib/courses.svelte';
	import type { Course } from '$lib/types';

	const PREVIEW = 3;

	let {
		course,
		preview = false,
		ondelete
	}: {
		course: Course;
		preview?: boolean;
		ondelete?: () => void;
	} = $props();

	let expanded = $state(false);
	const extra = $derived(Math.max(0, course.chapters.length - PREVIEW));
	const chapters = $derived(
		preview && !expanded ? course.chapters.slice(0, PREVIEW) : course.chapters
	);

	function remove() {
		if (!confirm(`Delete “${course.topic}”?`)) return;
		deleteCourse(course.id);
		ondelete?.();
	}
</script>

<article class="card">
	<div class="card-head">
		<h2 class="card-title">
			{#if course.status === 'ready'}
				<a href="/course/{course.id}">{course.topic}</a>
			{:else}
				{course.topic}
			{/if}
		</h2>
		<div class="card-meta">
			<span class="badge {course.level}">{levelLabel(course.level)}</span>
			{#if !preview && course.status === 'ready'}
				<button class="icon-btn" type="button" aria-label="Export course" onclick={() => exportCourse(course.id)}>
					<IconDownload width="16" height="16" />
				</button>
			{/if}
			<button class="icon-btn danger" type="button" aria-label="Delete course" onclick={remove}>
				<IconTrash width="16" height="16" />
			</button>
		</div>
	</div>

	{#if course.status === 'generating'}
		<div class="loading-row">
			<span class="dots" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
			Generating chapters…
		</div>
		<div class="shimmer" aria-hidden="true"></div>
	{:else}
		<p class="chapters-label">Chapters</p>
		<div class="chapter-list">
			{#each chapters as chapter}
				<a class="chapter-row" href="/course/{course.id}/chapter/{chapter.id}">
					<span class="chapter-num i{chapter.index % 4}">{String(chapter.index + 1).padStart(2, '0')}</span>
					<span class="chapter-copy">
						<strong>{chapter.title}</strong>
						<span>{chapter.description}</span>
					</span>
					<span class="chapter-go" aria-hidden="true"><IconChevronRight width="16" height="16" /></span>
				</a>
			{/each}
		</div>
		{#if preview && extra > 0}
			<button class="show-more" type="button" onclick={() => (expanded = !expanded)}>
				{expanded ? 'Show less' : `Show ${extra} more`}
				<span class="show-more-ico" class:open={expanded}><IconChevronDown width="16" height="16" /></span>
			</button>
		{/if}
	{/if}
</article>
