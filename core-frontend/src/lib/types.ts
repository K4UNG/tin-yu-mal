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
