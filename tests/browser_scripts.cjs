// Exercise the shipped inline scripts without browser or network dependencies.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const templates = process.argv[2] || path.join(__dirname, '../templates');
function inlineScript(filename) {
    const html = fs.readFileSync(path.join(templates, filename), 'utf8');
    const scripts = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)]
        .map(match => match[1]).filter(script => script.trim());
    assert.equal(scripts.length, 1, filename + ' should contain exactly one inline script');
    return scripts[0];
}
const themeScript = inlineScript('partials/theme.html');

function runTheme({saved = null, dark = false, fail = '', modern = true, media = true, missingControls = false} = {}) {
    let value = saved;
    const elements = Object.fromEntries(['system', 'light', 'dark'].map(name => [name, {
        style: {}, attributes: {}, handlers: {},
        setAttribute(key, value) { this.attributes[key] = value; },
        addEventListener(name, handler) { this.handlers[name] = handler; },
    }]));
    let applications = 0;
    const root = {style: {}, setAttribute(key, value) { this[key] = value; applications++; }};
    const storage = {
        getItem() { if (fail === 'get') throw Error('unavailable'); return value; },
        setItem(key, next) { if (fail === 'set') throw Error('unavailable'); value = next; },
        removeItem() { if (fail === 'remove') throw Error('unavailable'); value = null; },
    };
    let listener;
    let registrations = 0;
    const query = {matches: dark};
    query[modern ? 'addEventListener' : 'addListener'] = (...args) => {
        listener = args.at(-1);
        registrations++;
    };
    const window = {get localStorage() { if (fail === 'access') throw Error('unavailable'); return storage; }};
    if (media) window.matchMedia = () => query;
    let ready;
    const context = vm.createContext({window, document: {
        documentElement: root,
        addEventListener(event, handler) { assert.equal(event, "DOMContentLoaded"); ready = handler; },
        getElementById: id => missingControls ? null : elements[id.replace('theme-', '')],
    }});
    vm.runInContext(themeScript, context, {timeout: 1000});
    assert.equal(applications, 1, 'Theme must be applied before controls initialize');
    assert.equal(root['data-theme'], (saved === 'light' || saved === 'dark') && !['access', 'get'].includes(fail)
        ? saved : (media && dark ? 'dark' : 'light'));
    ready();
    assert.equal(applications, 1, 'Control initialization must not reapply the theme');
    const click = name => elements[name].handlers.click({preventDefault() {}});
    assert.equal(registrations, media ? 1 : 0);
    return {root, elements, click, changeOS(next) {
        query.matches = next;
        listener?.({matches: next});
    }};
}

for (const fail of ['', 'access', 'get', 'set', 'remove']) {
    const site = runTheme({saved: 'light', fail});
    site.click('dark');
    assert.equal(site.root['data-theme'], 'dark');
    assert.equal(site.elements.dark.attributes['aria-current'], 'true');
    site.changeOS(false);
    assert.equal(site.root['data-theme'], 'dark');
    site.click('system');
    assert.equal(site.elements.system.attributes['aria-current'], 'true');
    site.changeOS(true);
    assert.equal(site.root['data-theme'], 'dark');
}
assert.equal(runTheme({saved: 'invalid', dark: true}).root['data-theme'], 'dark');
assert.equal(runTheme({media: false}).root['data-theme'], 'light');
const withoutControls = runTheme({missingControls: true});
withoutControls.changeOS(true);
assert.equal(withoutControls.root['data-theme'], 'dark');
const legacy = runTheme({modern: false});
legacy.changeOS(true);
assert.equal(legacy.root['data-theme'], 'dark');

const mathScript = inlineScript('partials/footer.html');
vm.runInNewContext(mathScript, {window: {}, document: {
    addEventListener(event, handler) { handler(); },
}}); // A missing CDN script must leave source math readable without throwing.
const equations = [false, true].map(display => ({
    textContent: 'x^2', classList: {contains: () => display},
}));
const renders = [];
const katex = {render: (...args) => renders.push(args)};
vm.runInNewContext(mathScript, {window: {katex}, katex, document: {
    addEventListener(event, handler) { handler(); },
    querySelectorAll() { return equations; },
}});
assert.deepEqual(renders.map(call => call[2].displayMode), [false, true]);

const commentsScript = inlineScript('article.html');
for (const hostname of ['localhost', '127.0.0.1', '[::1]', 'fastpaced.com']) {
    vm.runInNewContext(commentsScript, {window: {location: {hostname}}, document: {
        getElementById() { return {}; },
    }}); // No observer API: no attempts to load Disqus or access missing APIs.
}
console.log('Browser script checks passed');
