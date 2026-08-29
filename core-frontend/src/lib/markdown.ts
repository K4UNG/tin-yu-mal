export function formatMarkdown(src: string): string {
	const escaped = src
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;');

	const lines = escaped.split('\n');
	const out: string[] = [];
	let i = 0;
	while (i < lines.length) {
		if (!lines[i].trim()) {
			i += 1;
			continue;
		}
		if (isTableStart(lines, i)) {
			const rows: string[] = [];
			while (i < lines.length && isTableLine(lines[i])) {
				rows.push(lines[i]);
				i += 1;
			}
			out.push(renderTable(rows));
			continue;
		}
		const chunk: string[] = [];
		while (i < lines.length && lines[i].trim() && !isTableStart(lines, i)) {
			chunk.push(lines[i]);
			i += 1;
		}
		out.push(renderChunk(chunk.join('\n')));
	}
	return out.join('');
}

function isSep(line: string): boolean {
	return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
}

function isTableLine(line: string): boolean {
	return line.includes('|');
}

function isTableStart(lines: string[], i: number): boolean {
	return i + 1 < lines.length && isTableLine(lines[i]) && isSep(lines[i + 1]);
}

function cells(line: string): string[] {
	let t = line.trim();
	if (t.startsWith('|')) t = t.slice(1);
	if (t.endsWith('|')) t = t.slice(0, -1);
	return t.split('|').map((c) => c.trim());
}

function renderTable(lines: string[]): string {
	const body = lines.filter((l) => !isSep(l));
	if (!body.length) return '';
	const [header, ...rest] = body;
	const th = cells(header)
		.map((c) => `<th>${inline(c)}</th>`)
		.join('');
	const tr = rest
		.map((row) => `<tr>${cells(row).map((c) => `<td>${inline(c)}</td>`).join('')}</tr>`)
		.join('');
	return `<div class="md-table"><table><thead><tr>${th}</tr></thead><tbody>${tr}</tbody></table></div>`;
}

function renderChunk(chunk: string): string {
	const line = chunk.trim();
	if (line.startsWith('### ')) return `<h3>${inline(line.slice(4))}</h3>`;
	if (line.startsWith('## ')) return `<h2>${inline(line.slice(3))}</h2>`;
	if (line.startsWith('# ')) return `<h1>${inline(line.slice(2))}</h1>`;
	if (/^[-*] /.test(line)) {
		const items = line
			.split('\n')
			.filter((l) => /^[-*] /.test(l))
			.map((l) => `<li>${inline(l.replace(/^[-*] /, ''))}</li>`)
			.join('');
		return `<ul>${items}</ul>`;
	}
	return `<p>${inline(line).replace(/\n/g, '<br>')}</p>`;
}

function inline(s: string): string {
	return s
		.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
		.replace(/`(.+?)`/g, '<code>$1</code>')
		.replace(/\*(.+?)\*/g, '<em>$1</em>');
}

if (import.meta.env.DEV) {
	const html = formatMarkdown('## Hi\n\n**bold** and <script>');
	console.assert(html.includes('<h2>') && html.includes('<strong>') && !html.includes('<script>'));
	const table = formatMarkdown('| A | B |\n| --- | --- |\n| **1** | 2 |');
	console.assert(table.includes('<table>') && table.includes('<th>') && table.includes('<strong>1</strong>'));
}
