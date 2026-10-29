// Automated test of the WebSocket auto-reconnect logic in
// app/static/js/note.js. Stubbed DOM/jQuery/WebSocket; simulates machine sleep
// (close), failed retries (backoff), wake (visibilitychange) and 'online'.
// Run from repo root:  node test/websocket_reconnect_note.js
// Reconnect behaviour test for the real app/static/js/note.js (and rich_tinymce.js
// pattern check) using stubs for jQuery / DOM / WebSocket.
// Run: node .tmp-test/reconnect_test.js
const fs = require('fs');

/* ---------- stubs ---------- */
function makeJq() {
    const fn = function () {};
    const proxy = new Proxy(fn, {
        get(t, p) {
            if (p === 'is') return () => false;
            if (p === 'length') return 0;
            if (['height','width','val','scrollTop','scrollLeft','offset','innerHeight','outerHeight'].includes(p)) return () => 0;
            return () => proxy;
        },
        set() { return true; },
        apply() { return proxy; },
    });
    return proxy;
}

const sockets = [];
class FakeWebSocket {
    constructor(uri) {
        this.uri = uri;
        this.readyState = 1; // OPEN
        this.CLOSED = 3;
        sockets.push(this);
    }
    close() { this.readyState = 3; }
}

const listeners = {};
const documentStub = {
    hidden: false,
    addEventListener: (ev, cb) => { listeners[ev] = cb; },
};
const windowStub = {
    location: { host: '127.0.0.1:1' },
    addEventListener: (ev, cb) => { listeners[ev] = cb; },
    setTimeout: (cb, ms) => setTimeout(cb, ms),
    clearTimeout: (t) => clearTimeout(t),
    WebSocket: FakeWebSocket,
};
const $ = makeJq();

/* ---------- load the real note.js and start it ---------- */
const src = fs.readFileSync('app/static/js/note.js', 'utf8');
const factory = new Function('window', 'document', '$', 'jQuery', 'tinymce',
    src + '\nreturn noteInit;');
const noteInit = factory(windowStub, documentStub, $, $, makeJq());
noteInit('http', 'en_US');   // what templates/note/note.html does

function assert(cond, msg) {
    if (!cond) { console.error('FAIL: ' + msg); process.exit(1); }
    console.log('ok - ' + msg);
}

(async () => {
    assert(sockets.length === 1, 'initial websocket created: ' + sockets[0].uri);

    // 1) simulate sleep -> connection dies
    const s1 = sockets[0];
    s1.readyState = 3;
    s1.onclose();
    assert(sockets.length === 1, 'no immediate reconnect on close (scheduled)');

    // 2) first retry after 1000ms
    await new Promise(r => setTimeout(r, 1300));
    assert(sockets.length === 2, 'reconnected after ~1s (attempt #2)');
    const s2 = sockets[1];
    s2.onopen();
    assert(s2.onmessage && s2.onclose, 'handlers attached on reconnect');

    // 3) after a success the delay resets to 1s; consecutive failures grow it
    s2.readyState = 3;
    s2.onclose();                       // delay was reset to 1000 by onopen above
    await new Promise(r => setTimeout(r, 1300));
    assert(sockets.length === 3, 'next attempt came quickly (1s) after a previous success');
    const s3 = sockets[2];
    s3.readyState = 3;
    s3.onclose();                       // no success in a row now -> backoff 2000ms
    await new Promise(r => setTimeout(r, 1500));
    assert(sockets.length === 3, 'fourth attempt delayed (backoff 2s)');
    await new Promise(r => setTimeout(r, 800));
    assert(sockets.length === 4, 'fourth attempt created after ~2s');

    // 4) server back up: success resets backoff
    const s4 = sockets[3];
    s4.onopen();

    // 5) wake from sleep: visibilitychange triggers immediate reconnect
    s4.readyState = 3;
    s4.onclose();
    documentStub.hidden = false;
    listeners['visibilitychange']();
    assert(sockets.length === 5, 'visibilitychange on wake reconnects immediately');

    // 6) 'online' event also reconnects
    const s5 = sockets[4];
    s5.readyState = 3;
    s5.onclose();
    listeners['online']();
    assert(sockets.length === 6, 'online event reconnects immediately');

    console.log('ALL RECONNECT TESTS PASSED');
    process.exit(0);
})();
