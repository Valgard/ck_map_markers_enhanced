# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Generate the mod's map-marker icons from tools/icons.toml.

Writes one MapMarkerIconDataBlock asset (plus .meta) per [[icon]] into
unity/MapMarkersEnhanced/Data/MapMarkerIconDataBlock/, and the C# tables into
unity/MapMarkersEnhanced/Scripts/Generated/IconTable.g.cs: the icon addresses,
the MapMarkers+ legacy mapping, and where each retired 1.x variant goes.
Each variant's sprite is resolved by name in both markers_large.png.meta and
markers_small.png.meta, and the variant order is checked against the layer
order of sources/mme_markers.pixaki; either failing aborts generation instead
of shipping a blank or misplaced icon.

    uv run tools/generate_icons.py           # write the outputs
    uv run tools/generate_icons.py --check   # write nothing, exit 1 on drift

A table, sheet or Pixaki that breaks a rule exits 2 before anything is written;
an .asset or .asset.meta in the output directory that the table does not
generate exits 1 in both modes.
"""

import argparse
import importlib.util
import json
import re
import sys
import tomllib
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TABLE = REPO / "tools/icons.toml"
MOD = REPO / "unity/MapMarkersEnhanced"
SHEET_METAS = (MOD / "Art/markers_large.png.meta", MOD / "Art/markers_small.png.meta")
PIXAKI = REPO / "sources/mme_markers.pixaki"
ASSET_DIR = MOD / "Data/MapMarkerIconDataBlock"
CSHARP = MOD / "Scripts/Generated/IconTable.g.cs"

SCRIPT_REF = "{fileID: 1194909520, guid: 5a7e404e57a3ed387bf565f46c30b9c1, type: 3}"
LEGACY_AMOUNT_BASE = 6000

# MapMarkers+ 1.1.1's PlusMarkerType, in enum order: a legacy marker's Amount
# is 6000 + the index of its type here.
LEGACY_TYPES: tuple[str, ...] = (
    "None",
    "FlagRed",
    "FlagOrange",
    "FlagPeach",
    "FlagYellow",
    "FlagGreen",
    "FlagTeal",
    "FlagCyan",
    "FlagBlue",
    "FlagPurple",
    "FlagPink",
    "FlagBrown",
    "FlagBlack",
    "FlagGray",
    "FlagWhite",
    "AncientCrystal",
    "Copper",
    "Tin",
    "Iron",
    "Gold",
    "Scarlet",
    "Octarine",
    "Galaxite",
    "Solarite",
    "Pandorium",
    "Skull",
    "QuestionMark",
    "ExclamationMark",
    "MusicNote",
    "Heart",
    "ArrowLeft",
    "ArrowRight",
    "ArrowUp",
    "ArrowDown",
    "Flames",
    "Relucite",
    "LetterA",
    "LetterB",
    "LetterC",
    "LetterD",
    "LetterE",
    "LetterF",
    "LetterG",
    "LetterH",
    "LetterI",
    "LetterJ",
    "LetterK",
    "LetterL",
    "LetterM",
    "LetterN",
    "LetterO",
    "LetterP",
    "LetterQ",
    "LetterR",
    "LetterS",
    "LetterT",
    "LetterU",
    "LetterV",
    "LetterW",
    "LetterX",
    "LetterY",
    "LetterZ",
    "Number1",
    "Number2",
    "Number3",
    "Number4",
    "Number5",
    "Number6",
    "Number7",
    "Number8",
    "Number9",
    "Number0",
    "Cross",
    "SkullRed",
    "Chest",
    "Ping",
    "Sign",
    "Dagger",
    "Axe",
    "StructureWood",
    "StructureStone",
    "Leaf",
    "Fish",
    "Shield",
    "Cog",
)

# Types MapMarkers+ let vanilla create: they never carried a 6000 + t Amount.
LEGACY_EXCLUDED = frozenset(
    {"None", "Ping", "AncientCrystal", "QuestionMark", "Skull", "FlagGreen"}
)


# Pixaki layers present in an icon's Large group that are never cut: vanilla
# draws these motifs itself. Both sheet definitions in sources/ exclude the same.
EXCLUDED_LAYERS = frozenset({"Question Mark", "Cross", "Skull", "Skull Red", "Diamond", "Ellipse"})

# A variant name becomes its layer name by a space before every inner capital or digit.
_INNER_BREAK = re.compile(r"(?<!^)(?=[A-Z0-9])")


@dataclass(frozen=True)
class VanillaTarget:
    """The vanilla block variant a retired variant is converted to."""

    block: str
    address: str
    variant: int


@dataclass(frozen=True)
class Variant:
    """One marker of a new block: its name and, where it differs, its Pixaki layer name."""

    name: str
    layer: str | None

    @property
    def sprite(self) -> str:
        """The sprite's name in both sheets, which is the Pixaki layer name."""
        return self.layer or _INNER_BREAK.sub(" ", self.name)


