<script lang="ts">
	import IconChevronLeft from '~icons/lucide/chevron-left';
	import IconChevronRight from '~icons/lucide/chevron-right';
	import { fade } from 'svelte/transition';
	import type { FlashcardsBlock } from '$lib/types';
	import FlipCard from './FlipCard.svelte';

	let { block }: { block: FlashcardsBlock } = $props();
	let index = $state(0);
	const last = $derived(block.cards.length - 1);

	function go(delta: number) {
		const next = Math.min(last, Math.max(0, index + delta));
		if (next === index) return;
		index = next;
	}
</script>

<section class="ix ix-cards">
	<p class="ix-kicker">Flash cards</p>
	<div class="deck">
		{#each block.cards as item, i (i)}
			{#if Math.abs(i - index) <= 1}
				<div
					class="deck-card"
					class:is-prev={i === index - 1}
					class:is-current={i === index}
					class:is-next={i === index + 1}
					role="button"
					tabindex={i === index ? -1 : 0}
					aria-label={i < index ? 'Previous card' : i > index ? 'Next card' : undefined}
					in:fade={{ duration: 200 }}
					out:fade={{ duration: 160 }}
					onclick={i === index ? undefined : () => go(i < index ? -1 : 1)}
					onkeydown={
						i === index
							? undefined
							: (e) => {
									if (e.key === 'Enter' || e.key === ' ') {
										e.preventDefault();
										go(i < index ? -1 : 1);
									}
								}
					}
				>
					<FlipCard
						front={item.front}
						back={item.back}
						tone={i % 4}
						interactive={i === index}
					/>
				</div>
			{/if}
		{/each}
	</div>
	<p class="deck-hint">Tap the card to flip</p>
	<div class="deck-nav">
		<button class="icon-btn" type="button" aria-label="Previous" disabled={index === 0} onclick={() => go(-1)}>
			<IconChevronLeft width="18" height="18" />
		</button>
		<span class="muted">{index + 1} / {block.cards.length}</span>
		<button class="icon-btn" type="button" aria-label="Next" disabled={index === last} onclick={() => go(1)}>
			<IconChevronRight width="18" height="18" />
		</button>
	</div>
</section>
