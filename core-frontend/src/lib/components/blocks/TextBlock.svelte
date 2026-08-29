<script lang="ts">
	import { formatMarkdown } from '$lib/markdown';
	import type { TextBlock } from '$lib/types';

	let { block }: { block: TextBlock } = $props();
</script>

<div class="prose">{@html formatMarkdown(block.markdown)}</div>