@dataclass(frozen=True)
class Icon:
    """One MapMarkerIconDataBlock: a pinned address and its variants in dialog order."""

    name: str
    address: str
    variants: tuple[Variant, ...]


@dataclass(frozen=True)
class RetiredVariant:
    """One variant of a 1.x block: its PlusMarkerType name and its vanilla target if any."""

    type: str
    vanilla: VanillaTarget | None = None

    @property
    def legacy(self) -> bool:
        """Whether old MapMarkers+ markers of this type carry a 6000 + t Amount."""
        return self.type not in LEGACY_EXCLUDED


@dataclass(frozen=True)
class Retired:
    """A 1.x block no longer shipped: its address and its variants in 1.x index order."""

    name: str
    address: str
    variants: tuple[RetiredVariant, ...]


@dataclass(frozen=True)
class Sheet:
    """A sprite sheet: its .meta file name, sprite name -> internalID, its texture GUID."""

    name: str
    ids: dict[str, int]
    guid: str


def _vanilla_table(data: dict) -> dict[str, str]:
    """The [vanilla] table of parsed icons.toml data ({} if absent).

    Raises:
        ValueError: [vanilla] is not a table.
    """
    table = data.get("vanilla", {})
    if not isinstance(table, dict):
        raise ValueError("[vanilla] must be a table of block name = address")
    return dict(table)


def load_vanilla(path: Path) -> dict[str, str]:
    """The [vanilla] table of icons.toml: vanilla block name -> address ({} if absent)."""
    return _vanilla_table(tomllib.loads(path.read_text(encoding="utf-8")))


def _string(row: dict, key: str, where: str) -> str:
    """row[key] as a string; a missing or non-string value is a ValueError.

    `main` maps only ValueError to exit 2, so any other exception would surface
    as a traceback with exit 1, the code `--check` uses for drift.
    """
    value = row.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{where}: `{key}` must be a string, got {value!r}")
    return value


def _variant(icon: str, row: dict) -> Variant:
    """One [[icon.variant]] row: a `name` and an optional `layer`, nothing else."""
    where = f"icon {icon}: variant {row.get('name')!r}"
    if unknown := set(row) - {"name", "layer"}:
        raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}")
    layer = _string(row, "layer", where) if "layer" in row else None
    return Variant(_string(row, "name", where), layer)


def _retired_variant(block: str, row: dict, vanilla: dict[str, str]) -> RetiredVariant:
    """One [[retired.variant]] row: a `type` and an optional `vanilla` target."""
    where = f"retired {block}: variant {row.get('type')!r}"
    if unknown := set(row) - {"type", "vanilla"}:
        raise ValueError(f"{where}: unknown field(s) {sorted(unknown)}")
    target = None
    if (ref := row.get("vanilla")) is not None:
        where = f"{where}: vanilla target"
        if not isinstance(ref, dict) or set(ref) != {"icon", "variant"}:
            raise ValueError(f"{where} must be {{ icon = <block>, variant = <int> }}, got {ref!r}")
        block_name, index = ref["icon"], ref["variant"]
        if not isinstance(block_name, str):
            raise ValueError(f"{where}: icon {block_name!r} is not a block name")
        # bool is a subclass of int, and `true` would render as C# `True`.
        if not isinstance(index, int) or isinstance(index, bool):
            raise ValueError(f"{where}: variant {index!r} is not an integer")
        if block_name not in vanilla:
            raise ValueError(f"{where}: vanilla block {block_name} is not in [vanilla]")
        target = VanillaTarget(block_name, vanilla[block_name], index)
    return RetiredVariant(_string(row, "type", where), target)


