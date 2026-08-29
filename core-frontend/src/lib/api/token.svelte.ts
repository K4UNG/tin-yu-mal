const STORAGE_KEY = 'access_token';

function readStored(): string | null {
	try {
		return localStorage.getItem(STORAGE_KEY);
	} catch {
		return null;
	}
}

// ponytail: module $state so createQuery `enabled` reacts after login/logout. Swap for httpOnly cookies if we add a refresh flow.
let accessToken = $state<string | null>(
	typeof localStorage === 'undefined' ? null : readStored()
);

export function getAccessToken(): string | null {
	return accessToken;
}

export function setAccessToken(token: string): void {
	accessToken = token;
	try {
		localStorage.setItem(STORAGE_KEY, token);
	} catch {
		// SSR / private mode
	}
}

export function clearAccessToken(): void {
	accessToken = null;
	try {
		localStorage.removeItem(STORAGE_KEY);
	} catch {
		// SSR / private mode
	}
}

export function isLoggedIn(): boolean {
	return accessToken !== null;
}
