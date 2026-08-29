import type { QuizVerdict } from './types';

export type QuizGrade = { verdict: QuizVerdict; feedback: string };

// ponytail: keyword overlap until POST /quiz/evaluate exists.
export function gradeFreeAnswer(input: {
	user_answer: string;
	sample_answer: string;
	grading_rubric: string;
}): QuizGrade {
	const words = input.sample_answer
		.toLowerCase()
		.split(/[^a-z0-9]+/)
		.filter((w) => w.length > 3);
	const answer = input.user_answer.toLowerCase();
	const hits = words.filter((w) => answer.includes(w)).length;
	if (hits >= 2 || (words.length > 0 && hits === words.length)) {
		return { verdict: 'correct', feedback: 'That covers the idea. Nice work.' };
	}
	if (hits >= 1) {
		return {
			verdict: 'partial',
			feedback: `Almost — a complete answer should include: ${input.grading_rubric}`
		};
	}
	return {
		verdict: 'incorrect',
		feedback: `Not quite. Look for: ${input.grading_rubric}`
	};
}

if (import.meta.env.DEV) {
	const g = gradeFreeAnswer({
		user_answer: 'neurons send signals through the network',
		sample_answer: 'Neurons send electrical signals',
		grading_rubric: 'mentions neurons and signals'
	});
	console.assert(g.verdict === 'correct' || g.verdict === 'partial');
}
