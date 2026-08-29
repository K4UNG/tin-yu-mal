export type Level = 'beginner' | 'intermediate' | 'advanced';
export type Language = 'en' | 'my';
export type ChapterStatus = 'not_generated' | 'generating' | 'ready';

export type ChapterSummary = {
	id: string;
	index: number;
	title: string;
	description: string;
	status: ChapterStatus;
};

export type Course = {
	id: string;
	topic: string;
	level: Level;
	language: Language;
	chapters: ChapterSummary[];
	created_at: string;
	status: 'generating' | 'ready';
};

export type TextBlock = { type: 'text'; markdown: string };
export type ImageBlock = { type: 'image'; prompt: string; alt: string; url: string };
export type QuizFreeBlock = {
	type: 'quiz_free';
	question: string;
	sample_answer: string;
	grading_rubric: string;
};
export type QuizMcBlock = {
	type: 'quiz_mc';
	question: string;
	options: string[];
	correct_index: number;
	explanation: string;
};
export type FlashcardsBlock = {
	type: 'flashcards';
	cards: { front: string; back: string }[];
};

export type ContentBlock = TextBlock | ImageBlock | QuizFreeBlock | QuizMcBlock | FlashcardsBlock;

export type Chapter = {
	id: string;
	title: string;
	blocks: ContentBlock[];
	edit_history: { prompt: string; timestamp: string }[];
};

export type QuizVerdict = 'correct' | 'partial' | 'incorrect';
