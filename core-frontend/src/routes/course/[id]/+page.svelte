<script lang="ts">
	import IconArrowLeft from '~icons/lucide/arrow-left';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import CourseCard from '$lib/components/CourseCard.svelte';
	import { getCourse } from '$lib/courses.svelte';

	const course = $derived(getCourse(page.params.id));
</script>

<svelte:head>
	<title>{course?.topic ?? 'Course'} · tin-yu-mal</title>
</svelte:head>

<div class="page">
	<a class="back" href="/"><IconArrowLeft width="16" height="16" /> Home</a>
	{#if course}
		<CourseCard {course} ondelete={() => goto('/')} />
	{:else}
		<div class="missing">
			<p>This course isn’t on this device anymore.</p>
			<p class="muted">Generate it again from the home screen.</p>
		</div>
	{/if}
</div>
