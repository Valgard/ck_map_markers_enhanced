"""Tests for tools/generate_icons.py and the table it reads, tools/icons.toml."""

import sys
import uuid
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import generate_icons as gi  # noqa: E402

META = REPO / "unity/MapMarkersEnhanced/Art/markers.png.meta"
TABLE = TOOLS / "icons.toml"
PNG_GUID = "0123456789abcdef0123456789abcdef"

# MapMarkers+ 1.1.1, Scripts/Common/PlusMarkerCategory.cs — copied as literals so
# the table is checked against upstream, not against itself.
GENERAL = [
    "QuestionMark",
    "ExclamationMark",
    "MusicNote",
    "Cross",
    "ArrowLeft",
    "ArrowRight",
    "ArrowUp",
    "ArrowDown",
    "Chest",
    "Sign",
    "StructureWood",
    "StructureStone",
    "Leaf",
    "Fish",
    "Cog",
    "Heart",
    "Skull",
    "SkullRed",
    "Flames",
    "Shield",
    "Dagger",
    "Axe",
]
ORES_AND_GEMS = [
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
    "Relucite",
]
FLAGS = [
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
]
NUMBERS = [
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
]
LETTERS = [f"Letter{chr(c)}" for c in range(ord("A"), ord("Z") + 1)]

# MapMarkers+ 1.1.1, Scripts/Common/PlusMarkerType.cs, in enum order — a legacy
# marker's Amount is 6000 + the index here, so an insertion or a swap would send
# every later type to the wrong icon, permanently, in every restored save.
PLUS_MARKER_TYPE = [
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
]

# The addresses that have shipped. Saved markers store these, so a shipped
# address must never change: every marker using it would turn into the game's
# fallback sprite. New icons may be appended; these entries stay as they are.
SHIPPED_ADDRESSES = {
    "General": "0877e397-7e74-4b3f-b822-4d0f052e1b60",
    "OresAndGems": "1d93e76b-8037-44e9-97a9-1c69a3f57156",
    "Flags": "2e4b6d8c-a19b-476a-b770-8e293827689e",
    "Numbers": "6152c695-14f2-4344-bee4-a2967b880bd3",
    "Letters": "77aea3e9-b732-4217-92f4-1bc153361245",
}

SMALL_SPELLING = {
    "Skull": "markers_skull_small",
    "AncientCrystal": "markers_ancient_crystal_small",
}


@pytest.fixture(scope="module")
def icons():
    """The table as the generator reads it."""
    return gi.load_table(TABLE)


@pytest.fixture(scope="module")
def ids():
    """Sprite name -> internalID of the real sprite sheet."""
    return gi.sprite_ids(META.read_text(encoding="utf-8"))


def variants(icons):
    """All variants of all icons, flattened."""
    return [v for icon in icons for v in icon.variants]


def test_every_variant_has_a_large_sprite(icons, ids):
    """Every variant's large sprite exists in the sheet."""
    missing = [v.large for v in variants(icons) if v.large not in ids]
    assert missing == []


def test_small_sprite_where_one_exists(icons, ids):
    """A minimap slice is named exactly where the sheet has one."""
    for v in variants(icons):
        expected = SMALL_SPELLING.get(v.type, f"markers_{v.type}_small")
        if expected in ids:
            assert v.small == expected, v.type
        else:
            assert v.small is None, v.type
    by_name = {icon.name: icon for icon in icons}
    for name in ("Numbers", "Letters"):
        assert all(v.small is None for v in by_name[name].variants)


def test_all_shipped_markers_are_variants(icons):
    """Icons and variants follow PlusMarkerCategory.cs, letters appended."""
    assert [icon.name for icon in icons] == [
        "General",
        "OresAndGems",
        "Flags",
        "Numbers",
        "Letters",
    ]
    got = [[v.type for v in icon.variants] for icon in icons]
    assert got == [GENERAL, ORES_AND_GEMS, FLAGS, NUMBERS, LETTERS]
    assert [len(x) for x in got] == [22, 11, 14, 10, 26]


def test_addresses_unique_ascending_start_0_to_7(icons):
    """Addresses are distinct, canonical, ascending, and start with 0-7."""
    addresses = [icon.address for icon in icons]
    assert len(set(addresses)) == len(addresses)
    assert all(a == a.lower() for a in addresses)
    assert addresses == sorted(addresses)
    assert all(a[0] in "01234567" for a in addresses)
    assert all(str(uuid.UUID(a)) == a for a in addresses)


