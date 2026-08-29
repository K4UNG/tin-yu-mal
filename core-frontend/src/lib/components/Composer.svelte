<script lang="ts">
	import IconArrowUp from '~icons/lucide/arrow-up';
	import IconFile from '~icons/lucide/file';
	import IconFileText from '~icons/lucide/file-text';
	import IconUpload from '~icons/lucide/upload';
	import IconX from '~icons/lucide/x';
	import { createCourse, EXAMPLE_PROMPTS, LANGUAGES, LEVELS } from '$lib/courses.svelte';
	import { ACCEPT, isAllowedUpload, kindOf, MAX_FILE_BYTES, MAX_FILES, prettySize } from '$lib/files';
	import type { Language, Level } from '$lib/types';

	type Attachment = { id: string; file: File; preview?: string };

	let topic = $state('');
	let level = $state<Level>('beginner');
	let language = $state<Language>('en');
	let field = $state<HTMLTextAreaElement | undefined>();
	let picker = $state<HTMLInputElement | undefined>();
	let attachments = $state<Attachment[]>([]);
	let skipNote = $state('');

	const canSend = $derived(topic.trim().length > 0);

	function autosize(el: HTMLTextAreaElement) {
		el.style.height = 'auto';
		el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
	}

	function clearAttachments() {
		for (const item of attachments) {
			if (item.preview) URL.revokeObjectURL(item.preview);
		}
		attachments = [];
	}

	function submit() {
		if (!canSend) return;
		// ponytail: files stay client-side until the course API accepts uploads.
		createCourse({ topic, level, language });
		topic = '';
		skipNote = '';
		clearAttachments();
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

	function addFiles(list: FileList | File[] | null) {
		if (!list) return;
		const next = [...attachments];
		const skipped: string[] = [];

		for (const file of list) {
			if (next.length >= MAX_FILES) {
				skipped.push('too many files');
				break;
			}
			if (!isAllowedUpload(file)) {
				skipped.push(file.name);
				continue;
			}
			if (file.size > MAX_FILE_BYTES) {
				skipped.push(file.name);
				continue;
			}
			const dup = next.some(
				(a) => a.file.name === file.name && a.file.size === file.size && a.file.lastModified === file.lastModified
			);
			if (dup) continue;
			next.push({
				id: crypto.randomUUID(),
				file,
				preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined
			});
		}

		attachments = next;
		skipNote = skipped.length
			? 'Skipped some files. Use text, PDF, or images (10 MB max).'
			: '';
	}

	function removeAttachment(id: string) {
		const item = attachments.find((a) => a.id === id);
		if (item?.preview) URL.revokeObjectURL(item.preview);
		attachments = attachments.filter((a) => a.id !== id);
		skipNote = '';
	}

	function onPick(e: Event) {
		addFiles((e.currentTarget as HTMLInputElement).files);
		if (picker) picker.value = '';
	}
</script>

<div class="composer-dock">
	<form class="composer" onsubmit={(e) => { e.preventDefault(); submit(); }}>
		{#if attachments.length}
			<ul class="attach-list">
				{#each attachments as item (item.id)}
					{@const kind = kindOf(item.file)}
					<li class="attach">
						{#if item.preview}
							<img class="attach-thumb" src={item.preview} alt="" />
						{:else}
							<span class="attach-kind {kind}">
								{#if kind === 'pdf'}
									<IconFile width="16" height="16" />
								{:else}
									<IconFileText width="16" height="16" />
								{/if}
							</span>
						{/if}
						<span class="attach-meta">
							<strong>{item.file.name}</strong>
							<span>{prettySize(item.file.size)}</span>
						</span>
						<button
							class="attach-remove"
							type="button"
							aria-label="Remove {item.file.name}"
							onclick={() => removeAttachment(item.id)}
						>
							<IconX width="14" height="14" />
						</button>
					</li>
				{/each}
			</ul>
		{/if}

		{#if skipNote}
			<p class="attach-note">{skipNote}</p>
		{/if}

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
			<input
				bind:this={picker}
				class="sr-only"
				type="file"
				accept={ACCEPT}
				multiple
				aria-hidden="true"
				tabindex="-1"
				onchange={onPick}
			/>
			<div class="composer-actions">
				<button class="icon-btn" type="button" aria-label="Upload text, PDF, or image" onclick={() => picker?.click()}>
					<IconUpload width="18" height="18" />
				</button>
				<button class="send" type="submit" disabled={!canSend} aria-label="Generate course">
					<IconArrowUp width="18" height="18" />
				</button>
			</div>
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
