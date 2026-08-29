<script lang="ts">
	import IconArrowLeft from '~icons/lucide/arrow-left';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { getApiErrorMessage } from '$lib/api/client';
	import { createCourseQuery } from '$lib/api/queries.svelte';
	import CourseCard from '$lib/components/CourseCard.svelte';
	import { getCourse } from '$lib/courses.svelte';

	const courseQ = createCourseQuery(() => page.params.id);
	const course = $derived(courseQ.data ?? getCourse(page.params.id));
</script>

<svelte:head>
	<title>{course?.topic ?? 'Course'} · tin-yu-mal</title>
</svelte:head>

<div class="page">
	<a class="back" href="/"><IconArrowLeft width="16" height="16" /> Home</a>
	{#if course}
		<CourseCard {course} ondelete={() => goto('/')} />
	{:else if courseQ.isError}
		<div class="missing">
			<p>{getApiErrorMessage(courseQ.error)}</p>
			<p class="muted">Generate it again from the home screen.</p>
		</div>
	{:else}
		<div class="loading-row">
			<span class="dots" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
			Loading course…
		</div>
	{/if}
</div>
