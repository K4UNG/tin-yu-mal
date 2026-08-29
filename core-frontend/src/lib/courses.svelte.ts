import type { Chapter, ChapterStatus, Course, Language, Level } from './types';

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
): Course['chapters'][number] | undefined {
	if (!chapterId) return undefined;
	return getCourse(courseId)?.chapters.find((ch) => ch.id === chapterId);
}

export function getChapterContent(chapterId: string | undefined): Chapter | undefined {
	if (!chapterId) return undefined;
	return catalog.chapters[chapterId];
}

export function levelLabel(level: Level): string {
	return LEVELS.find((l) => l.id === level)?.label ?? level;
}

export function upsertCourse(course: Course): void {
	const i = catalog.courses.findIndex((c) => c.id === course.id);
	if (i < 0) {
		catalog.courses = [course, ...catalog.courses];
		return;
	}
	catalog.courses[i] = course;
	catalog.courses = [...catalog.courses];
}

export function replaceCourse(oldId: string, course: Course): void {
	if (!catalog.courses.some((c) => c.id === oldId)) {
		upsertCourse(course);
		return;
	}
	catalog.courses = catalog.courses.map((c) => (c.id === oldId ? course : c));
}

export function setChapterStatus(courseId: string, chapterId: string, status: ChapterStatus): void {
	const course = getCourse(courseId);
	const chapter = course?.chapters.find((ch) => ch.id === chapterId);
	if (!chapter) return;
	chapter.status = status;
	catalog.courses = [...catalog.courses];
}

export function rememberChapter(chapter: Chapter): void {
	catalog.chapters = { ...catalog.chapters, [chapter.id]: chapter };
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
