<script lang="ts">
	import { createCourse, EXAMPLE_PROMPTS, LANGUAGES, LEVELS } from '$lib/courses.svelte';
	import type { Language, Level } from '$lib/types';

	let topic = $state('');
	let level = $state<Level>('beginner');
	let language = $state<Language>('en');
	let field = $state<HTMLTextAreaElement | undefined>();

	const canSend = $derived(topic.trim().length > 0);

	function autosize(el: HTMLTextAreaElement) {
		el.style.height = 'auto';
		el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
	}

	function submit() {
		if (!canSend) return;
		createCourse({ topic, level, language });
		topic = '';
		if (field) {
			field.style.height = 'auto';
			field.focus();
		}
	}

	function onKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			submit();
		}
	}

	function usePrompt(text: string) {
		topic = text;
		queueMicrotask(() => {
			if (field) {
				autosize(field);
				field.focus();
			}
		});
	}
</script>

<div class="composer-dock">
	<form class="composer" onsubmit={(e) => { e.preventDefault(); submit(); }}>
		<div class="composer-top">
			<textarea
				bind:this={field}
				bind:value={topic}
				rows="1"
				placeholder="Describe what you want to learn..."
				aria-label="Course topic"
				oninput={(e) => autosize(e.currentTarget)}
				onkeydown={onKeydown}
			></textarea>
			<button class="send" type="submit" disabled={!canSend} aria-label="Generate course">
				<svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
					<path
						d="M12 4v16M12 4l-6 6M12 4l6 6"
						stroke="currentColor"
						stroke-width="2.2"
						stroke-linecap="round"
						stroke-linejoin="round"
					/>
				</svg>
			</button>
		</div>

		<div class="composer-controls">
			<fieldset class="control">
				<legend>Level</legend>
				<div class="seg" role="radiogroup" aria-label="Complexity level">
					{#each LEVELS as item}
						<button
							type="button"
							class="pill {item.id}"
							class:on={level === item.id}
							role="radio"
							aria-checked={level === item.id}
							onclick={() => (level = item.id)}
						>
							{item.label}
						</button>
					{/each}
				</div>
			</fieldset>

			<fieldset class="control">
				<legend>Primary language</legend>
				<div class="seg" role="radiogroup" aria-label="Primary language">
					{#each LANGUAGES as item}
						<button
							type="button"
							class="pill {item.id}"
							class:on={language === item.id}
							role="radio"
							aria-checked={language === item.id}
							onclick={() => (language = item.id)}
						>
							{item.label}
						</button>
					{/each}
				</div>
			</fieldset>
		</div>

		<div class="prompts">
			{#each EXAMPLE_PROMPTS as prompt, i}
				<button type="button" class="prompt c{i % 4}" onclick={() => usePrompt(prompt)}>
					<i></i>
					{prompt}
				</button>
			{/each}
		</div>
	</form>
</div>
