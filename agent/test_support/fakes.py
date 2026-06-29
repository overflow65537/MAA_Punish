"""Fake Maa Framework objects for agent unit tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeBestResult:
    box: tuple[int, int, int, int]


@dataclass
class FakeRecognitionResult:
    hit: bool = False
    best_result: FakeBestResult | None = None
    filtered_results: list[FakeBestResult] = field(default_factory=list)


@dataclass
class FakeJob:
    image: bytes = b"fake"

    def wait(self) -> FakeJob:
        return self

    def get(self) -> bytes:
        return self.image


@dataclass
class FakeController:
    clicks: list[tuple[int, int]] = field(default_factory=list)
    swipes: list[tuple[int, int, int, int, int]] = field(default_factory=list)
    image: bytes = b"fake"

    def post_screencap(self) -> FakeJob:
        return FakeJob(image=self.image)

    def post_click(self, x: int, y: int) -> FakeJob:
        self.clicks.append((x, y))
        return FakeJob()

    def post_swipe(
        self, x1: int, y1: int, x2: int, y2: int, duration: int
    ) -> FakeJob:
        self.swipes.append((x1, y1, x2, y2, duration))
        return FakeJob()


@dataclass
class FakeTasker:
    controller: FakeController = field(default_factory=FakeController)


@dataclass
class FakeContext:
    """Minimal Maa Context stand-in for unit tests."""

    recognition_map: dict[str, FakeRecognitionResult] = field(default_factory=dict)
    check_role_results: list[FakeRecognitionResult | None] = field(default_factory=list)
    check_role_calls: list[dict[str, Any]] = field(default_factory=list)
    node_data: dict[str, dict[str, Any]] = field(default_factory=dict)
    pipeline_overrides: list[dict[str, Any]] = field(default_factory=list)
    tasker: FakeTasker = field(default_factory=FakeTasker)

    def run_recognition(
        self,
        entry: str,
        image: Any = None,
        pipeline_override: dict[str, Any] | None = None,
    ) -> FakeRecognitionResult | None:
        if entry == "检查角色":
            self.check_role_calls.append(
                {
                    "entry": entry,
                    "image": image,
                    "pipeline_override": pipeline_override,
                }
            )
            if self.check_role_results:
                return self.check_role_results.pop(0)
            return FakeRecognitionResult(hit=False)

        if entry in self.recognition_map:
            return self.recognition_map[entry]

        return FakeRecognitionResult(hit=False)

    def get_node_data(self, name: str) -> dict[str, Any] | None:
        return self.node_data.get(name)

    def override_pipeline(self, patch: dict[str, Any]) -> None:
        self.pipeline_overrides.append(patch)
        for node_name, node_patch in patch.items():
            current = self.node_data.setdefault(node_name, {})
            if isinstance(node_patch, dict):
                current.update(node_patch)


def make_hit(box: tuple[int, int, int, int] = (100, 200, 40, 40)) -> FakeRecognitionResult:
    best = FakeBestResult(box=box)
    return FakeRecognitionResult(hit=True, best_result=best, filtered_results=[best])


def make_miss() -> FakeRecognitionResult:
    return FakeRecognitionResult(hit=False)
