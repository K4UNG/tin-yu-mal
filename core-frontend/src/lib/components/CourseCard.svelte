<script lang="ts">
	import IconChevronRight from '~icons/lucide/chevron-right';
	import { levelLabel } from '$lib/courses.svelte';
	import type { Course } from '$lib/types';

	let { course }: { course: Course } = $props();
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
		<span class="badge {course.level}">{levelLabel(course.level)}</span>
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
			{#each course.chapters as chapter}
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
	{/if}
</article>
