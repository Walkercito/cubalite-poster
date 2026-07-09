"""Background poster rendering so the UI thread never blocks on PIL."""

from __future__ import annotations

import contextlib
import queue
import threading
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from cubalite_poster.config import constants
from cubalite_poster.core.colors import Rgb
from cubalite_poster.core.generator import PosterGenerator
from cubalite_poster.models import PosterStyle
from cubalite_poster.ui.preview import pil_to_preview_floats


@dataclass(frozen=True)
class RenderJob:
    """Snapshot of form state for one generation."""

    generation_id: int
    headline: str
    fill_color: Rgb
    image_path: Path | None
    style: PosterStyle


@dataclass(frozen=True)
class RenderResult:
    generation_id: int
    preview_floats: list[float]
    full_image: Image.Image
    error: str | None = None


class RenderWorker:
    """Single daemon worker: always renders the latest queued job."""

    def __init__(self) -> None:
        self._jobs: queue.Queue[RenderJob | None] = queue.Queue()
        self._results: queue.Queue[RenderResult] = queue.Queue(maxsize=2)
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="poster-render-worker",
            daemon=True,
        )
        self._latest_id = 0
        self._lock = threading.Lock()

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._jobs.put(None)
        self._thread.join(timeout=2.0)

    def submit(self, job: RenderJob) -> None:
        with self._lock:
            self._latest_id = job.generation_id
        self._jobs.put(job)

    def poll(self) -> RenderResult | None:
        try:
            return self._results.get_nowait()
        except queue.Empty:
            return None

    def _run(self) -> None:
        while not self._stop.is_set():
            job = self._jobs.get()
            if job is None:
                return
            # Drain queue: only the newest snapshot matters.
            while True:
                try:
                    newer = self._jobs.get_nowait()
                except queue.Empty:
                    break
                if newer is None:
                    return
                job = newer

            with self._lock:
                if job.generation_id < self._latest_id:
                    continue

            result = self._render(job)
            self._push_result(result)

    def _render(self, job: RenderJob) -> RenderResult:
        try:
            image_source = job.image_path if job.image_path is not None else None
            full = PosterGenerator(
                image=image_source,
                fill_color=job.fill_color,
                headline=job.headline,
                style=job.style,
            ).render()
            preview = pil_to_preview_floats(full)
            return RenderResult(
                generation_id=job.generation_id,
                preview_floats=preview,
                full_image=full.copy(),
            )
        except Exception as exc:  # noqa: BLE001 — surface to UI status
            blank = Image.new(
                "RGB",
                (constants.POSTER_WIDTH, constants.POSTER_HEIGHT),
                (40, 40, 40),
            )
            return RenderResult(
                generation_id=job.generation_id,
                preview_floats=pil_to_preview_floats(blank),
                full_image=blank,
                error=str(exc),
            )

    def _push_result(self, result: RenderResult) -> None:
        try:
            self._results.put_nowait(result)
        except queue.Full:
            with contextlib.suppress(queue.Empty):
                self._results.get_nowait()
            with contextlib.suppress(queue.Full):
                self._results.put_nowait(result)
