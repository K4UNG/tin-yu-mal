<script lang="ts">
	let {
		front,
		back,
		tone,
		interactive = true
	}: {
		front: string;
		back: string;
		tone: number;
		interactive?: boolean;
	} = $props();

	let flipped = $state(false);

	$effect(() => {
		if (!interactive) flipped = false;
	});

	function flip() {
		if (!interactive) return;
		flipped = !flipped;
	}
</script>

<div
	class="flip t{tone}"
	class:flipped
	class:locked={!interactive}
	role="button"
	tabindex={interactive ? 0 : -1}
	aria-pressed={interactive ? flipped : undefined}
	aria-hidden={!interactive}
	aria-label={interactive ? (flipped ? 'Show front of card' : 'Show back of card') : undefined}
	onclick={flip}
	onkeydown={(e) => {
		if (!interactive) return;
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			flip();
		}
	}}
>
	<span class="face front">{front}</span>
	<span class="face back">{back}</span>
</div>
