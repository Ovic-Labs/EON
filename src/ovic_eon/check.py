"""Exercise the installed seven-engine SDK with a synthetic interaction."""

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from ovic_eon.ems import EmotionalMemory
from ovic_eon.ere import MemoryStatus
from ovic_eon.erg import ResponseContent
from ovic_eon.ers import EmotionObservation, ERSClient, ERSConfig
from ovic_eon.hbu import HumanBehaviorEngine
from ovic_eon.interaction import RobotInteraction


async def check() -> dict[str, str]:
    session_id, reference = uuid4().hex, uuid4().hex
    utterance = "I feel frustrated. Explain the setup."
    config = ERSConfig(enable_facial=False, enable_speech=False, enable_video=False)
    async with ERSClient(config=config) as ers:
        await ers.register_consent(session_id, reference)
        try:
            observation = await ers.analyze_text(session_id, reference, utterance)
        finally:
            await ers.revoke_consent(session_id)
    if not isinstance(observation, EmotionObservation) or observation.status.value == "failed":
        raise RuntimeError("Local ERS processing failed")
    with TemporaryDirectory() as directory:
        memory = EmotionalMemory(Path(directory) / "memory.db", user_id="fixture")
        pref = memory.confirm_preference("reply_style", "detailed", confirmed=True)
        robot = RobotInteraction(user_id="fixture", session_id=session_id, memory=memory)
        try:
            proposal = HumanBehaviorEngine().interpret(utterance)
            result = robot.respond(
                proposal,
                confirmed=True,
                use_memory=True,
                observation=observation,
                content=ResponseContent(clauses=("Open the setup screen",)),
            )
            if (
                result.plan.memory_status != MemoryStatus.AVAILABLE
                or result.plan.preference_id != pref.id
                or result.reply is None
                or "Open the setup screen." not in result.reply.sentences
                or not robot.session.complete(result.reply.turn_id)
            ):
                raise RuntimeError("The installed SDK did not complete the fixture turn")
            return {
                "ERS": observation.status.value,
                "EMS": result.plan.memory_status.value,
                "HBU": proposal.goal.value,
                "ERE": result.plan.strategy.value,
                "PSE": result.reply.profile_id,
                "SIE": "completed",
                "ERG": result.reply.text,
            }
        finally:
            robot.session.close()


def main() -> None:
    print(json.dumps(asyncio.run(check()), indent=2))


if __name__ == "__main__":
    main()
