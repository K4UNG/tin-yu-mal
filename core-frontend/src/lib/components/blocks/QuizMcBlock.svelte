<script lang="ts">
	import type { QuizMcBlock } from '$lib/types';

	let { block }: { block: QuizMcBlock } = $props();
	let picked = $state<number | null>(null);
	const done = $derived(picked !== null);
</script>

<section class="ix ix-mc">
	<p class="ix-kicker">Multiple-choice</p>
	<p class="ix-q">{block.question}</p>
	<div class="mc-options">
		{#each block.options as option, i}
			<button
				type="button"
				class:right={done && i === block.correct_index}
				class:wrong={done && picked === i && i !== block.correct_index}
				disabled={done}
				onclick={() => (picked = i)}
			>
				{option}
			</button>
		{/each}
	</div>
	{#if done}
		<p class="ix-explain">{block.explanation}</p>
	{/if}
</section>
