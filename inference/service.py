"""Inference service: the business logic the API talks to.

How it works (asynchronous):
    1. submit(prompt)  -> creates a job, puts it in a queue, returns at once
    2. a single worker thread takes jobs one by one and runs the model
    3. get_job(id)     -> returns the job with its status and answer

Why one worker? A GPU runs one generation at a time efficiently with LitGPT;
a queue avoids memory errors when many users send questions together.
"""

import logging
import queue
import threading

from inference.engine import InferenceEngine
from inference.job_store import JobStore
from inference.schemas import GenerationParams, Job

logger = logging.getLogger(__name__)

_STOP_SIGNAL = None  # Put in the queue to stop the worker


class InferenceService:
    def __init__(self, engine: InferenceEngine, store: JobStore, default_params: GenerationParams) -> None:
        self._engine = engine
        self._store = store
        self._default_params = default_params
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._worker: threading.Thread | None = None

    # ---- Life cycle --------------------------------------------------------
    def start(self) -> None:
        """Start the background worker (it loads the model first)."""
        if self._worker is not None:
            return
        self._worker = threading.Thread(target=self._run_worker, name="inference-worker", daemon=True)
        self._worker.start()

    def stop(self, timeout: float = 5.0) -> None:
        """Ask the worker to finish and wait for it."""
        if self._worker is None:
            return
        self._queue.put(_STOP_SIGNAL)
        self._worker.join(timeout)
        self._worker = None

    # ---- Public API ----------------------------------------------------------
    def submit(self, prompt: str) -> Job:
        """Queue a question and return its job right away."""
        job = self._store.create(prompt)
        self._queue.put(job.request_id)
        return job

    def get_job(self, request_id: str) -> Job | None:
        return self._store.get(request_id)

    def queue_size(self) -> int:
        return self._queue.qsize()

    # ---- Worker ----------------------------------------------------------------
    def _run_worker(self) -> None:
        self._load_engine()
        while True:
            request_id = self._queue.get()
            if request_id is _STOP_SIGNAL:
                break
            self._process(request_id)

    def _load_engine(self) -> None:
        try:
            self._engine.load()
            logger.info("Model ready, waiting for questions")
        except Exception:
            # Keep the worker alive: each job will then fail with a clear error
            logger.exception("Model loading failed")

    def _process(self, request_id: str) -> None:
        job = self._store.get(request_id)
        if job is None:  # Expired before being processed
            return
        self._store.mark_processing(request_id)
        try:
            result = self._engine.generate(job.prompt, self._default_params)
            self._store.mark_completed(request_id, result)
        except Exception as error:
            logger.exception("Generation failed for %s", request_id)
            self._store.mark_failed(request_id, f"{type(error).__name__}: {error}")
