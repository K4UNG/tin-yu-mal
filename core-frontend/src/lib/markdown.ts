export function formatMarkdown(src: string): string {
	const escaped = src
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;');

	const blocks = escaped.split(/\n{2,}/).map((chunk) => {
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
	});

	return blocks.join('');
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
}
