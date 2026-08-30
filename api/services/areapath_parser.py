"""Deterministic Area Path -> (Platform, Module, Sub-module) parsing.

No config screen, no persisted rules, no per-path overrides, no database at
all — the WIQL query the DM writes is what controls scope; this is a pure
function over config.ADO_AREA_PATH_DROP_SEGMENTS /
ADO_AREA_PATH_JOIN_EXTRA_SUBMODULE_SEGMENTS. Never crashes, never guesses:
a missing segment becomes the literal placeholder UNASSIGNED rather than
inventing a value.
"""

from config import ADO_AREA_PATH_DROP_SEGMENTS, ADO_AREA_PATH_JOIN_EXTRA_SUBMODULE_SEGMENTS

UNASSIGNED = "(none)"


def split_area_path(area_path: str) -> list[str]:
    return [seg.strip() for seg in area_path.split("\\") if seg.strip()]


def parse_area_path(area_path: str | None) -> tuple[str, str, str]:
    """"EIB\\Core\\LOS\\MultiCollateral" -> ("Core", "LOS", "MultiCollateral").
    Fewer segments than needed -> UNASSIGNED for whatever's missing. More than
    3 segments after the drop -> extras fold into sub_module per
    ADO_AREA_PATH_JOIN_EXTRA_SUBMODULE_SEGMENTS."""
    if not area_path:
        return UNASSIGNED, UNASSIGNED, UNASSIGNED

    segments = split_area_path(area_path)
    remaining = segments[ADO_AREA_PATH_DROP_SEGMENTS:] if ADO_AREA_PATH_DROP_SEGMENTS < len(segments) else []

    platform = remaining[0] if len(remaining) >= 1 else UNASSIGNED
    module = remaining[1] if len(remaining) >= 2 else UNASSIGNED

    if len(remaining) < 3:
        sub_module = UNASSIGNED
    elif ADO_AREA_PATH_JOIN_EXTRA_SUBMODULE_SEGMENTS:
        sub_module = " / ".join(remaining[2:])
    else:
        sub_module = remaining[2]

    return platform, module, sub_module
