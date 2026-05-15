function appRoot() {
    return {
        theme: 'light',
        init() {
            const stored = localStorage.getItem('theme');
            if (stored === 'light' || stored === 'dark') {
                this.theme = stored;
            } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                this.theme = 'dark';
            }
        },
        toggleTheme() {
            this.theme = this.theme === 'dark' ? 'light' : 'dark';
            localStorage.setItem('theme', this.theme);
        },
    };
}

function fileDrop() {
    return {
        fileName: '',
        dragover: false,
        pick(event) {
            const f = event.target.files && event.target.files[0];
            this.fileName = f ? f.name : '';
        },
        clear(event) {
            event.stopPropagation();
            event.preventDefault();
            this.fileName = '';
            this.$refs.input.value = '';
        },
        onDrop(event) {
            this.dragover = false;
            const dt = event.dataTransfer;
            if (dt && dt.files && dt.files.length) {
                this.$refs.input.files = dt.files;
                this.fileName = dt.files[0].name;
            }
        },
    };
}

function highlightMarkedText(rawText) {
    if (rawText == null) return '';
    let out = '';
    const len = rawText.length;
    let i = 0;
    while (i < len) {
        const ch = rawText[i];
        if (rawText.startsWith('<<<', i)) {
            const end = rawText.indexOf('>>>', i + 3);
            if (end !== -1) {
                const inner = rawText.slice(i + 3, end);
                out += '<span class="unknown">&lt;&lt;&lt;' + escapeHtml(inner) + '&gt;&gt;&gt;</span>';
                i = end + 3;
                continue;
            }
        }
        if (ch === '<') {
            out += '<span class="stress">&lt;</span>';
            i++;
            continue;
        }
        if (ch === '|') {
            out += '<span class="boundary">|</span>';
            i++;
            continue;
        }
        if (ch === '^') {
            out += '<span class="phantom">^</span>';
            i++;
            continue;
        }
        if (ch === '[' || ch === ']') {
            out += '<span class="bracket">' + ch + '</span>';
            i++;
            continue;
        }
        out += escapeHtml(ch);
        i++;
    }
    return out;
}

function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function copyText(text) {
    if (!text) return Promise.resolve(false);
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text).then(() => true).catch(() => fallbackCopy(text));
    }
    return Promise.resolve(fallbackCopy(text));
}

function fallbackCopy(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
}

function downloadText(text, filename) {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'processed_text.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function toast(message) {
    let el = document.getElementById('app-toast');
    if (!el) {
        el = document.createElement('div');
        el.id = 'app-toast';
        el.className = 'toast';
        document.body.appendChild(el);
    }
    el.textContent = message;
    requestAnimationFrame(() => el.classList.add('visible'));
    clearTimeout(el._t);
    el._t = setTimeout(() => el.classList.remove('visible'), 1600);
}

function getCaretCharOffset(el) {
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0) return null;
    const range = sel.getRangeAt(0);
    if (!el.contains(range.endContainer)) return null;
    const preRange = range.cloneRange();
    preRange.selectNodeContents(el);
    preRange.setEnd(range.endContainer, range.endOffset);
    return preRange.toString().length;
}

function setCaretCharOffset(el, offset) {
    if (offset == null) return;
    const sel = window.getSelection();
    if (!sel) return;
    const range = document.createRange();
    let pos = 0;
    let placed = false;
    function walk(node) {
        if (placed) return;
        if (node.nodeType === Node.TEXT_NODE) {
            const len = node.textContent.length;
            if (pos + len >= offset) {
                range.setStart(node, Math.max(0, offset - pos));
                range.collapse(true);
                placed = true;
                return;
            }
            pos += len;
        } else {
            for (const child of node.childNodes) {
                walk(child);
                if (placed) return;
            }
        }
    }
    walk(el);
    if (!placed) {
        range.selectNodeContents(el);
        range.collapse(false);
    }
    sel.removeAllRanges();
    sel.addRange(range);
}

function selectAllWithin(el) {
    const range = document.createRange();
    range.selectNodeContents(el);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
}

