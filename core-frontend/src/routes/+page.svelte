<script lang="ts">
	import Composer from '$lib/components/Composer.svelte';
	import CourseCard from '$lib/components/CourseCard.svelte';
	import { createCoursesQuery } from '$lib/api/queries.svelte';
	import { catalog } from '$lib/courses.svelte';

	const list = createCoursesQuery();
	const courses = $derived(list.data ?? catalog.courses);
</script>

<svelte:head>
	<title>tin-yu-mal</title>
</svelte:head>

<div class="page">
	{#if list.isError && courses.length === 0}
		<div class="missing">
			<p>Couldn’t load courses.</p>
			<p class="muted">Is the API running?</p>
		</div>
	{:else if courses.length === 0}
		<section class="hero">
			<h1>
				<span>What</span>
				<span> do you</span>
				<span> want to</span>
				<span> learn?</span>
			</h1>
			<p>Name a topic, pick a level and a language. We’ll write the chapters, the lessons, and the quizzes.</p>
		</section>
	{:else}
		<div class="feed">
			{#each courses as course (course.id)}
				<CourseCard {course} preview />
			{/each}
		</div>
	{/if}
</div>

<Composer />