def test_legacy_coverage(icons):
    """Every PlusMarkerType is mapped or excluded, never both."""
    legacy_variant_types = {v.type for v in variants(icons) if v.legacy}
    for name in gi.LEGACY_TYPES:
        in_mapping = name in legacy_variant_types
        excluded = name in gi.LEGACY_EXCLUDED
        assert in_mapping != excluded, name
    assert set(gi.LEGACY_TYPES) >= gi.LEGACY_EXCLUDED
    assert legacy_variant_types <= set(gi.LEGACY_TYPES)
    assert len(gi.LEGACY_TYPES) == 85
    assert len(set(gi.LEGACY_TYPES)) == 85
    assert gi.LEGACY_TYPES.index("Copper") == 16
    assert gi.LEGACY_TYPES.index("MusicNote") == 28
    assert gi.LEGACY_TYPES[0] == "None"
    assert gi.LEGACY_TYPES[-1] == "Cog"


def test_address_fields_roundtrip():
    """m_low/m_high are the Guid's two little-endian halves."""
    address = "7e09f30c-8838-5604-2b46-8c13b0ef771e"
    raw = uuid.UUID(address).bytes_le
    low, high = gi.address_fields(address)
    assert low == int.from_bytes(raw[:8], "little", signed=True)
    assert high == int.from_bytes(raw[8:], "little", signed=True)
    assert gi.address_fields("00000000-0000-0000-0000-000000000000") == (0, 0)


def test_render_asset_references(icons, ids):
    """The asset carries the script, address and sprite references."""
    for icon in icons:
        text = gi.render_asset(icon, ids, PNG_GUID)
        assert (
            "m_Script: {fileID: 1194909520, guid: 5a7e404e57a3ed387bf565f46c30b9c1, type: 3}"
            in text
        )
        assert f"m_Name: {icon.name}\n" in text
        low, high = gi.address_fields(icon.address)
        assert f"  m_address:\n    m_low: {low}\n    m_high: {high}\n" in text
        large_lines = [line.strip() for line in text.splitlines() if "largeMapSprite:" in line]
        expected = [
            f"largeMapSprite: {{fileID: {ids[v.large]}, guid: {PNG_GUID}, type: 3}}"
            for v in icon.variants
        ]
        assert [line.removeprefix("- ") for line in large_lines] == expected
        mini = [line.strip() for line in text.splitlines() if "miniMapSprite:" in line]
        expected_mini = [
            f"miniMapSprite: {{fileID: {ids[v.small or v.large]}, guid: {PNG_GUID}, type: 3}}"
            for v in icon.variants
        ]
        assert mini == expected_mini
        color = [line.strip() for line in text.splitlines() if "colorIcon:" in line]
        expected_color = [
            f"colorIcon: {{fileID: {ids[v.large]}, guid: {PNG_GUID}, type: 3}}"
            for v in icon.variants
        ]
        assert color == expected_color


def test_legacy_excluded_is_exactly_the_vanilla_backed_types():
    """Upstream PlusMarkerUtility.TryGetVanillaInfo let vanilla create these, plus None."""
    assert {
        "None",
        "Ping",
        "AncientCrystal",
        "QuestionMark",
        "Skull",
        "FlagGreen",
    } == gi.LEGACY_EXCLUDED


def test_render_asset_rejects_missing_sprite(icons, ids):
    """A sprite missing from the sheet aborts rendering."""
    icon = icons[0]
    broken = gi.Icon(icon.name, icon.address, (gi.Variant("NoSuchMarker", None),))
    with pytest.raises(ValueError, match="markers_NoSuchMarker"):
        gi.render_asset(broken, ids, PNG_GUID)


def test_csharp_table_agrees(icons):
    """The C# mapping lists exactly the legacy variants, addresses in order."""
    text = gi.render_csharp(icons)
    entries = 0
    for icon in icons:
        for index, v in enumerate(icon.variants):
            key = 6000 + gi.LEGACY_TYPES.index(v.type)
            entry = f'{{{key}, ("{icon.address}", {index})}}'
            if v.legacy:
                assert entry in text, v.type
                entries += 1
            else:
                assert f"{{{key}," not in text, v.type
    assert text.count("{60") == entries
    assert "namespace MapMarkersEnhanced" in text
    assert "internal static class IconTable" in text
    assert "public static readonly string[] ModIconAddresses" in text
    assert "public static readonly Dictionary<int, (string address, int variant)> Legacy" in text
    block = text.split("ModIconAddresses", 1)[1].split(";", 1)[0]
    positions = [block.find(f'"{icon.address}"') for icon in icons]
    assert all(p >= 0 for p in positions)
    assert positions == sorted(positions)


