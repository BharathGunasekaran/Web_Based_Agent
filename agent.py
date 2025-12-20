from dotenv import load_dotenv
from prompts import agent_instructions, sys_instructions
from livekit import agents, rtc
from livekit.agents import AgentServer,AgentSession, Agent, room_io
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from mcp_client import MCPServerSse
from mcp_client.agent_tools import MCPToolsIntegration
import os

load_dotenv()


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions= agent_instructions
        )

server = AgentServer()

@server.rtc_session(agent_name="Jordan-25e1")
async def my_agent(ctx: agents.JobContext):
    session = AgentSession(
        stt="assemblyai/universal-streaming:en",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-3:39d518b7-fd0b-4676-9b8b-29d64ff31e12",
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    N8N_MCP_API_KEY  = os.getenv("N8N_MCP_API_KEY")
    if not N8N_MCP_API_KEY:
        raise RuntimeError("N8N_MCP_URL is missing in .env")

    mcp_server = MCPServerSse(
        params={"url": N8N_MCP_API_KEY},
        name="AI Agent workflow",
    )


    agent = await MCPToolsIntegration.create_agent_with_tools(
        agent_class=Assistant,
        mcp_servers=[mcp_server],
    )

    await session.start(
        room=ctx.room,
        agent=agent,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: noise_cancellation.BVCTelephony() if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP else noise_cancellation.BVC(),
            ),
        ),
    )

    await session.generate_reply(
        instructions = sys_instructions,
        allow_interruptions=False,
    )


if __name__ == "__main__":
    agents.cli.run_app(server)