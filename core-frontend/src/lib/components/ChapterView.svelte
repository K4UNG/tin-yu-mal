<script lang="ts">
	import FlashcardsBlock from './blocks/FlashcardsBlock.svelte';
	import ImageBlock from './blocks/ImageBlock.svelte';
	import QuizFreeBlock from './blocks/QuizFreeBlock.svelte';
	import QuizMcBlock from './blocks/QuizMcBlock.svelte';
	import TextBlock from './blocks/TextBlock.svelte';
	import type { ContentBlock } from '$lib/types';

	let { blocks }: { blocks: ContentBlock[] } = $props();
</script>

<div class="chapter-blocks">
	{#each blocks as block, i (i)}
		{#if block.type === 'text'}
			<TextBlock {block} />
		{:else if block.type === 'image'}
			<ImageBlock {block} />
		{:else if block.type === 'quiz_free'}
			<QuizFreeBlock {block} />
		{:else if block.type === 'quiz_mc'}
			<QuizMcBlock {block} />
		{:else if block.type === 'flashcards'}
			<FlashcardsBlock {block} />
		{/if}
	{/each}
</div>