def load_table(path: Path) -> tuple[tuple[Icon, ...], tuple[Retired, ...]]:
    """Read icons.toml into the new icons and the retired 1.x blocks, in table order.

    Raises:
        ValueError: the table breaks a rule of `validate`; [vanilla] is not a
            table; a row lacks its string `name`/`type`/`address` or has a field
            it does not know; a `vanilla` field is not exactly a string `icon`
            and an integer `variant`, or names a block that [vanilla] lacks.
    """
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    vanilla = _vanilla_table(data)
    icons = tuple(
        Icon(
            name=_string(icon, "name", "an [[icon]]"),
            address=_string(icon, "address", f"icon {icon.get('name')}"),
            variants=tuple(_variant(icon["name"], v) for v in icon.get("variant", ())),
        )
        for icon in data.get("icon", ())
    )
    retired = tuple(
        Retired(
            name=_string(block, "name", "a [[retired]]"),
            address=_string(block, "address", f"retired {block.get('name')}"),
            variants=tuple(
                _retired_variant(block["name"], v, vanilla) for v in block.get("variant", ())
            ),
        )
        for block in data.get("retired", ())
    )
    validate(icons, retired, vanilla)
    return icons, retired


def _canonical(address: str) -> str | None:
    """The lowercase canonical form of a UUID string, or None if it is not one."""
    try:
        return str(uuid.UUID(address))
    except ValueError:
        return None


def validate(
    icons: tuple[Icon, ...],
    retired: tuple[Retired, ...] = (),
    vanilla: dict[str, str] | None = None,
) -> None:
    """Reject a table the game would load wrongly without a word.

    The game keeps the first block registered at an address and drops the rest
    silently, and sorts each loader's blocks by address, so a duplicate or
    out-of-order address shows up only as a missing icon or a shuffled dialog.
    Addresses start with 0-7 to stay clear of the sign bit of the Guid's first
    field, should anything ever compare it as a signed number. A retired address
    is still stored in saved markers, so no new block may take it, and every
    retired variant needs somewhere to go.

    Raises:
        ValueError: a duplicate icon name, variant name or address; an address
            that is not a lowercase canonical UUID; a new address that is a
            retired one, does not ascend in table order or does not start with
            0-7; an icon without variants; a retired type that is not a
            PlusMarkerType or appears twice; a vanilla variant index outside
            0-9; a [vanilla] address that is not canonical or is one of the
            mod's own; a retired variant without a target.
    """
    retired_addresses: set[str] = set()
    legacy_types: set[str] = set()
    for block in retired:
        if _canonical(block.address) != block.address:
            raise ValueError(
                f"retired {block.name}: address {block.address} is not a lowercase canonical UUID"
            )
        if block.address in retired_addresses:
            raise ValueError(f"retired address {block.address} appears twice ({block.name})")
        retired_addresses.add(block.address)
        for v in block.variants:
            if v.type not in LEGACY_TYPES:
                raise ValueError(f"retired {block.name}: {v.type} is not a PlusMarkerType")
            if v.type in legacy_types:
                raise ValueError(f"retired {block.name}: {v.type} appears twice in [[retired]]")
            legacy_types.add(v.type)
            if v.vanilla is not None and not 0 <= v.vanilla.variant <= 9:
                raise ValueError(
                    f"retired {block.name}: vanilla variant {v.vanilla.variant} of {v.type} "
                    "must be in 0-9"
                )

    names: set[str] = set()
    variant_names: set[str] = set()
    addresses: set[str] = set()
    previous = None
    for icon in icons:
        if icon.name in names:
            raise ValueError(f"icon name {icon.name} appears twice")
        names.add(icon.name)
        address = icon.address
        if address in addresses:
            raise ValueError(f"address {address} appears twice (icon {icon.name})")
        addresses.add(address)
        if _canonical(address) != address:
            raise ValueError(
                f"icon {icon.name}: address {address} is not a lowercase canonical UUID"
            )
        if address in retired_addresses:
            raise ValueError(
                f"icon {icon.name}: address {address} is a retired 1.x address; mint a new one"
            )
        if address[0] not in "01234567":
            raise ValueError(f"icon {icon.name}: address {address} must start with 0-7")
        if previous is not None and address <= previous:
            raise ValueError(
                f"icon {icon.name}: address {address} does not ascend after {previous}"
            )
        previous = address
        if not icon.variants:
            raise ValueError(f"icon {icon.name} has no variant; the dialog would show nothing")
        for v in icon.variants:
            if v.name in variant_names:
                raise ValueError(f"icon {icon.name}: variant name {v.name} appears twice")
            variant_names.add(v.name)

    for block, address in (vanilla or {}).items():
        # The game parses these at runtime; a typo there would switch off conversion
        # and restoration alike (the Legacy table points vanilla types at them too).
        if not isinstance(address, str) or _canonical(address) != address:
            raise ValueError(
                f"vanilla block {block}: address {address!r} is not a lowercase canonical UUID"
            )
        if address in addresses | retired_addresses:
            raise ValueError(f"vanilla block {block}: address {address} is one of the mod's own")

    retired_targets(icons, retired)


