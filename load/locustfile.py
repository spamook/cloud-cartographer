"""Users of the sample app for the baseline load test.

A user opens the frontend (page and static files), then keeps calling the API with a think time
of 1–5 s, the way a person clicks around. The step shape raises the number of simultaneous users
to 1,000 and beyond; scripts/load-test.sh runs it and measures every step.

The routes come from environment variables, so the file doesn't change when the app does:
  CC_FRONTEND_PATHS  comma-separated, loaded once per user (default "/")
  CC_API_PATHS       comma-separated, called at random during the session
  CC_STEPS           users per step (default "100,250,500,1000,1500")
  CC_STEP_SECONDS    how long each step is held (default 600)
"""
import os
import random

from locust import FastHttpUser, LoadTestShape, between, task

FRONTEND = [p for p in os.environ.get("CC_FRONTEND_PATHS", "/").split(",") if p]
API = [p for p in os.environ.get("CC_API_PATHS", "").split(",") if p]
STEPS = [int(n) for n in os.environ.get("CC_STEPS", "100,250,500,1000,1500").split(",")]
STEP_SECONDS = int(os.environ.get("CC_STEP_SECONDS", "600"))
SPAWN_RATE = 50  # users started per second when a step begins


class AppUser(FastHttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        for path in FRONTEND:
            self.client.get(path, name=f"frontend {path}")

    @task(5)
    def call_api(self):
        if API:
            path = random.choice(API)
            self.client.get(path, name=f"api {path}")

    @task(1)
    def reload_page(self):
        self.client.get(FRONTEND[0], name=f"frontend {FRONTEND[0]}")


class Steps(LoadTestShape):
    """Each step holds a fixed number of users for STEP_SECONDS, then the test stops."""

    def tick(self):
        step = int(self.get_run_time() // STEP_SECONDS)
        if step >= len(STEPS):
            return None
        return STEPS[step], SPAWN_RATE
