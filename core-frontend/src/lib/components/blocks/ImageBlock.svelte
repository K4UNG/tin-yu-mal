<script lang="ts">
	import IconImage from '~icons/lucide/image';
	import type { ImageBlock } from '$lib/types';

	let { block }: { block: ImageBlock } = $props();
</script>

<figure class="gen-image">
	{#if block.url}
		<img src={block.url} alt={block.alt} width="300" height="300" />
	{:else}
		<div class="gen-image-ph" aria-hidden="true">
			<IconImage width="40" height="40" />
		</div>
	{/if}
	<figcaption>{block.alt}</figcaption>
</figure>