def retired_targets(
    icons: tuple[Icon, ...], retired: tuple[Retired, ...]
) -> dict[tuple[str, int], tuple[str, int]]:
    """(retired address, 1.x index) -> (target address, variant index).

    The target is the variant's vanilla target if it has one, else the new
    variant of the same name.

    Raises:
        ValueError: a retired variant has neither.
    """
    new = {v.name: (icon.address, n) for icon in icons for n, v in enumerate(icon.variants)}
    targets: dict[tuple[str, int], tuple[str, int]] = {}
    for block in retired:
        for index, v in enumerate(block.variants):
            if v.vanilla is not None:
                target = (v.vanilla.address, v.vanilla.variant)
            elif v.type in new:
                target = new[v.type]
            else:
                raise ValueError(
                    f"retired {block.name}: variant {index} ({v.type}) has no target — "
                    "neither a vanilla target nor a new variant of that name"
                )
            targets[(block.address, index)] = target
    return targets


def _pixaki_container():
    """utils/pixaki_container.py of the first ancestor directory that has one.

    The mod repository sits inside the shared core_keeper repository, directly
    or inside one of its own worktrees, so the depth is not fixed.

    Raises:
        ValueError: no ancestor has it, or the one found does not import.
    """
    for parent in (REPO, *REPO.parents):
        candidate = parent / "utils/pixaki_container.py"
        if candidate.is_file():
            try:
                spec = importlib.util.spec_from_file_location("pixaki_container", candidate)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except Exception as err:  # a broken reader is broken input, not drift
                raise ValueError(f"cannot import {candidate}: {err!r}") from err
            return module
    raise ValueError(f"no utils/pixaki_container.py in any directory above {REPO}")


def pixaki_order(pixaki: Path) -> dict[str, list[str]]:
    """Icon group -> the layer names of its `Large` group, top layer first, unfiltered.

    An icon group is any group holding a group named `Large`. The document
    stores layers bottom-up, so each list is reversed into Pixaki's own order.

    Raises:
        ValueError: the file does not exist or is not a readable Pixaki, no
            pixaki reader is found, or two icon groups share a name.
    """
    if not pixaki.exists():
        raise ValueError(f"Pixaki master {pixaki} not found")
    container_module = _pixaki_container()
    try:
        with container_module.open_pixaki(pixaki) as container:
            document = json.loads(container.read("document.json"))
    except (OSError, KeyError, zipfile.BadZipFile, ValueError) as err:
        raise ValueError(f"cannot read the Pixaki master {pixaki}: {err!r}") from err
    order: dict[str, list[str]] = {}

    def walk(layers: list[dict]) -> None:
        for layer in layers:
            if layer.get("type") != "group":
                continue
            children = layer["group"]["layers"]
            large = [c for c in children if c.get("type") == "group" and c["name"] == "Large"]
            if large:
                if layer["name"] in order:
                    raise ValueError(f"Pixaki group {layer['name']} appears twice")
                order[layer["name"]] = [c["name"] for c in reversed(large[0]["group"]["layers"])]
            else:
                walk(children)

    try:
        walk(document["sprites"][0]["layers"])
    except (KeyError, IndexError, TypeError) as err:
        raise ValueError(f"malformed Pixaki document in {pixaki}: {err!r}") from err
    return order


def check_order(icons: tuple[Icon, ...], order: dict[str, list[str]]) -> None:
    """Each icon's variants, as sprite names, must be its Pixaki Large group minus EXCLUDED_LAYERS.

    Raises:
        ValueError: an icon has no Pixaki group, or its variants are in another
            order or set than the layers.
    """
    for icon in icons:
        if icon.name not in order:
            raise ValueError(f"icon {icon.name} has no group with a Large group in the Pixaki")
        layers = [name for name in order[icon.name] if name not in EXCLUDED_LAYERS]
        sprites = [v.sprite for v in icon.variants]
        if sprites != layers:
            raise ValueError(
                f"icon {icon.name}: variant order differs from the Pixaki layer order\n"
                f"  table:  {sprites}\n  Pixaki: {layers}"
            )


