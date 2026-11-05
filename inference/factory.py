"""Build a ready-to-use InferenceService from the settings.

Keeps the wiring in one place, so the API (and scripts) just call
`build_inference_service(get_settings())`.
"""

from config.settings import Settings
from inference.engine import LitGPTEngine
from inference.job_store import JobStore
from inference.schemas import GenerationParams
from inference.service import InferenceService


def default_generation_params(settings: Settings) -> GenerationParams:
    gen = settings.generation
    return GenerationParams(
        max_new_tokens=gen.max_new_tokens,
        temperature=gen.temperature,
        top_p=gen.top_p,
        top_k=gen.top_k,
        system_prompt=gen.system_prompt,
    )


def build_inference_service(settings: Settings) -> InferenceService:
    return InferenceService(
        engine=LitGPTEngine(settings.model),
        store=JobStore(ttl_seconds=settings.server.result_ttl_seconds),
        default_params=default_generation_params(settings),
    )
