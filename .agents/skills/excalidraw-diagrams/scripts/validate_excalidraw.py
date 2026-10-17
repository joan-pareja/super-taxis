"""Validate structural invariants for repository-native Excalidraw scenes."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

FONT_FAMILY = 8  # Comic Shanns
SHAPE_TYPES = {"rectangle", "ellipse", "diamond"}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        scene = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read valid JSON: {exc}"]

    if scene.get("type") != "excalidraw":
        errors.append("root type must be 'excalidraw'")
    elements = scene.get("elements")
    if not isinstance(elements, list):
        return errors + ["root elements must be a list"]

    active = [element for element in elements if not element.get("isDeleted", False)]
    ids = [element.get("id") for element in active]
    if any(not isinstance(element_id, str) for element_id in ids):
        errors.append("every active element must have a string id")
    duplicates = sorted(
        {
            element_id
            for element_id in ids
            if isinstance(element_id, str) and ids.count(element_id) > 1
        }
    )
    if duplicates:
        errors.append(f"duplicate active ids: {', '.join(duplicates)}")
    by_id = {
        element["id"]: element
        for element in active
        if isinstance(element.get("id"), str)
    }

    def backlinks(element: dict[str, Any], target_id: str, kind: str) -> int:
        refs = element.get("boundElements") or []
        return sum(
            ref.get("id") == target_id and ref.get("type") == kind for ref in refs
        )

    for element in active:
        element_id = element.get("id", "<missing-id>")
        kind = element.get("type")

        for ref in element.get("boundElements") or []:
            target = by_id.get(ref.get("id"))
            if target is None:
                errors.append(
                    f"{element_id}: orphan boundElements reference {ref.get('id')!r}"
                )
            elif ref.get("type") != target.get("type"):
                errors.append(
                    f"{element_id}: boundElements type mismatch for {target['id']}"
                )

        if kind == "text":
            if element.get("fontFamily") != FONT_FAMILY:
                errors.append(
                    f"{element_id}: fontFamily must be {FONT_FAMILY} (Comic Shanns)"
                )
            container_id = element.get("containerId")
            if not container_id:
                continue
            container = by_id.get(container_id)
            if container is None:
                errors.append(f"{element_id}: missing container {container_id!r}")
                continue
            if backlinks(container, element_id, "text") != 1:
                errors.append(
                    f"{element_id}: container must contain exactly one text backlink"
                )
            if (
                element.get("textAlign") != "center"
                or element.get("verticalAlign") != "middle"
            ):
                errors.append(f"{element_id}: bound text must be centred")
            if container.get("type") in SHAPE_TYPES:
                available_width = abs(float(container.get("width", 0))) - 16
                available_height = abs(float(container.get("height", 0))) - 16
                if (
                    float(element.get("width", 0)) > available_width
                    or float(element.get("height", 0)) > available_height
                ):
                    errors.append(
                        f"{element_id}: text does not fit inside {container_id}"
                    )

        if kind != "arrow":
            continue

        points = element.get("points")
        if not isinstance(points, list) or len(points) < 2:
            errors.append(f"{element_id}: arrow needs at least two points")
        elif len(points) == 2 and element.get("elbowed"):
            errors.append(f"{element_id}: direct two-point arrow must not be elbowed")
        elif len(points) > 2 and not element.get("elbowed"):
            errors.append(f"{element_id}: routed arrow must be elbowed")

        for end in ("startBinding", "endBinding"):
            binding = element.get(end)
            target_id = binding.get("elementId") if isinstance(binding, dict) else None
            if not isinstance(target_id, str) or target_id not in by_id:
                errors.append(f"{element_id}: {end} must target an active element")
                continue
            if backlinks(by_id[target_id], element_id, "arrow") != 1:
                errors.append(
                    f"{element_id}: {target_id} must contain exactly one arrow backlink"
                )

        labels = [
            ref
            for ref in element.get("boundElements") or []
            if ref.get("type") == "text"
        ]
        if len(labels) > 1:
            errors.append(f"{element_id}: arrow may have at most one bound label")
        if labels and isinstance(points, list) and len(points) >= 2:
            label = by_id.get(labels[0].get("id"))
            path_length = sum(
                math.hypot(float(b[0]) - float(a[0]), float(b[1]) - float(a[1]))
                for a, b in zip(points, points[1:])
            )
            if label and float(label.get("width", 0)) + 16 > path_length:
                errors.append(f"{element_id}: route is too short for its label")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()

    failed = False
    for path in args.files:
        errors = validate(path)
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"OK   {path}")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
