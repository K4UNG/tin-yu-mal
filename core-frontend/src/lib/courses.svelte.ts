import type { Chapter, ChapterSummary, ContentBlock, Course, Language, Level } from './types';

export const LEVELS: { id: Level; label: string }[] = [
	{ id: 'beginner', label: 'Beginner' },
	{ id: 'intermediate', label: 'Intermediate' },
	{ id: 'advanced', label: 'Advanced' }
];

export const LANGUAGES: { id: Language; label: string }[] = [
	{ id: 'my', label: 'Burmese' },
	{ id: 'en', label: 'English' }
];

export const EXAMPLE_PROMPTS = [
	'How neural networks work',
	'The kingdoms of Bagan',
	'Photosynthesis, simply',
	'How a compiler works'
];

const TEMPLATES: Record<Level, [string, string][]> = {
	beginner: [
		['Getting oriented', 'A friendly map of the topic and why it matters.'],
		['The building blocks', 'The few ideas you need before anything else makes sense.'],
		['A simple walkthrough', 'See the whole path once, with everyday analogies.'],
		['Try it yourself', 'A short practice pass so the ideas stick.'],
		['Common mix-ups', 'The mistakes beginners usually make — and how to avoid them.'],
		['Where to go next', 'A clear next step and what “good enough” looks like.']
	],
	intermediate: [
		['Frame the problem', 'What this topic is actually trying to explain.'],
		['Core model', 'The main structure, in enough detail to use it.'],
		['Worked example', 'One concrete case, walked through end to end.'],
		['Trade-offs', 'Where the simple story breaks and what to do instead.'],
		['Practice and recap', 'Check your understanding, then lock it in.']
	],
	advanced: [
		['Assumptions and scope', 'What we are taking as given, and what we are not.'],
		['The dense core', 'Mechanisms, constraints, and the parts that usually get hand-waved.'],
		['Edge cases', 'Where intuition fails — and how experts recover.'],
		['Synthesis', 'Put the pieces together and test them against a hard question.']
	]
};

export function chapterCountForLevel(level: Level): number {
	return TEMPLATES[level].length;
}

if (import.meta.env.DEV) {
	console.assert(
		chapterCountForLevel('beginner') > chapterCountForLevel('advanced'),
		'beginner courses should have more chapters than advanced'
	);
}

function outline(level: Level): ChapterSummary[] {
	return TEMPLATES[level].map(([title, description], index) => ({
		id: crypto.randomUUID(),
		index,
		title,
		description,
		status: 'not_generated' as const
	}));
}

export const catalog = $state({
	courses: [] as Course[],
	chapters: {} as Record<string, Chapter>
});

export function getCourse(id: string | undefined): Course | undefined {
	if (!id) return undefined;
	return catalog.courses.find((c) => c.id === id);
}

export function getChapter(
	courseId: string | undefined,
	chapterId: string | undefined
): ChapterSummary | undefined {
	if (!chapterId) return undefined;
	return getCourse(courseId)?.chapters.find((ch) => ch.id === chapterId);
}

export function getChapterContent(chapterId: string | undefined): Chapter | undefined {
	if (!chapterId) return undefined;
	return catalog.chapters[chapterId];
}

function mockBlocks(topic: string, chapter: ChapterSummary): ContentBlock[] {
	return [
		{
			type: 'text',
			markdown: `## ${chapter.title}\n\n${chapter.description}\n\nThis lesson is part of **${topic}**. We'll start with the idea in plain language, then check it with a picture and a few short exercises.`
		},
		{
			type: 'image',
			prompt: `Illustration for ${chapter.title} in a course about ${topic}`,
			alt: `Generated illustration for ${chapter.title}`,
			url: '/chapter-demo.png'
		},
		{
			type: 'text',
			markdown: `Once you can picture that, the rest of the chapter is practice: say it in your own words, pick the better option, then flip a few cards.\n\n- Keep the picture in mind\n- Prefer a short answer over a long one\n- Flip the card only after you've guessed`
		},
		{
			type: 'quiz_free',
			question: `In one or two sentences, what is the main idea of “${chapter.title}” in ${topic}?`,
			sample_answer: chapter.description,
			grading_rubric: 'Mentions the chapter theme and one concrete idea from the topic.'
		},
		{
			type: 'quiz_mc',
			question: `Which best describes this chapter of ${topic}?`,
			options: [
				chapter.description,
				'A list of unrelated facts with no through-line.',
				'A recap of a different course entirely.',
				'A puzzle with no connection to the topic.'
			],
			correct_index: 0,
			explanation: `This chapter is about ${chapter.title.toLowerCase()}: ${chapter.description}`
		},
		{
			type: 'flashcards',
			cards: [
				{ front: 'What is this chapter about?', back: chapter.title },
				{ front: `Why does it matter for ${topic}?`, back: chapter.description },
				{ front: 'What should you do next?', back: 'Try the quiz, then open the next chapter.' }
			]
		}
	];
}