_SPRITE_NAME = re.compile(r"^      name: (.*)$")
_SPRITE_ID = re.compile(r"^      internalID: (-?\d+)$")
_GUID = re.compile(r"^guid: ([0-9a-f]{32})$", re.MULTILINE)


def sprite_ids(meta_text: str) -> dict[str, int]:
    """Sprite name -> internalID, from a multiple-sprite texture's .meta."""
    ids: dict[str, int] = {}
    name = None
    for line in meta_text.splitlines():
        if m := _SPRITE_NAME.match(line):
            name = m.group(1).strip()
        elif (m := _SPRITE_ID.match(line)) and name is not None:
            ids[name] = int(m.group(1))
            name = None
    return ids


def png_guid(meta_text: str) -> str:
    """The texture's own GUID, from the top-level guid line of its .meta."""
    m = _GUID.search(meta_text)
    if m is None:
        raise ValueError("no top-level guid in the sprite sheet's .meta")
    return m.group(1)


def load_sheet(meta: Path) -> Sheet:
    """A sprite sheet, read from its .meta."""
    try:
        text = meta.read_text(encoding="utf-8")
    except OSError as err:
        raise ValueError(f"cannot read sprite sheet meta {meta}: {err}") from err
    return Sheet(meta.name, sprite_ids(text), png_guid(text))


def address_fields(address: str) -> tuple[int, int]:
    """(m_low, m_high) of a DataBlockAddress, whose Guid overlays both fields."""
    raw = uuid.UUID(address).bytes_le
    return (
        int.from_bytes(raw[:8], "little", signed=True),
        int.from_bytes(raw[8:], "little", signed=True),
    )


def _sprite_ref(name: str, sheet: Sheet) -> str:
    if name not in sheet.ids:
        raise ValueError(f"sprite {name} not found in {sheet.name}")
    return f"{{fileID: {sheet.ids[name]}, guid: {sheet.guid}, type: 3}}"


def render_asset(icon: Icon, large: Sheet, small: Sheet) -> str:
    """The icon's MapMarkerIconDataBlock asset as Unity YAML.

    Each variant takes its map sprite and colour icon from the large sheet and
    its minimap sprite from the small one, both under the same name.

    Raises:
        ValueError: a variant's sprite is missing from either sheet.
    """
    low, high = address_fields(icon.address)
    lines = [
        "%YAML 1.1",
        "%TAG !u! tag:unity3d.com,2011:",
        "--- !u!114 &11400000",
        "MonoBehaviour:",
        "  m_ObjectHideFlags: 0",
        "  m_CorrespondingSourceObject: {fileID: 0}",
        "  m_PrefabInstance: {fileID: 0}",
        "  m_PrefabAsset: {fileID: 0}",
        "  m_GameObject: {fileID: 0}",
        "  m_Enabled: 1",
        "  m_EditorHideFlags: 0",
        f"  m_Script: {SCRIPT_REF}",
        f"  m_Name: {icon.name}",
        "  m_EditorClassIdentifier: ",
        "  m_overload:",
        "    m_address:",
        "      m_low: 0",
        "      m_high: 0",
        "  m_address:",
        f"    m_low: {low}",
        f"    m_high: {high}",
        "  m_dynamicCollections:",
        "    m_list: []",
        "  variants:",
    ]
    for v in icon.variants:
        large_ref = _sprite_ref(v.sprite, large)
        lines += [
            f"  - largeMapSprite: {large_ref}",
            f"    miniMapSprite: {_sprite_ref(v.sprite, small)}",
            f"    colorIcon: {large_ref}",
        ]
    lines += [
        "  references:",
        "    version: 2",
        "    RefIds: []",
    ]
    return "\n".join(lines) + "\n"


def render_meta(icon: Icon) -> str:
    """The asset's .meta, with a GUID derived from the icon's name."""
    guid = uuid.uuid5(uuid.NAMESPACE_URL, "MapMarkersEnhanced/" + icon.name).hex
    return (
        "fileFormatVersion: 2\n"
        f"guid: {guid}\n"
        "NativeFormatImporter:\n"
        "  externalObjects: {}\n"
        "  mainObjectFileID: 11400000\n"
        "  userData: \n"
        "  assetBundleName: \n"
        "  assetBundleVariant: \n"
    )


