import { browser } from '$app/environment';
import { mutationOptions, queryOptions } from '@tanstack/svelte-query';
import type { Chapter, Course, Language, Level } from '$lib/types';
import { catalog, rememberChapter, upsertCourse } from '$lib/courses.svelte';
import { axiosInstance } from './client';

export const POLL_MS = 2000;

export type CourseRead = {
	id: string;
	topic: string;
	level: Level;
	language: Language;
	chapters: Course['chapters'];
	created_at: string;
};

export type CreateCourseInput = {
	topic: string;
	level: Level;
	language: Language;
	files?: File[];
};

export type UploadedFileRead = {
	id: string;
	filename: string;
	content_type: string;
	size_bytes: number;
	has_text: boolean;
	created_at: string;
};

export const courseKeys = {
	all: ['courses'] as const,
	list: () => [...courseKeys.all, 'list'] as const,
	detail: (id: string) => [...courseKeys.all, 'detail', id] as const,
	chapter: (courseId: string, chapterId: string) =>
		[...courseKeys.all, 'detail', courseId, 'chapter', chapterId] as const
};

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function isCourseId(id: string | undefined): id is string {
	return !!id && UUID_RE.test(id);
}

export function asCourse(raw: CourseRead): Course {
	const chapters = raw.chapters ?? [];
	return {
		id: String(raw.id),
		topic: raw.topic,
		level: raw.level,
		language: raw.language,
		created_at:
			typeof raw.created_at === 'string' ? raw.created_at : new Date(raw.created_at).toISOString(),
		chapters: chapters.map((ch) => ({
			...ch,
			id: String(ch.id)
		})),
		status: chapters.length === 0 ? 'generating' : 'ready'
	};
}

/** Poll while the outline is still empty. Chapter generate is a separate POST. */
export function pollWhileOutlinePending(
	courseOrList: Course | Course[] | undefined
): number | false {
	if (!courseOrList) return false;
	const rows = Array.isArray(courseOrList) ? courseOrList : [courseOrList];
	return rows.some((c) => c.chapters.length === 0) ? POLL_MS : false;
}

export async function uploadFile(file: File): Promise<UploadedFileRead> {
	const body = new FormData();
	body.append('file', file);
	const { data } = await axiosInstance.post<UploadedFileRead>('/uploads', body);
	return data;
}

export async function postCourse(input: {
	topic: string;
	level: Level;
	language: Language;
	file_ids: string[];
}): Promise<Course> {
	const { data } = await axiosInstance.post<CourseRead>('/courses', {
		topic: input.topic,
		level: input.level,
		language: input.language,
		file_ids: input.file_ids
	});
	return asCourse(data);
}

export async function fetchCourses(): Promise<Course[]> {
	const { data } = await axiosInstance.get<CourseRead[]>('/courses');
	const server = data.map(asCourse);
	// ponytail: merge in-flight optimistic cards; list is global until courses are user-scoped.
	const locals = catalog.courses.filter((c) => !isCourseId(c.id));
	const merged = [...locals, ...server];
	catalog.courses = merged;
	return merged;
}

export async function fetchCourse(id: string): Promise<Course> {
	const { data } = await axiosInstance.get<CourseRead>(`/courses/${id}`);
	const course = asCourse(data);
	upsertCourse(course);
	return course;
}

export async function deleteCourseOnServer(id: string): Promise<void> {
	if (!isCourseId(id)) return;
	await axiosInstance.delete(`/courses/${id}`);
}

export async function fetchChapter(courseId: string, chapterId: string): Promise<Chapter> {
	const { data } = await axiosInstance.get<Chapter>(
		`/courses/${courseId}/chapters/${chapterId}`
	);
	rememberChapter(data);
	return data;
}

export async function postGenerateChapter(courseId: string, chapterId: string): Promise<Chapter> {
	const { data } = await axiosInstance.post<Chapter>(
		`/courses/${courseId}/chapters/${chapterId}/generate`
	);
	rememberChapter(data);
	return data;
}

export async function postEditChapter(
	courseId: string,
	chapterId: string,
	prompt: string
): Promise<Chapter> {
	const { data } = await axiosInstance.post<Chapter>(
		`/courses/${courseId}/chapters/${chapterId}/edit`,
		{ prompt }
	);
	rememberChapter(data);
	return data;
}

export async function postQuizEvaluate(body: {
	question: string;
	sample_answer: string;
	grading_rubric: string;
	user_answer: string;
}): Promise<{ verdict: 'correct' | 'partial' | 'incorrect'; feedback: string }> {
	const { data } = await axiosInstance.post('/quiz/evaluate', body);
	return data;
}

export function coursesQueryOptions() {
	return queryOptions({
		queryKey: courseKeys.list(),
		queryFn: fetchCourses,
		enabled: browser,
		refetchInterval: (q) => pollWhileOutlinePending(q.state.data)
	});
}

export function courseQueryOptions(id: string) {
	return queryOptions({
		queryKey: courseKeys.detail(id),
		queryFn: () => fetchCourse(id),
		enabled: browser && isCourseId(id),
		refetchInterval: (q) => pollWhileOutlinePending(q.state.data)
	});
}

export function chapterQueryOptions(courseId: string, chapterId: string, ready: boolean) {
	return queryOptions({
		queryKey: courseKeys.chapter(courseId, chapterId),
		queryFn: () => fetchChapter(courseId, chapterId),
		enabled: browser && isCourseId(courseId) && isCourseId(chapterId) && ready,
		retry: false
	});
}

export function createCourseMutationOptions() {
	return mutationOptions({
		mutationFn: async (input: CreateCourseInput) => {
			const files = input.files ?? [];
			const file_ids = await Promise.all(files.map(async (file) => (await uploadFile(file)).id));
			return postCourse({
				topic: input.topic.trim(),
				level: input.level,
				language: input.language,
				file_ids
			});
		}
	});
}

export function deleteCourseMutationOptions() {
	return mutationOptions({
		mutationFn: (courseId: string) => deleteCourseOnServer(courseId)
	});
}

export function generateChapterMutationOptions() {
	return mutationOptions({
		mutationFn: ({ courseId, chapterId }: { courseId: string; chapterId: string }) =>
			postGenerateChapter(courseId, chapterId)
	});
}

export function editChapterMutationOptions() {
	return mutationOptions({
		mutationFn: ({
			courseId,
			chapterId,
			prompt
		}: {
			courseId: string;
			chapterId: string;
			prompt: string;
		}) => postEditChapter(courseId, chapterId, prompt)
	});
}

if (import.meta.env.DEV) {
	console.assert(isCourseId('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'));
	console.assert(!isCourseId('local:nope'));
	const empty = asCourse({
		id: 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
		topic: 't',
		level: 'beginner',
		language: 'en',
		created_at: new Date().toISOString(),
		chapters: []
	});
	console.assert(empty.status === 'generating');
	console.assert(pollWhileOutlinePending(empty) === POLL_MS);
	console.assert(pollWhileOutlinePending({ ...empty, chapters: [{ id: '1', index: 0, title: 'a', description: 'b', status: 'not_generated' }], status: 'ready' }) === false);
}
