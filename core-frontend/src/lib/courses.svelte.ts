import type { ChapterSummary, Course, Language, Level } from './types';

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
	courses: [] as Course[]
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
	if (!chapter || chapter.status === 'ready') return;
	chapter.status = 'generating';
	catalog.courses = [...catalog.courses];

	window.setTimeout(() => {
		const ready = getChapter(courseId, chapterId);
		if (!ready) return;
		ready.status = 'ready';
		catalog.courses = [...catalog.courses];
	}, 900);
}
