import io
import re
from dataclasses import dataclass
from typing import Any

from PIL import Image

VALUE_PATTERN = re.compile(r"\d+(?:\.\d+)?")


@dataclass
class GaugeBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def x_center(self) -> float:
        return (self.x_min + self.x_max) / 2

    @property
    def y_center(self) -> float:
        return (self.y_min + self.y_max) / 2

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min

    def expanded(self, ratio: float = 0.35) -> "GaugeBox":
        dx = self.width * ratio
        dy = self.height * ratio
        return GaugeBox(
            x_min=self.x_min - dx,
            y_min=self.y_min - dy,
            x_max=self.x_max + dx,
            y_max=self.y_max + dy,
        )


def detect_red_value_boxes(content: bytes) -> list[GaugeBox]:
    loaded = _load_scaled_rgb_image(content)
    if loaded is None:
        return []
    image, scale = loaded
    width, height = image.size
    red_mask = _build_red_mask(image)
    boxes = _find_red_components(red_mask, width, height, scale)
    return _merge_close_boxes(boxes)


def _load_scaled_rgb_image(content: bytes) -> tuple[Image.Image, float] | None:
    try:
        image = Image.open(io.BytesIO(content)).convert("RGB")
    except Exception:
        return None

    original_width, original_height = image.size
    max_dimension = 1400
    scale = 1.0
    if max(original_width, original_height) > max_dimension:
        scale = max_dimension / max(original_width, original_height)
        image = image.resize((int(original_width * scale), int(original_height * scale)))
    return image, scale


def _build_red_mask(image: Image.Image) -> bytearray:
    width, height = image.size
    pixels = image.load()
    red_mask = bytearray(width * height)
    for y in range(height):
        row_offset = y * width
        for x in range(width):
            r, g, b = pixels[x, y]
            if r >= 145 and g <= 135 and b <= 135 and r >= g * 1.25 and r >= b * 1.25:
                red_mask[row_offset + x] = 1
    return red_mask


def _find_red_components(red_mask: bytearray, width: int, height: int, scale: float) -> list[GaugeBox]:
    visited = bytearray(width * height)
    boxes: list[GaugeBox] = []
    for y in range(height):
        for x in range(width):
            index = y * width + x
            if not red_mask[index] or visited[index]:
                continue
            component = _collect_component(red_mask, visited, width, height, x, y)
            if component is None:
                continue
            x_min, y_min, x_max, y_max, count = component
            box_width = x_max - x_min + 1
            box_height = y_max - y_min + 1
            area = box_width * box_height
            if count < 20 or area < 120 or box_width < 8 or box_height < 6:
                continue
            if box_width > width * 0.5 or box_height > height * 0.25:
                continue
            inv_scale = 1 / scale
            boxes.append(
                GaugeBox(
                    x_min=x_min * inv_scale,
                    y_min=y_min * inv_scale,
                    x_max=(x_max + 1) * inv_scale,
                    y_max=(y_max + 1) * inv_scale,
                )
            )
    return boxes


def _collect_component(
    mask: bytearray,
    visited: bytearray,
    width: int,
    height: int,
    start_x: int,
    start_y: int,
) -> tuple[int, int, int, int, int] | None:
    stack = [(start_x, start_y)]
    x_min = x_max = start_x
    y_min = y_max = start_y
    count = 0
    while stack:
        x, y = stack.pop()
        if x < 0 or y < 0 or x >= width or y >= height:
            continue
        index = y * width + x
        if visited[index] or not mask[index]:
            continue
        visited[index] = 1
        count += 1
        x_min = min(x_min, x)
        y_min = min(y_min, y)
        x_max = max(x_max, x)
        y_max = max(y_max, y)
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return (x_min, y_min, x_max, y_max, count) if count else None


def _merge_close_boxes(boxes: list[GaugeBox]) -> list[GaugeBox]:
    merged: list[GaugeBox] = []
    for box in sorted(boxes, key=lambda item: (item.y_min, item.x_min)):
        target_index = None
        for index, existing in enumerate(merged):
            if _boxes_are_close(existing, box):
                target_index = index
                break
        if target_index is None:
            merged.append(box)
            continue
        existing = merged[target_index]
        merged[target_index] = GaugeBox(
            x_min=min(existing.x_min, box.x_min),
            y_min=min(existing.y_min, box.y_min),
            x_max=max(existing.x_max, box.x_max),
            y_max=max(existing.y_max, box.y_max),
        )
    return sorted(merged, key=lambda item: (item.y_min, item.x_min))


def _boxes_are_close(left: GaugeBox, right: GaugeBox) -> bool:
    y_overlap = min(left.y_max, right.y_max) - max(left.y_min, right.y_min)
    x_gap = max(0.0, max(left.x_min, right.x_min) - min(left.x_max, right.x_max))
    y_gap = max(0.0, max(left.y_min, right.y_min) - min(left.y_max, right.y_max))
    return y_overlap > min(left.height, right.height) * 0.35 and x_gap <= 8 or y_gap <= 4 and x_gap <= 12


def is_gauge_form(boxes: list[GaugeBox]) -> bool:
    return len(boxes) >= 3


def extract_gauge_results(
    boxes: list[GaugeBox],
    fields: list[Any],
    label_specs: list[tuple[str, list[str]]],
) -> dict[str, int | float]:
    label_positions = _find_label_positions(fields, label_specs)
    value_boxes = [(box, _extract_box_value(box, fields)) for box in boxes]
    value_boxes = [(box, value) for box, value in value_boxes if value is not None]

    results: dict[str, int | float] = {}
    used_boxes: set[int] = set()
    for field_name, label_y in label_positions:
        best_index = None
        best_distance = None
        for index, (box, _value) in enumerate(value_boxes):
            if index in used_boxes:
                continue
            distance = abs(box.y_center - label_y)
            allowed = max(box.height * 3.0, 42)
            if distance > allowed:
                continue
            if best_distance is None or distance < best_distance:
                best_index = index
                best_distance = distance
        if best_index is None:
            continue
        used_boxes.add(best_index)
        value = value_boxes[best_index][1]
        results[field_name] = int(value) if float(value).is_integer() else round(value, 2)
    return results


def _find_label_positions(fields: list[Any], label_specs: list[tuple[str, list[str]]]) -> list[tuple[str, float]]:
    positions: list[tuple[str, float]] = []
    for field_name, labels in label_specs:
        label_re = re.compile("|".join(labels), flags=re.IGNORECASE)
        matched = [field for field in fields if label_re.search(str(getattr(field, "text", "")))]
        if matched:
            positions.append((field_name, sum(_field_y_center(field) for field in matched) / len(matched)))
    return sorted(positions, key=lambda item: item[1])


def _extract_box_value(box: GaugeBox, fields: list[Any]) -> float | None:
    target = box.expanded()
    candidates = [
        field
        for field in fields
        if target.x_min <= _field_x_center(field) <= target.x_max
        and target.y_min <= _field_y_center(field) <= target.y_max
    ]
    for field in sorted(candidates, key=lambda item: (_field_y_center(item), _field_x_center(item))):
        match = VALUE_PATTERN.search(str(getattr(field, "text", "")).replace(",", ""))
        if match:
            return float(match.group(0))
    return None


def _field_x_center(field: Any) -> float:
    return (float(getattr(field, "x_min", 0)) + float(getattr(field, "x_max", 0))) / 2


def _field_y_center(field: Any) -> float:
    return (float(getattr(field, "y_min", 0)) + float(getattr(field, "y_max", 0))) / 2
