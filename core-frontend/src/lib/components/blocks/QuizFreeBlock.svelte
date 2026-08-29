<script lang="ts">
	import IconArrowUp from '~icons/lucide/arrow-up';
	import { getApiErrorMessage } from '$lib/api/client';
	import { postQuizEvaluate } from '$lib/api/courses';
	import type { QuizGrade } from '$lib/quiz';
	import type { QuizFreeBlock } from '$lib/types';

	let { block }: { block: QuizFreeBlock } = $props();

	let answer = $state('');
	let pending = $state(false);
	let result = $state<QuizGrade | null>(null);

	async function submit() {
		const text = answer.trim();
		if (!text || pending) return;
		pending = true;
		result = null;
		try {
			result = await postQuizEvaluate({
				question: block.question,
				sample_answer: block.sample_answer,
				grading_rubric: block.grading_rubric,
				user_answer: text
			});
		} catch (err) {
			result = { verdict: 'incorrect', feedback: getApiErrorMessage(err) };
		} finally {
			pending = false;
		}
	}
</script>

<section class="ix ix-quiz">
	<p class="ix-kicker">Quiz</p>
	<p class="ix-q">{block.question}</p>
	<form class="quiz-row" onsubmit={(e) => { e.preventDefault(); submit(); }}>
		<input
			type="text"
			bind:value={answer}
			placeholder="Type your answer"
			aria-label="Your answer"
			disabled={pending}
		/>
		<button class="send" type="submit" disabled={pending || !answer.trim()} aria-label="Submit answer">
			<IconArrowUp width="18" height="18" />
		</button>
	</form>
	{#if pending}
		<p class="muted">Checking your answer…</p>
	{:else if result}
		<p class="verdict {result.verdict}">{result.verdict}</p>
		<p class="ix-explain">{result.feedback}</p>
	{/if}
</section>