export function levelLabel(level: Level): string {
	return LEVELS.find((l) => l.id === level)?.label ?? level;
}

export function createCourse(input: { topic: string; level: Level; language: Language }): Course {
	const course: Course = {
		id: crypto.randomUUID(),
		topic: input.topic.trim(),
		level: input.level,
		language: input.language,
		chapters: [],
		created_at: new Date().toISOString(),
		status: 'generating'
	};
	catalog.courses = [course, ...catalog.courses];

	// ponytail: fake latency until POST /courses exists. Swap for the real mutation.
	window.setTimeout(() => finishOutline(course.id), 1400);
	return course;
}

function finishOutline(id: string): void {
	const course = getCourse(id);
	if (!course) return;
	course.status = 'ready';
	course.chapters = outline(course.level);
	catalog.courses = [...catalog.courses];
}

export function markChapterGenerating(courseId: string, chapterId: string): void {
	const chapter = getChapter(courseId, chapterId);
	if (!chapter || chapter.status !== 'not_generated') return;
	chapter.status = 'generating';
	catalog.courses = [...catalog.courses];

	window.setTimeout(() => {
		const ready = getChapter(courseId, chapterId);
		const course = getCourse(courseId);
		if (!ready || !course) return;
		ready.status = 'ready';
		catalog.chapters = {
			...catalog.chapters,
			[ready.id]: {
				id: ready.id,
				title: ready.title,
				blocks: mockBlocks(course.topic, ready),
				edit_history: catalog.chapters[ready.id]?.edit_history ?? []
			}
		};
		catalog.courses = [...catalog.courses];
	}, 900);
}

export function deleteCourse(id: string): void {
	const course = getCourse(id);
	if (!course) return;
	const nextChapters = { ...catalog.chapters };
	for (const chapter of course.chapters) {
		delete nextChapters[chapter.id];
	}
	catalog.chapters = nextChapters;
	catalog.courses = catalog.courses.filter((c) => c.id !== id);
}

export function exportCourse(id: string): void {
	const course = getCourse(id);
	if (!course) return;
	const payload = {
		topic: course.topic,
		level: course.level,
		language: course.language,
		created_at: course.created_at,
		chapters: course.chapters.map((ch) => ({
			index: ch.index,
			title: ch.title,
			description: ch.description,
			status: ch.status,
			content: catalog.chapters[ch.id] ?? null
		}))
	};
	const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = `${slug(course.topic)}.json`;
	a.click();
	URL.revokeObjectURL(url);
}

function slug(topic: string): string {
	return (
		topic
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, '-')
			.replace(/^-|-$/g, '')
			.slice(0, 60) || 'course'
	);
}

export function requestChapterEdit(courseId: string, chapterId: string, prompt: string): void {
	const chapter = getChapter(courseId, chapterId);
	const full = catalog.chapters[chapterId];
	if (!chapter || !full || chapter.status !== 'ready') return;
	chapter.status = 'generating';
	full.edit_history = [...full.edit_history, { prompt, timestamp: new Date().toISOString() }];
	catalog.courses = [...catalog.courses];

	window.setTimeout(() => {
		const again = getChapter(courseId, chapterId);
		const body = catalog.chapters[chapterId];
		if (!again || !body) return;
		again.status = 'ready';
		body.blocks = [
			{
				type: 'text',
				markdown: `*Updated from your request: “${prompt.trim()}”*`
			},
			...body.blocks.filter(
				(b) => !(b.type === 'text' && b.markdown.startsWith('*Updated from your request'))
			)
		];
		catalog.chapters = { ...catalog.chapters };
		catalog.courses = [...catalog.courses];
	}, 900);
}
