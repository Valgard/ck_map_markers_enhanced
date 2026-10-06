# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Generate the mod's map-marker icons from tools/icons.toml.

Writes one MapMarkerIconDataBlock asset (plus .meta) per icon into
unity/MapMarkersEnhanced/Data/MapMarkerIconDataBlock/, and the C# legacy
mapping and the ToVanilla table of hidden variants into
unity/MapMarkersEnhanced/Scripts/Generated/IconTable.g.cs.
Sprites are resolved through their internalID in markers.png.meta; a sprite
that does not exist aborts generation instead of shipping a blank icon.

    uv run tools/generate_icons.py           # write the outputs
    uv run tools/generate_icons.py --check   # write nothing, exit 1 on drift

A table that breaks a rule of `validate` exits 2; an .asset or .asset.meta in
the output directory that the table does not generate exits 1 in both modes.
"""

import argparse
import re
import sys
import tomllib
import uuid
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TABLE = REPO / "tools/icons.toml"
MOD = REPO / "unity/MapMarkersEnhanced"
SHEET_META = MOD / "Art/markers.png.meta"
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


@dataclass(frozen=True)
class VanillaTarget:
    """The vanilla block variant a hidden variant is converted to."""

    block: str
    address: str
    variant: int


@dataclass(frozen=True)
class Variant:
    """One marker: a PlusMarkerType name, its minimap slice if any, its vanilla target if any."""

    type: str
    small: str | None
    vanilla: VanillaTarget | None = None

    @property
    def hidden(self) -> bool:
        """Whether the dialog hides this variant and converts it to its vanilla target."""
        return self.vanilla is not None

    @property
    def large(self) -> str:
        """Name of the full-size sprite in markers.png."""
        return f"markers_{self.type}"

    @property
    def legacy(self) -> bool:
        """Whether old MapMarkers+ markers of this type carry a 6000 + t Amount."""
        return self.type not in LEGACY_EXCLUDED


@dataclass(frozen=True)
class Icon:
    """One MapMarkerIconDataBlock: a pinned address and its variants in dialog order."""

    name: str
    address: str
    variants: tuple[Variant, ...]


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


def _variant(icon: str, row: dict, vanilla: dict[str, str]) -> Variant:
    """One variant row; a malformed `vanilla` field is a ValueError, not a KeyError.

    `main` maps only ValueError to exit 2, so any other exception would surface
    as a traceback with exit 1, the code `--check` uses for drift.
    """
    target = None
    if (ref := row.get("vanilla")) is not None:
        where = f"icon {icon}: vanilla target of {row.get('type')}"
        if not isinstance(ref, dict) or set(ref) != {"icon", "variant"}:
            raise ValueError(f"{where} must be {{ icon = <block>, variant = <int> }}, got {ref!r}")
        block, index = ref["icon"], ref["variant"]
        if not isinstance(block, str):
            raise ValueError(f"{where}: icon {block!r} is not a block name")
        # bool is a subclass of int, and `true` would render as C# `True`.
        if not isinstance(index, int) or isinstance(index, bool):
            raise ValueError(f"{where}: variant {index!r} is not an integer")
        if block not in vanilla:
            raise ValueError(f"icon {icon}: vanilla block {block} is not in [vanilla]")
        target = VanillaTarget(block, vanilla[block], index)
    return Variant(row["type"], row.get("small"), target)


def load_table(path: Path) -> tuple[Icon, ...]:
    """Read icons.toml into icons, in table order, and validate them.

    Raises:
        ValueError: the table breaks a rule of `validate`; [vanilla] is not a
            table; a variant's `vanilla` field is not exactly a string `icon`
            and an integer `variant`, or names a vanilla block that [vanilla]
            does not list.
    """
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    vanilla = _vanilla_table(data)
    icons = tuple(
        Icon(
            name=icon["name"],
            address=icon["address"],
            variants=tuple(_variant(icon["name"], v, vanilla) for v in icon["variant"]),
        )
        for icon in data["icon"]
    )
    validate(icons, vanilla)
    return icons


def _canonical(address: str) -> str | None:
    """The lowercase canonical form of a UUID string, or None if it is not one."""
    try:
        return str(uuid.UUID(address))
    except ValueError:
        return None


def validate(icons: tuple[Icon, ...], vanilla: dict[str, str] | None = None) -> None:
    """Reject a table the game would load wrongly without a word.

    The game keeps the first block registered at an address and drops the rest
    silently, and sorts each loader's blocks by address, so a duplicate or
    out-of-order address shows up only as a missing icon or a shuffled dialog.
    Addresses start with 0-7 to stay clear of the sign bit of the Guid's first
    field, should anything ever compare it as a signed number.

    Raises:
        ValueError: a duplicate name or address; an address that is not a
            lowercase canonical UUID, does not ascend in table order, or does
            not start with 0-7; a variant type that is not a PlusMarkerType; a
            [vanilla] address that is not a lowercase canonical UUID or is one
            of the mod's own; a vanilla variant
            index outside 0-9; an icon whose variants are all hidden.
    """
    names: set[str] = set()
    addresses: set[str] = set()
    previous = None
    for block, address in (vanilla or {}).items():
        # The game parses these at runtime; a typo there would switch off conversion
        # and restoration alike (the Legacy table points hidden types at them too).
        if not isinstance(address, str) or _canonical(address) != address:
            raise ValueError(
                f"vanilla block {block}: address {address!r} is not a lowercase canonical UUID"
            )
        if address in {icon.address for icon in icons}:
            raise ValueError(f"vanilla block {block}: address {address} is one of the mod's own")
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
        if address[0] not in "01234567":
            raise ValueError(f"icon {icon.name}: address {address} must start with 0-7")
        if previous is not None and address <= previous:
            raise ValueError(
                f"icon {icon.name}: address {address} does not ascend after {previous}"
            )
        previous = address
        for v in icon.variants:
            if v.type not in LEGACY_TYPES:
                raise ValueError(f"icon {icon.name}: {v.type} is not a PlusMarkerType")
            if v.vanilla is not None and not 0 <= v.vanilla.variant <= 9:
                raise ValueError(
                    f"icon {icon.name}: vanilla variant {v.vanilla.variant} of {v.type} "
                    "must be in 0-9"
                )
        if all(v.hidden for v in icon.variants):
            raise ValueError(
                f"icon {icon.name} has no visible variant; the dialog would show nothing"
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


def address_fields(address: str) -> tuple[int, int]:
    """(m_low, m_high) of a DataBlockAddress, whose Guid overlays both fields."""
    raw = uuid.UUID(address).bytes_le
    return (
        int.from_bytes(raw[:8], "little", signed=True),
        int.from_bytes(raw[8:], "little", signed=True),
    )


def _sprite_ref(name: str, ids: dict[str, int], guid: str) -> str:
    if name not in ids:
        raise ValueError(f"sprite {name} not found in markers.png.meta")
    return f"{{fileID: {ids[name]}, guid: {guid}, type: 3}}"


def render_asset(icon: Icon, ids: dict[str, int], png_guid: str) -> str:
    """The icon's MapMarkerIconDataBlock asset as Unity YAML.

    Raises:
        ValueError: a variant names a sprite the sheet does not have.
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
        large = _sprite_ref(v.large, ids, png_guid)
        mini = _sprite_ref(v.small, ids, png_guid) if v.small else large
        lines += [
            f"  - largeMapSprite: {large}",
            f"    miniMapSprite: {mini}",
            f"    colorIcon: {large}",
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


def render_csharp(icons: tuple[Icon, ...]) -> str:
    """IconTable.g.cs: the icon addresses, the legacy Amount mapping, the hidden variants.

    Raises:
        ValueError: a legacy variant's type appears twice, which would otherwise
            surface only in game, as a failed static init, or is unknown.
    """
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
    seen: set[str] = set()
    for icon in icons:
        for index, v in enumerate(icon.variants):
            if not v.legacy:
                continue
            if v.type not in LEGACY_TYPES:
                raise ValueError(f"{v.type} is not a PlusMarkerType")
            if v.type in seen:
                raise ValueError(f"{v.type} appears twice in the table")
            seen.add(v.type)
            amount = LEGACY_AMOUNT_BASE + LEGACY_TYPES.index(v.type)
            address, variant = (
                (v.vanilla.address, v.vanilla.variant) if v.vanilla else (icon.address, index)
            )
            lines.append(f'            {{{amount}, ("{address}", {variant})}}, // {v.type}')
    lines += [
        "        };",
        "",
        "        /// <summary>Hidden variants (icon address, variant index)"
        " to the vanilla block variant they are converted to.</summary>",
        "        public static readonly Dictionary<(string icon, int variant),"
        " (string address, int variant)> ToVanilla ="
        " new Dictionary<(string icon, int variant), (string address, int variant)>",
        "        {",
    ]
    for icon in icons:
        for index, v in enumerate(icon.variants):
            if v.vanilla:
                lines.append(
                    f'            {{("{icon.address}", {index}),'
                    f' ("{v.vanilla.address}", {v.vanilla.variant})}}, // {v.type}'
                )
    lines += [
        "        };",
        "    }",
        "}",
    ]
    return "\n".join(lines) + "\n"


def outputs() -> dict[Path, str]:
    """Every generated file, path -> content."""
    icons = load_table(TABLE)
    meta_text = SHEET_META.read_text(encoding="utf-8")
    ids = sprite_ids(meta_text)
    guid = png_guid(meta_text)
    result: dict[Path, str] = {}
    for icon in icons:
        result[ASSET_DIR / f"{icon.name}.asset"] = render_asset(icon, ids, guid)
        result[ASSET_DIR / f"{icon.name}.asset.meta"] = render_meta(icon)
    result[CSHARP] = render_csharp(icons)
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
