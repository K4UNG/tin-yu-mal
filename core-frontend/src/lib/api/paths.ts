export const PUBLIC_PATHS = ['/login', '/signup'] as const;

export function isPublicPath(pathname: string): boolean {
	return (PUBLIC_PATHS as readonly string[]).includes(pathname);
}

export function safeNext(raw: string | null | undefined): string {
	if (!raw || !raw.startsWith('/') || raw.startsWith('//')) return '/';
	if (isPublicPath(raw)) return '/';
	return raw;
}

if (import.meta.env.DEV) {
	console.assert(safeNext('https://evil.test') === '/');
	console.assert(safeNext('//evil.test') === '/');
	console.assert(safeNext('/course/1') === '/course/1');
}
