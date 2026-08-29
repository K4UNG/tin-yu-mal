export const ACCEPT = [
	'.txt',
	'.md',
	'.csv',
	'.tsv',
	'.json',
	'.pdf',
	'.jpg',
	'.jpeg',
	'.png',
	'.gif',
	'.webp',
	'.avif',
	'text/plain',
	'text/markdown',
	'text/csv',
	'application/json',
	'application/pdf',
	'image/jpeg',
	'image/png',
	'image/gif',
	'image/webp',
	'image/avif'
].join(',');

export const MAX_FILE_BYTES = 10 * 1024 * 1024;
export const MAX_FILES = 8;

const ALLOWED_EXT = /\.(txt|md|markdown|csv|tsv|json|pdf|jpe?g|png|gif|webp|avif)$/i;
const BLOCKED_MIME = /html|xml|svg/i;

export type FileKind = 'image' | 'pdf' | 'text';

export function isAllowedUpload(file: File): boolean {
	if (BLOCKED_MIME.test(file.type) || BLOCKED_MIME.test(file.name)) return false;
	return ALLOWED_EXT.test(file.name);
}

export function kindOf(file: File): FileKind {
	const name = file.name.toLowerCase();
	if (file.type.startsWith('image/') || /\.(jpe?g|png|gif|webp|avif)$/.test(name)) return 'image';
	if (file.type === 'application/pdf' || name.endsWith('.pdf')) return 'pdf';
	return 'text';
}

export function prettySize(bytes: number): string {
	if (bytes < 1024) return `${bytes} B`;
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
	return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

if (import.meta.env.DEV) {
	const pdf = { type: 'application/pdf', name: 'a.pdf' } as File;
	const pic = { type: 'image/png', name: 'a.png' } as File;
	const html = { type: 'text/html', name: 'a.html' } as File;
	const xml = { type: 'text/xml', name: 'a.xml' } as File;
	const txt = { type: 'text/plain', name: 'notes.txt' } as File;
	console.assert(isAllowedUpload(pdf) && isAllowedUpload(pic) && isAllowedUpload(txt));
	console.assert(!isAllowedUpload(html) && !isAllowedUpload(xml));
}
