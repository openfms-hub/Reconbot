/* ReconBot Desktop — Main Application */

const { invoke } = window.__TAURI__?.core || window;
const { shell } = window.__TAURI__?.shell || {};
const { dialog } = window.__TAURI__?.dialog || {};

// ── DOM refs ──
const $ = (sel) => document.querySelector(sel);

const state = {
    currentReportPath: null,
    reports: [],
    researchRunning: false,
};

// ── Helpers ──
function escapeHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

// ── History ──
async function loadHistory(filter = '') {
    const reports = await invoke('list_reports');
    const filtered = reports.filter(r => r.name.toLowerCase().includes(filter.toLowerCase()));
    state.reports = filtered;

    if (filtered.length === 0) {
        $('#history-list').innerHTML = '<div class="history-empty">暂无调研记录</div>';
        return;
    }

    $('#history-list').innerHTML = filtered.map(r => `
        <div class="history-item${state.currentReportPath === r.path ? ' active' : ''}" data-path="${escapeHtml(r.path)}">
            <div class="name">${escapeHtml(r.name)}</div>
            <div class="date">${escapeHtml(r.date)}</div>
        </div>
    `).join('');
}

// ── Read & render report ──
async function showReport(path) {
    try {
        const md = await invoke('read_report', { path });
        state.currentReportPath = path;
        renderMarkdown(md);
        // Refresh history to highlight active
        const filter = $('#search-input').value;
        loadHistory(filter);
    } catch (e) {
        alert('读取报告失败: ' + e);
    }
}

