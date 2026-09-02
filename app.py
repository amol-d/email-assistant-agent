"""Gradio demo UI for the Email Assistant Agent, mounted on FastAPI."""

from __future__ import annotations

import gradio as gr

from email_assistant_agent.agent import EmailAssistantAgent
from email_assistant_agent.config import CONFIG
from email_assistant_agent.security import RateLimitError, ValidationError, sanitize_text
from email_assistant_agent.web import LIMITER, caller_id, make_app, run

_agent: EmailAssistantAgent | None = None


def _get_agent() -> EmailAssistantAgent:
    global _agent
    if _agent is None:
        _agent = EmailAssistantAgent()
    return _agent


def handle(email: str, request: gr.Request):
    try:
        clean = sanitize_text(email, field="an email", min_chars=10)
    except ValidationError as exc:
        yield f"⚠️ {exc}"
        return
    try:
        LIMITER.check(caller_id(request))
    except RateLimitError as exc:
        yield f"⏳ {exc}"
        return
    if not CONFIG.api_key_present:
        yield "⚠️ The demo is not configured (missing API key). See the GitHub repo to run it locally."
        return
    yield "✉️ Reading and drafting…"
    try:
        yield _get_agent().assist(clean)
    except Exception:  # noqa: BLE001
        yield "⚠️ Something went wrong. Please try again in a moment."


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="Email Assistant Agent — Day 09", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            "## ✉️ Email Assistant Agent\n"
            "Paste an email; get a **classification, summary, and a drafted reply**.\n\n"
            "*Day 09 of 14 AI Agents in 14 Days — classification + structured output.*"
        )
        email = gr.Textbox(label="Email", lines=12, placeholder="Paste the email you received here…")
        run_btn = gr.Button("Process", variant="primary")
        out = gr.Markdown()
        run_btn.click(handle, inputs=email, outputs=out)
    demo.queue(default_concurrency_limit=2, max_size=20)
    return demo


app = make_app(build_demo(), title="Email Assistant Agent")

if __name__ == "__main__":
    run(app)
