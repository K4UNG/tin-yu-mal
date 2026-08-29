import { createMutation, createQuery, useQueryClient } from '@tanstack/svelte-query';
import type { QueryClient } from '@tanstack/svelte-query';
import type { ChapterStatus, Course } from '$lib/types';
import {
	deleteCourse,
	replaceCourse,
	setChapterStatus,
	upsertCourse
} from '$lib/courses.svelte';
import {
	authKeys,
	loginMutationOptions,
	logoutMutationOptions,
	meQueryOptions,
	signupMutationOptions
} from './auth';
import {
	chapterQueryOptions,
	courseKeys,
	courseQueryOptions,
	coursesQueryOptions,
	createCourseMutationOptions,
	editChapterMutationOptions,
	generateChapterMutationOptions,
	type CreateCourseInput
} from './courses';

/** Call from a component `<script>` (needs QueryClient context). */
export function createMeQuery() {
	return createQuery(() => meQueryOptions());
}

/** Call from a component `<script>` (needs QueryClient context). */
export function createLoginMutation() {
	const queryClient = useQueryClient();
	return createMutation(() => ({
		...loginMutationOptions(),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: authKeys.me() });
		}
	}));
}

/** Call from a component `<script>` (needs QueryClient context). */
export function createSignupMutation() {
	const queryClient = useQueryClient();
	return createMutation(() => ({
		...signupMutationOptions(),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: authKeys.me() });
		}
	}));
}

/** Call from a component `<script>` (needs QueryClient context). */
export function createLogoutMutation() {
	const queryClient = useQueryClient();
	return createMutation(() => ({
		...logoutMutationOptions(),
		onSuccess: () => {
			queryClient.removeQueries({ queryKey: authKeys.all });
		}
	}));
}

export function createCoursesQuery() {
	return createQuery(() => coursesQueryOptions());
}

export function createCourseQuery(id: () => string | undefined) {
	return createQuery(() => courseQueryOptions(id() ?? ''));
}

export function createChapterQuery(
	courseId: () => string | undefined,
	chapterId: () => string | undefined,
	ready: () => boolean
) {
	return createQuery(() => chapterQueryOptions(courseId() ?? '', chapterId() ?? '', ready()));
}

export function createCourseMutation() {
	const queryClient = useQueryClient();
	return createMutation(() => ({
		...createCourseMutationOptions(),
		onMutate: (vars: CreateCourseInput) => {
			const optimistic: Course = {
				id: `local:${crypto.randomUUID()}`,
				topic: vars.topic.trim(),
				level: vars.level,
				language: vars.language,
				chapters: [],
				created_at: new Date().toISOString(),
				status: 'generating'
			};
			upsertCourse(optimistic);
			queryClient.setQueryData<Course[]>(courseKeys.list(), (old) => [
				optimistic,
				...(old ?? []).filter((c) => c.id !== optimistic.id)
			]);
			return { optimisticId: optimistic.id };
		},
		onSuccess: (course, _vars, ctx) => {
			replaceCourse(ctx?.optimisticId ?? course.id, course);
			queryClient.setQueryData(courseKeys.detail(course.id), course);
			queryClient.setQueryData<Course[]>(courseKeys.list(), (old) => [
				course,
				...(old ?? []).filter((c) => c.id !== ctx?.optimisticId && c.id !== course.id)
			]);
		},
		onError: (_err, _vars, ctx) => {
			if (!ctx?.optimisticId) return;
			deleteCourse(ctx.optimisticId);
			queryClient.setQueryData<Course[]>(courseKeys.list(), (old) =>
				(old ?? []).filter((c) => c.id !== ctx.optimisticId)
			);
		}
	}));
}

export function createGenerateChapterMutation() {
	const queryClient = useQueryClient();
	return createMutation(() => ({
		...generateChapterMutationOptions(),
		onMutate: ({ courseId, chapterId }) => {
			patchChapterStatus(queryClient, courseId, chapterId, 'generating');
		},
		onSuccess: (chapter, { courseId, chapterId }) => {
			patchChapterStatus(queryClient, courseId, chapterId, 'ready');
			queryClient.setQueryData(courseKeys.chapter(courseId, chapterId), chapter);
		},
		onError: (_err, { courseId, chapterId }) => {
			patchChapterStatus(queryClient, courseId, chapterId, 'not_generated');
		}
	}));
}

export function createEditChapterMutation() {
	const queryClient = useQueryClient();
	return createMutation(() => ({
		...editChapterMutationOptions(),
		onMutate: ({ courseId, chapterId }) => {
			patchChapterStatus(queryClient, courseId, chapterId, 'generating');
		},
		onSuccess: (chapter, { courseId, chapterId }) => {
			patchChapterStatus(queryClient, courseId, chapterId, 'ready');
			queryClient.setQueryData(courseKeys.chapter(courseId, chapterId), chapter);
		},
		onError: (_err, { courseId, chapterId }) => {
			patchChapterStatus(queryClient, courseId, chapterId, 'ready');
		}
	}));
}

export function dropCourseQueries(queryClient: QueryClient, courseId: string) {
	deleteCourse(courseId);
	queryClient.setQueryData<Course[]>(courseKeys.list(), (old) =>
		(old ?? []).filter((c) => c.id !== courseId)
	);
	queryClient.removeQueries({ queryKey: courseKeys.detail(courseId) });
}

function patchChapterStatus(
	queryClient: QueryClient,
	courseId: string,
	chapterId: string,
	status: ChapterStatus
) {
	setChapterStatus(courseId, chapterId, status);
	queryClient.setQueryData<Course>(courseKeys.detail(courseId), (old) =>
		old
			? {
					...old,
					chapters: old.chapters.map((ch) => (ch.id === chapterId ? { ...ch, status } : ch))
				}
			: old
	);
	queryClient.setQueryData<Course[]>(courseKeys.list(), (old) =>
		old?.map((course) =>
			course.id === courseId
				? {
						...course,
						chapters: course.chapters.map((ch) => (ch.id === chapterId ? { ...ch, status } : ch))
					}
				: course
		)
	);
}