function markedTextController(rawText, filename) {
    return {
        raw: rawText || '',
        rendered: '',
        filename: filename || 'processed_text.txt',
        init() {
            this.rendered = highlightMarkedText(this.raw);
        },
        onInput(event) {
            const el = event.currentTarget;
            const offset = getCaretCharOffset(el);
            this.raw = el.innerText.replace(/\r\n?/g, '\n');
            this.rendered = highlightMarkedText(this.raw);
            this.$nextTick(() => setCaretCharOffset(el, offset));
        },
        onKeyDown(event) {
            if ((event.metaKey || event.ctrlKey) && (event.key === 'a' || event.key === 'A')) {
                event.preventDefault();
                selectAllWithin(event.currentTarget);
                return;
            }
            if (event.key === 'Enter') {
                event.preventDefault();
                document.execCommand('insertText', false, '\n');
            }
        },
        onPaste(event) {
            event.preventDefault();
            const text = (event.clipboardData || window.clipboardData).getData('text');
            document.execCommand('insertText', false, text);
        },
        copy() {
            copyText(this.raw).then(ok => toast(ok ? 'Скопировано в буфер' : 'Не удалось скопировать'));
        },
        download() {
            downloadText(this.raw, this.filename);
        },
    };
}

function isFirstTypeIambPattern(pattern) {
    if (!pattern) return false;
    for (let i = 0; i < pattern.length; i++) {
        if (pattern[i] === '/' && i % 2 === 0) return false;
    }
    return true;
}

function iambListController(items, filename) {
    return {
        items: Array.isArray(items) ? items : [],
        filename: filename || 'accidental_iambs.txt',
        hideFirstType: true,
        init() {},
        get filteredItems() {
            if (!this.hideFirstType) return this.items;
            return this.items.filter(it => !isFirstTypeIambPattern(it.pattern));
        },
        get visibleCount() {
            return this.filteredItems.length;
        },
        get totalCount() {
            return this.items.length;
        },
        get filteredText() {
            return this.filteredItems.map(it => it.text).join('\n') + (this.filteredItems.length ? '\n' : '');
        },
        copy() {
            copyText(this.filteredText).then(ok => toast(ok ? 'Скопировано в буфер' : 'Не удалось скопировать'));
        },
        download() {
            downloadText(this.filteredText, this.filename);
        },
    };
}

function makeSortable(table) {
    const headers = table.querySelectorAll('thead th');
    headers.forEach((th, idx) => {
        th.addEventListener('click', () => sortTableByColumn(table, idx, th));
    });
}

function sortTableByColumn(table, columnIdx, header) {
    const tbody = table.tBodies[0];
    if (!tbody) return;
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const currentDir = header.classList.contains('sort-asc') ? 'asc'
        : header.classList.contains('sort-desc') ? 'desc' : null;
    const nextDir = currentDir === 'asc' ? 'desc' : 'asc';

    table.querySelectorAll('thead th').forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
    header.classList.add(nextDir === 'asc' ? 'sort-asc' : 'sort-desc');

    rows.sort((a, b) => {
        const av = (a.cells[columnIdx]?.textContent || '').trim();
        const bv = (b.cells[columnIdx]?.textContent || '').trim();
        const an = parseFloat(av);
        const bn = parseFloat(bv);
        const isNum = !isNaN(an) && !isNaN(bn) && /^-?\d/.test(av) && /^-?\d/.test(bv);
        let cmp;
        if (isNum) {
            cmp = an - bn;
        } else {
            cmp = av.localeCompare(bv, 'ru', { numeric: true });
        }
        return nextDir === 'asc' ? cmp : -cmp;
    });

    rows.forEach(r => tbody.appendChild(r));
}

function initSortableTables(root) {
    (root || document).querySelectorAll('table.data.sortable').forEach(makeSortable);
}

document.addEventListener('DOMContentLoaded', () => {
    initSortableTables(document);
});

document.addEventListener('htmx:afterSwap', (evt) => {
    initSortableTables(evt.target);
});
