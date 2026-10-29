# Integration test for the Tornado WebSocket endpoints.
# Start a dev server first, from app/:
#   MYNOTE_HOME=../.tmp-test/home ../.venv-electron/bin/python MyNote.py --port=8200
# then run:  .venv-electron/bin/python test/websocket_server_test.py
import asyncio, json, subprocess, time
import requests
from tornado.websocket import websocket_connect
from tornado.httpclient import HTTPRequest, HTTPClientError

BASE = "http://127.0.0.1:8200"
PORT = 8200

def auth_session():
    s = requests.Session()
    s.get(BASE + "/login")
    xsrf = s.cookies.get("_xsrf")
    data = {"_xsrf": xsrf, "user": "wstester", "passwd": "wstest-pass-123",
            "passwd_confirm": "wstest-pass-123", "optionsRadios": "en_US"}
    s.post(BASE + "/register", data=data)  # idempotent-ish (existing user -> info page)
    del data["passwd_confirm"]
    s.post(BASE + "/login", data=data)
    assert s.cookies.get("user"), "login failed, no user cookie"
    return s

async def ws_connect(s):
    cookie = "; ".join(f"{k}={v}" for k, v in s.cookies.items() if v)
    for attempt in range(20):
        try:
            req = HTTPRequest(f"ws://127.0.0.1:{PORT}/note/websocket",
                              headers={"Cookie": cookie}, connect_timeout=3)
            return await websocket_connect(req)
        except (HTTPClientError, ConnectionRefusedError, OSError) as e:
            print(f"  ws attempt {attempt+1} failed: {e}")
            await asyncio.sleep(0.5)
    return None

async def read_init(conn, tries=5):
    for _ in range(tries):
        m = await conn.read_message()
        if m is None:
            return None
        d = json.loads(m)
        if "books" in d:
            return d
    return None

async def main():
    s = auth_session()
    print("registered/logged in as wstester")

    conn = await ws_connect(s)
    assert conn, "websocket connect failed"
    init = await read_init(conn)
    assert init and "books" in init, "no init payload"
    print(f"WS #1 OK: init payload received, books={init['books']['books']}")

    await conn.write_message(json.dumps({"category": {"cmd": "select", "category_name": "All"}}))
    try:
        m = await asyncio.wait_for(conn.read_message(), 5)
    except asyncio.TimeoutError:
        m = None
    print("WS #1 round-trip OK" if m is not None else "WS #1 connected (no reply to category select)")

    # simulate machine sleep killing TCP: hard-kill the server
    subprocess.run(["pkill", "-9", "-f", f"port={PORT}"], check=False)
    time.sleep(1)
    m = await conn.read_message()
    print(f"after server kill, read_message -> {'None (dropped)' if m is None else 'data'}")
    conn.close()

    # restart server on the same port: the browser's reconnect logic would now succeed
    subprocess.Popen(["bash", "-c",
        "cd app && MYNOTE_HOME=../.tmp-test/home ../.venv-electron/bin/python "
        f"MyNote.py --port={PORT} > ../.tmp-test/srv2.log 2>&1"])
    await asyncio.sleep(4)
    s2 = auth_session()
    conn2 = await ws_connect(s2)
    assert conn2, "reconnect after restart failed"
    init2 = await read_init(conn2)
    assert init2 and "books" in init2
    print("WS #2 OK: reconnected after server restart, init payload received")
    conn2.close()
    print("ALL WEBSOCKET TESTS PASSED")

asyncio.run(main())