// ── Markdown renderer (minimal, no deps) ──
function renderMarkdown(md) {
    if (!md || md.trim() === '') {
        $('#report-content').innerHTML = '<div class="report-placeholder"><p>调研失败或未返回内容</p></div>';
        return;
    }

    let html = md
        // code blocks
        .replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) =>
            `<pre><code class="language-${escapeHtml(lang)}">${escapeHtml(code)}</code></pre>`)
        // inline code
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        // headers
        .replace(/^### (.*?)$/gm, '<h3>$1</h3>')
        .replace(/^## (.*?)$/gm, '<h2>$1</h2>')
        .replace(/^# (.*?)$/gm, '<h1>$1</h1>')
        // horizontal rules
        .replace(/^---$/gm, '<hr>')
        // bold
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        // italic
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        // blockquotes
        .replace(/^> (.*)$/gm, '<blockquote>$1</blockquote>')
        // tables
        .replace(/\|(.+)\|\n\|[-| ]+\|\n?/g, (_, header) => {
            const cells = header.split('|').map(c => c.trim());
            return `<table><thead><tr>${cells.map(c => `<th>${c}</th>`).join('')}</tr></thead><tbody>`;
        })
        .replace(/\|(.+)\|\n?/g, (_, row) => {
            const cells = row.split('|').map(c => c.trim());
            return `<tr>${cells.map(c => `<td>${c}</td>`).join('')}</tr>`;
        })
        .replace(/<\/tbody>\s*$/g, '</tbody></table>')
        // unordered lists
        .replace(/^\s*[-*+]\s+(.+)/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
        // paragraphs (double newline -> p)
        .replace(/\n\n/g, '</p><p>')
        // single newlines -> <br>
        .replace(/\n/g, '<br>');

    // Close any open table without tbody
    html = html.replace(/<\/tr>(?!<\s*(\/)?tr>)(?!<\s*(\/)?td>)(?!<\s*(\/)?th>)/g, '</tr>');

    $('#report-content').innerHTML = `<p>${html}</p>`;
}

// ── Research ──
async function doResearch() {
    if (state.researchRunning) return;

    const company = $('#company').value.trim();
    if (!company) { alert('请输入公司名称'); return; }

    state.researchRunning = true;
    $('#btn-research').disabled = true;
    $('#progress-panel').classList.remove('hidden');
    $('#progress-bar').style.width = '0%';
    $('#progress-text').textContent = '正在调研...';

    // Disable inputs
    document.querySelectorAll('.input-section input').forEach(i => i.disabled = true);

    try {
        const model = $('#model').value.trim();
        const result = await invoke('do_research', {
            input: {
                company: company,
                website: $('#website').value.trim(),
                country: $('#country').value.trim(),
                city: $('#city').value.trim(),
                phone: $('#phone').value.trim(),
                email: $('#email').value.trim(),
                industry: $('#industry').value.trim(),
                model: model,
            },
        });

        $('#progress-bar').style.width = '100%';
        $('#progress-text').textContent = '调研完成!';

        // Parse stdout for the filepath
        const filePathMatch = result.match(/报告已保存:\s*(.+)/);
        if (filePathMatch) {
            await showReport(filePathMatch[1].trim());
        } else {
            renderMarkdown(result);
        }

        loadHistory();
    } catch (e) {
        $('#progress-text').textContent = '调研失败: ' + e;
    } finally {
        state.researchRunning = false;
        $('#btn-research').disabled = false;
        document.querySelectorAll('.input-section input').forEach(i => i.disabled = false);
        setTimeout(() => {
            $('#progress-panel').classList.add('hidden');
        }, 2000);
    }
}

// ── Export ──
async function exportMarkdown() {
    if (!state.currentReportPath) return;
    const dir = await dialog.open({ directory: true, multiple: false, title: '保存目录' });
    if (!dir) return;
    const content = await invoke('read_report', { path: state.currentReportPath });
    const name = state.currentReportPath.split('/').pop();
    await shell.writeTextFile(dir + '/' + name, content);
}

async function exportPDF() {
    window.print();
}

async function copyToClipboard() {
    if (!state.currentReportPath) return;
    const content = await invoke('read_report', { path: state.currentReportPath });
    await navigator.clipboard.writeText(content);
}

async function deleteReport() {
    if (!state.currentReportPath) return;
    if (!confirm('确定删除此报告？')) return;
    await invoke('delete_report', { path: state.currentReportPath });
    state.currentReportPath = null;
    $('#report-content').innerHTML = '<div class="report-placeholder"><p>输入目标公司信息并点击「开始调研」</p></div>';
    loadHistory();
}

// ── Config ──
async function openConfig() {
    $('#config-modal').classList.remove('hidden');
    try {
        const root = await invoke('get_app_root');
        const configPath = root + '/config/settings.yaml';
        const content = await invoke('read_report', { path: configPath });
        $('#config-content').textContent = content;
    } catch (e) {
        $('#config-content').textContent = '无法读取配置文件: ' + e;
    }
}

function closeConfig() {
    $('#config-modal').classList.add('hidden');
}

// ── Events ──
function bindEvents() {
    $('#btn-research').addEventListener('click', doResearch);
    $('#btn-cancel').addEventListener('click', () => {
        state.researchRunning = false;
        $('#btn-research').disabled = false;
        document.querySelectorAll('.input-section input').forEach(i => i.disabled = false);
        $('#progress-panel').classList.add('hidden');
    });
    $('#btn-export-pdf').addEventListener('click', exportPDF);
    $('#btn-export-md').addEventListener('click', exportMarkdown);
    $('#btn-copy').addEventListener('click', copyToClipboard);
    $('#btn-delete').addEventListener('click', deleteReport);
    $('#btn-config').addEventListener('click', openConfig);
    $('#modal-close').addEventListener('click', closeConfig);
    $('#btn-config-close').addEventListener('click', closeConfig);
    $('#btn-config-open').addEventListener('click', async () => {
        const root = await invoke('get_app_root');
        await shell.open(root + '/config');
    });
    $('#search-input').addEventListener('input', (e) => loadHistory(e.target.value));
    $('#history-list').addEventListener('click', (e) => {
        const item = e.target.closest('.history-item');
        if (item) showReport(item.dataset.path);
    });
    $('#company').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') doResearch();
    });
}

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
    bindEvents();
    loadHistory();
});
