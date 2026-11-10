"""Visitors of the sample app for the stepped load test.

Each Locust user is one browser, and it repeats visits the way the app's pages work:

1. Arrive. The browser loads index.html and config.js.
   - With an empty cache (CC_COLD_SHARE of the visits) it also loads the JS and CSS bundles,
     manifest.json and favicon.ico.
   - A returning browser keeps /static/ (nginx lets it cache that for a year). It revalidates the
     rest with If-None-Match, and nginx answers 304.
2. The start page asks /api/session without a token and gets a 401. It then calls /api/logout and
   shows the login form.
3. Log in: POST /api/login, which is a bcrypt check on the backend, then /api/session with the
   token.
4. 10–30 page reloads. Each revalidates index.html and config.js and calls /api/session with the
   token.
5. Log out.

Every step is followed by a think time of 1–5 s, so 1,000 users make about 330 page actions per
second.

Registration is not part of the load: the app leaves a database connection open on every
registration (see docs/1). The accounts are created beforehand by scripts/load-test.sh.

Environment:
  CC_ACCOUNTS       accounts loaduser1..N@example.com to log in with (default 2000)
  CC_USER_PASSWORD  their password (scripts/load-test.sh passes .secrets/load-users)
  CC_COLD_SHARE     share of visits with an empty browser cache (default 0.3)
  CC_STEPS          users per step (default "100,250,500,1000,1500")
  CC_STEP_SECONDS   how long each step is held (default 600)
"""
import os
import random
import re

from locust import FastHttpUser, LoadTestShape, between, task

ACCOUNTS = int(os.environ.get("CC_ACCOUNTS", "2000"))
PASSWORD = os.environ.get("CC_USER_PASSWORD", "")
COLD_SHARE = float(os.environ.get("CC_COLD_SHARE", "0.3"))
STEPS = [int(n) for n in os.environ.get("CC_STEPS", "100,250,500,1000,1500").split(",")]
STEP_SECONDS = int(os.environ.get("CC_STEP_SECONDS", "600"))
SPAWN_RATE = 50  # users started per second when a step begins
BUNDLES = re.compile(r'(?:src|href)="(/static/[^"]+)"')


class Visitor(FastHttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        self.etags = {}             # the browser cache: path -> ETag
        self.static_cached = False  # bundles under /static/ are in the cache
        self.token = None
        self.reloads = 0
        self.next_action = self.arrive

    @task
    def act(self):
        self.next_action()

    # one visit: arrive -> log_in -> reload x N -> log_out -> arrive ...
    def arrive(self):
        if random.random() < COLD_SHARE:
            self.etags.clear()
            self.static_cached = False
        self.open_page()
        self.check_session()  # no token yet: 401
        self.client.get("/api/logout", name="/api/logout")
        self.next_action = self.log_in

    def log_in(self):
        account = {"email": f"loaduser{random.randint(1, ACCOUNTS)}@example.com", "password": PASSWORD}
        with self.client.post("/api/login", json=account, name="/api/login", catch_response=True) as r:
            token = r.json().get("token") if r.status_code == 200 else None
            if not token:
                r.failure(f"login failed with HTTP {r.status_code}")
                self.next_action = self.arrive
                return
            r.success()
        self.token = token
        self.check_session()
        self.reloads = random.randint(10, 30)
        self.next_action = self.reload

    def reload(self):
        self.open_page()
        self.check_session()
        self.reloads -= 1
        if self.reloads <= 0:
            self.next_action = self.log_out

    def log_out(self):
        self.client.get("/api/logout", name="/api/logout")
        self.token = None
        self.next_action = self.arrive

    # requests
    def fetch(self, path, name):
        """GET the way a browser does: conditional when the cache holds the file."""
        headers = {"If-None-Match": self.etags[path]} if path in self.etags else {}
        r = self.client.get(path, headers=headers, name=name)
        etag = r.headers.get("ETag") if r.headers else None
        if r.status_code == 200 and etag:
            self.etags[path] = etag
        return r

    def open_page(self):
        page = self.fetch("/", "/ (index.html)")
        self.fetch("/config.js", "/config.js")
        if not self.static_cached and page.status_code == 200:
            for path in BUNDLES.findall(page.text or ""):
                self.client.get(path, name="/static/ (JS and CSS bundles)")
            self.fetch("/manifest.json", "/manifest.json")
            self.fetch("/favicon.ico", "/favicon.ico")
            self.static_cached = True

    def check_session(self):
        # the page sends the token from its cookie, or the string "undefined" when there is none
        expected = 200 if self.token else 401
        with self.client.get("/api/session", headers={"Authorization": self.token or "undefined"},
                             name="/api/session" if self.token else "/api/session (no token)",
                             catch_response=True) as r:
            if r.status_code == expected:
                r.success()
            else:
                r.failure(f"HTTP {r.status_code}, expected {expected}")


class Steps(LoadTestShape):
    """Each step holds a fixed number of users for STEP_SECONDS, then the test stops."""

    def tick(self):
        step = int(self.get_run_time() // STEP_SECONDS)
        if step >= len(STEPS):
            return None
        return STEPS[step], SPAWN_RATE