def test_generation_is_deterministic(icons, ids):
    """Rendering twice gives identical text; meta GUIDs are name-derived."""
    for icon in icons:
        assert gi.render_asset(icon, ids, PNG_GUID) == gi.render_asset(icon, ids, PNG_GUID)
        assert gi.render_meta(icon) == gi.render_meta(icon)
        expected_guid = uuid.uuid5(uuid.NAMESPACE_URL, "MapMarkersEnhanced/" + icon.name).hex
        assert f"guid: {expected_guid}\n" in gi.render_meta(icon)
    assert gi.render_csharp(icons) == gi.render_csharp(gi.load_table(TABLE))


def test_legacy_types_match_upstream_enum():
    """LEGACY_TYPES is PlusMarkerType, every name in enum order."""
    assert list(gi.LEGACY_TYPES) == PLUS_MARKER_TYPE
    assert len(PLUS_MARKER_TYPE) == 85


def test_shipped_addresses_never_change(icons):
    """Every shipped icon keeps its name and its address."""
    by_name = {icon.name: icon.address for icon in icons}
    assert {name: by_name.get(name) for name in SHIPPED_ADDRESSES} == SHIPPED_ADDRESSES


def test_committed_outputs_match_the_generator():
    """Every generated file on disk is byte-identical to what the table produces."""
    for path, text in gi.outputs().items():
        assert path.read_bytes() == text.encode("utf-8"), path.name


GOOD_A = "0877e397-7e74-4b3f-b822-4d0f052e1b60"
GOOD_B = "1d93e76b-8037-44e9-97a9-1c69a3f57156"


def write_table(tmp_path, *icons):
    """A minimal icons.toml with one QuestionMark variant per (name, address[, type])."""
    parts = []
    for name, address, *rest in icons:
        kind = rest[0] if rest else "QuestionMark"
        parts.append(
            f'[[icon]]\nname = "{name}"\naddress = "{address}"\n\n'
            f'[[icon.variant]]\ntype = "{kind}"\n'
        )
    path = tmp_path / "icons.toml"
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def test_valid_crafted_table_loads(tmp_path):
    """The crafted-table helper itself produces a table that passes validation."""
    icons = gi.load_table(write_table(tmp_path, ("A", GOOD_A), ("B", GOOD_B)))
    assert [icon.name for icon in icons] == ["A", "B"]


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ((("A", GOOD_A), ("A", GOOD_B)), "name A"),
        ((("A", GOOD_A), ("B", GOOD_A)), "address .* twice"),
        ((("A", GOOD_A.upper()),), "canonical"),
        ((("A", "not-a-uuid"),), "canonical"),
        ((("A", GOOD_A.replace("-", "")),), "canonical"),
        ((("A", GOOD_B), ("B", GOOD_A)), "ascend"),
        ((("A", "8" + GOOD_A[1:]),), "0-7"),
        ((("A", "f" + GOOD_A[1:]),), "0-7"),
        ((("A", GOOD_A, "NoSuchType"),), "NoSuchType"),
    ],
    ids=[
        "duplicate-name",
        "duplicate-address",
        "uppercase-address",
        "malformed-address",
        "unhyphenated-address",
        "descending-addresses",
        "address-from-8",
        "address-from-f",
        "unknown-type",
    ],
)
def test_load_table_rejects(tmp_path, rows, message):
    """Every table defect is a ValueError naming it, before anything is rendered."""
    with pytest.raises(ValueError, match=message):
        gi.load_table(write_table(tmp_path, *rows))


def test_orphans_flags_files_the_table_does_not_generate(tmp_path):
    """A leftover asset or meta in the output directory is reported."""
    for name in ("General.asset", "General.asset.meta", "Old.asset", "Old.asset.meta", "notes.txt"):
        (tmp_path / name).write_text("x", encoding="utf-8")
    expected = {tmp_path / "General.asset": "", tmp_path / "General.asset.meta": ""}
    assert gi.orphans(expected, tmp_path) == [tmp_path / "Old.asset", tmp_path / "Old.asset.meta"]


def test_check_fails_on_an_orphan(tmp_path, monkeypatch, capsys):
    """--check exits 1 and names the orphan, even when every generated file matches."""
    asset_dir = tmp_path / "MapMarkerIconDataBlock"
    asset_dir.mkdir()
    for path in gi.ASSET_DIR.iterdir():
        (asset_dir / path.name).write_bytes(path.read_bytes())
    monkeypatch.setattr(gi, "ASSET_DIR", asset_dir)
    assert gi.main(["--check"]) == 0
    (asset_dir / "Renamed.asset").write_text("x", encoding="utf-8")
    assert gi.main(["--check"]) == 1
    assert "Renamed.asset" in capsys.readouterr().out
