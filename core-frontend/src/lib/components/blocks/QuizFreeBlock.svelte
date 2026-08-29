<script lang="ts">
	import IconArrowUp from '~icons/lucide/arrow-up';
	import { gradeFreeAnswer, type QuizGrade } from '$lib/quiz';
	import type { QuizFreeBlock } from '$lib/types';

	let { block }: { block: QuizFreeBlock } = $props();

	let answer = $state('');
	let pending = $state(false);
	let result = $state<QuizGrade | null>(null);

	function submit() {
		const text = answer.trim();
		if (!text || pending) return;
		pending = true;
		result = null;
		// ponytail: fake latency until POST /quiz/evaluate exists.
		window.setTimeout(() => {
			result = gradeFreeAnswer({
				user_answer: text,
				sample_answer: block.sample_answer,
				grading_rubric: block.grading_rubric
			});
			pending = false;
		}, 500);
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
