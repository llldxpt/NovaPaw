# -*- coding: utf-8 -*-
"""Text-to-Speech tool backed by local NovaMax TTS API."""

from ...runtime.tool_registry import tool_descriptor

import logging
import tempfile

import httpx
from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

logger = logging.getLogger(__name__)

_TTS_BASE = "http://127.0.0.1:15050/v1"
_TIMEOUT = 60.0


@tool_descriptor(
    tool_type="network",
    target_param="text",
    policy_name="TextToSpeech",
    default_policy="allow",
    policy_reason="Allow local NovaMax TTS synthesis",
    ui_description="Convert text to speech via local NovaMax TTS engine",
    ui_icon="🔊",
)
async def text_to_speech(
    text: str = "",
    voice: str = "",
    model: str = "",
    speed: float = 1.0,
    response_format: str = "wav",
) -> ToolResponse:
    """Convert text to speech using the local NovaMax TTS engine.

    **Discovery mode** — call WITHOUT text (or with empty text) to retrieve
    the list of available TTS models and voices. Present these to the user
    and let them choose before generating audio.

    **Synthesis mode** — call WITH text, model and voice to generate speech.
    The model must be a 6-character workspace ID and the voice must be an
    8-character voice ID (both obtained from discovery mode).

    Args:
        text: The text to synthesize (max 4096 chars). Leave empty for discovery mode.
        voice: Voice ID (8 chars). Required in synthesis mode.
        model: Workspace Model ID (6 chars). Required in synthesis mode.
        speed: Playback speed, 0.25 to 4.0. Default 1.0.
        response_format: Audio format — "wav", "mp3", "flac", or "opus". Default "wav".

    Returns:
        `ToolResponse` with available options (discovery mode) or the
        path to the generated audio file (synthesis mode).
    """
    # ── Discovery mode: list available models and voices ──────────────────
    if not text:
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT, trust_env=False) as client:
                models_resp = await client.get(f"{_TTS_BASE}/audio/models")
                models_resp.raise_for_status()
                all_models = models_resp.json().get("data", [])
                tts_models = [m for m in all_models if m.get("engine")]

                voices_resp = await client.get(f"{_TTS_BASE}/audio/voices")
                voices_resp.raise_for_status()
                voices = voices_resp.json().get("data", [])

            lines = ["## Available TTS Models"]
            for m in tts_models:
                lines.append(
                    f"- **{m['id']}** — {m.get('engine','?')}"
                    f" ({m.get('voice_mode','?')} mode)"
                )
            lines.append("")
            lines.append("## Available Voices")
            for v in voices:
                lines.append(f"- **{v['voice_id']}** — {v.get('name','?')}")

            if not tts_models or not voices:
                lines.append("")
                lines.append(
                    "No models or voices configured yet. "
                    "Please set up TTS in NovaMax first."
                )

            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text="\n".join(lines),
                    ),
                ],
            )
        except Exception as exc:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Failed to query NovaMax TTS API: {exc}",
                    ),
                ],
            )

    # ── Synthesis mode: generate audio ────────────────────────────────────
    if not model:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Please specify a model ID. Use text_to_speech() without arguments first to list available models and voices.",
                ),
            ],
        )
    if not voice:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Please specify a voice ID. Use text_to_speech() without arguments first to list available models and voices.",
                ),
            ],
        )

    payload: dict = {
        "model": model,
        "input": text[:4096],
        "voice": voice,
        "speed": max(0.25, min(4.0, speed)),
        "response_format": response_format,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, trust_env=False) as client:
            resp = await client.post(
                f"{_TTS_BASE}/audio/speech",
                json=payload,
            )
            if resp.status_code != 200:
                err = "unknown error"
                try:
                    err = resp.json().get("error", {}).get("message", err)
                except Exception:
                    pass
                return ToolResponse(
                    content=[TextBlock(type="text", text=f"TTS failed: {err}")],
                )

            duration = resp.headers.get("X-Audio-Duration", "?")
            suffix = f".{response_format}"
            tmp = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
                prefix="novapaw_tts_",
            )
            tmp.write(resp.content)
            tmp.close()

            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=(
                            f"TTS generated successfully.\n"
                            f"File: {tmp.name}\n"
                            f"Duration: {duration}s\n"
                            f"Format: {response_format}\n"
                            f"Voice: {voice} | Model: {model}"
                        ),
                    ),
                ],
            )
    except Exception as exc:
        logger.exception("TTS request failed")
        return ToolResponse(
            content=[TextBlock(type="text", text=f"TTS request failed: {exc}")],
        )
