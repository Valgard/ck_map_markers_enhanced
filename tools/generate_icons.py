# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Generate the mod's map-marker icons from tools/icons.toml.

Writes one MapMarkerIconDataBlock asset (plus .meta) per icon into
unity/MapMarkersEnhanced/Data/MapMarkerIconDataBlock/, and the C# legacy
mapping into unity/MapMarkersEnhanced/Scripts/Generated/IconTable.g.cs.
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
class Variant:
    """One marker: a PlusMarkerType name and, where one exists, its minimap slice."""

    type: str
    small: str | None

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


def load_table(path: Path) -> tuple[Icon, ...]:
    """Read icons.toml into icons, in table order, and validate them.

    Raises:
        ValueError: the table breaks a rule of `validate`.
    """
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    icons = tuple(
        Icon(
            name=icon["name"],
            address=icon["address"],
            variants=tuple(Variant(v["type"], v.get("small")) for v in icon["variant"]),
        )
        for icon in data["icon"]
    )
    validate(icons)
    return icons


def validate(icons: tuple[Icon, ...]) -> None:
    """Reject a table the game would load wrongly without a word.

    The game keeps the first block registered at an address and drops the rest
    silently, and sorts each loader's blocks by address, so a duplicate or
    out-of-order address shows up only as a missing icon or a shuffled dialog.
    Addresses start with 0-7 to stay clear of the sign bit of the Guid's first
    field, should anything ever compare it as a signed number.

    Raises:
        ValueError: a duplicate name or address; an address that is not a
            lowercase canonical UUID, does not ascend in table order, or does
            not start with 0-7; a variant type that is not a PlusMarkerType.
    """
    names: set[str] = set()
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
        try:
            canonical = str(uuid.UUID(address))
        except ValueError:
            canonical = None
        if canonical != address:
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
    """IconTable.g.cs: the icon addresses and the legacy Amount mapping.

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
            lines.append(f'            {{{amount}, ("{icon.address}", {index})}}, // {v.type}')
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