_PAIR_MAP = "Dictionary<(string icon, int variant), (string address, int variant)>"


def render_csharp(icons: tuple[Icon, ...], retired: tuple[Retired, ...]) -> str:
    """IconTable.g.cs: the icon addresses, the legacy Amount mapping, the retired variants.

    Raises:
        ValueError: a retired variant has no target.
    """
    targets = retired_targets(icons, retired)
    lines = [
        "// <auto-generated>",
        "// Generated by tools/generate_icons.py from tools/icons.toml. Do not edit;",
        "// change the table and regenerate.",
        "// </auto-generated>",
        "using System.Collections.Generic;",
        "",
        "namespace MapMarkersEnhanced",
        "{",
        "    internal static class IconTable",
        "    {",
        "        /// <summary>The mod's icon addresses, in dialog order.</summary>",
        "        public static readonly string[] ModIconAddresses =",
        "        {",
    ]
    lines += [f'            "{icon.address}",' for icon in icons]
    lines += [
        "        };",
        "",
        "        /// <summary>Legacy MapMarkers+ Amount (6000 + PlusMarkerType)"
        " to icon address and variant index.</summary>",
        "        public static readonly Dictionary<int, (string address, int variant)> Legacy ="
        " new Dictionary<int, (string address, int variant)>",
        "        {",
    ]
    for block in retired:
        for index, v in enumerate(block.variants):
            if v.legacy:
                amount = LEGACY_AMOUNT_BASE + LEGACY_TYPES.index(v.type)
                address, variant = targets[(block.address, index)]
                lines.append(f'            {{{amount}, ("{address}", {variant})}}, // {v.type}')
    lines += [
        "        };",
        "",
        "        /// <summary>Retired 1.x variants (icon address, variant index)"
        " to the new or vanilla variant they are converted to.</summary>",
        f"        public static readonly {_PAIR_MAP} Retired = new {_PAIR_MAP}",
        "        {",
    ]
    for block in retired:
        for index, v in enumerate(block.variants):
            address, variant = targets[(block.address, index)]
            lines.append(
                f'            {{("{block.address}", {index}), ("{address}", {variant})}},'
                f" // {block.name} {v.type}"
            )
    lines += [
        "        };",
        "    }",
        "}",
    ]
    return "\n".join(lines) + "\n"


def outputs() -> dict[Path, str]:
    """Every generated file, path -> content.

    Raises:
        ValueError: the table, the Pixaki order or a sheet refuses; nothing is
            rendered for writing until all of them pass.
    """
    icons, retired = load_table(TABLE)
    check_order(icons, pixaki_order(PIXAKI))
    large, small = (load_sheet(meta) for meta in SHEET_METAS)
    result: dict[Path, str] = {}
    for icon in icons:
        result[ASSET_DIR / f"{icon.name}.asset"] = render_asset(icon, large, small)
        result[ASSET_DIR / f"{icon.name}.asset.meta"] = render_meta(icon)
    result[CSHARP] = render_csharp(icons, retired)
    return result


def orphans(files: dict[Path, str], asset_dir: Path) -> list[Path]:
    """Assets and metas in asset_dir that the table does not generate.

    A renamed icon leaves its old asset behind with the same address; both get
    bundled, and the game keeps whichever registers first without a word.
    """
    return sorted(
        p
        for p in asset_dir.glob("*")
        if p.name.endswith((".asset", ".asset.meta")) and p not in files
    )


def _shown(path: Path) -> Path:
    return path.relative_to(REPO) if path.is_relative_to(REPO) else path


def main(argv=None) -> int:
    """Write the outputs, or with --check report drift and exit 1.

    A leftover asset the table no longer generates fails both modes: it is
    reported, never deleted, since only the author knows it is a leftover.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="write nothing; exit 1 if any output differs"
    )
    args = parser.parse_args(argv)
    try:
        files = outputs()
    except ValueError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    stale = []
    for path, text in files.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == text:
            continue
        stale.append(path)
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    for path in stale:
        verb = "differs" if args.check else "wrote"
        print(f"{verb}: {_shown(path)}")
    leftovers = orphans(files, ASSET_DIR)
    for path in leftovers:
        print(f"orphan, not generated by the table: {_shown(path)}")
    return 1 if (args.check and stale) or leftovers else 0


if __name__ == "__main__":
    sys.exit(main())
