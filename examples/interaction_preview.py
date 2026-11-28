"""Browser visualization of two synthetic EON interactions. Run with uvicorn."""

from html import escape
from pathlib import Path
from string import Template
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from ovic_eon.check import check
from ovic_eon.hbu import HumanBehaviorEngine
from ovic_eon.interaction import RobotInteraction

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
PAGE = Template(Path(__file__).with_name("interaction_preview.html").read_text(encoding="utf-8"))
NAMES = {
    "ERS": "Emotion recognition",
    "HBU": "Request interpretation",
    "EMS": "Emotional memory",
    "ERE": "Empathy reasoning",
    "PSE": "Communication style",
    "SIE": "Turn management",
    "ERG": "Response generation",
}


@app.get("/", response_class=HTMLResponse)
async def preview(example: str = "explain") -> HTMLResponse:
    if example == "explain":
        transcript = "I feel frustrated. Explain the setup."
        outputs = await check()
        reply = outputs["ERG"]
        outputs["ERG"] = "rendered"
        note = "The operator explicitly reported frustration. The ERS baseline withheld its emotion estimate."
    elif example == "pause":
        transcript = "Please stop talking."
        proposal = HumanBehaviorEngine().interpret(transcript)
        robot = RobotInteraction(user_id="fixture", session_id=uuid4().hex)
        try:
            result = robot.respond(proposal, confirmed=True)
            outputs = {
                "ERS": "unused",
                "HBU": proposal.goal.value,
                "EMS": result.plan.memory_status.value,
                "ERE": result.plan.strategy.value,
                "PSE": "silent delivery",
                "SIE": result.turn.action.value,
                "ERG": "suppressed" if result.reply is None else "rendered",
            }
            reply = result.reply.text if result.reply else "No spoken response."
        finally:
            robot.session.close()
        note = "The explicit request for space pauses the session. This scenario requires no affect observation or memory retrieval."
    else:
        raise HTTPException(status_code=404, detail="Unknown example")

    rows = "".join(
        f'<tr><th scope="row">{code}</th><td>{name}</td><td><code>{escape(outputs[code])}</code></td></tr>'
        for code, name in NAMES.items()
    )
    return HTMLResponse(
        PAGE.substitute(
            transcript=escape(transcript),
            reply=escape(reply),
            note=escape(note),
            rows=rows,
            explain_current='aria-current="page"' if example == "explain" else "",
            pause_current='aria-current="page"' if example == "pause" else "",
        ),
        headers={"Cache-Control": "no-store"},
    )
