"""Tests for tools/generate_icons.py and the table it reads, tools/icons.toml."""

import json
import re
import sys
import uuid
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import generate_icons as gi  # noqa: E402

ART = REPO / "unity/MapMarkersEnhanced/Art"
LARGE_META = ART / "markers_large.png.meta"
SMALL_META = ART / "markers_small.png.meta"
PIXAKI = REPO / "sources/mme_markers.pixaki"
TABLE = TOOLS / "icons.toml"
LARGE_GUID = "0123456789abcdef0123456789abcdef"
SMALL_GUID = "fedcba9876543210fedcba9876543210"

# MapMarkers+ 1.1.1, Scripts/Common/PlusMarkerCategory.cs — copied as literals so
# the retired 1.x blocks are checked against upstream, not against themselves.
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
    *LETTERS,
    *NUMBERS,
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

# The 1.x addresses. Saved markers store these, so none may ever be used again by
# any block: the migration matches them, and a new block there would shadow it.
SHIPPED_ADDRESSES = {
    "General": "0877e397-7e74-4b3f-b822-4d0f052e1b60",
    "OresAndGems": "1d93e76b-8037-44e9-97a9-1c69a3f57156",
    "Flags": "2e4b6d8c-a19b-476a-b770-8e293827689e",
    "Numbers": "6152c695-14f2-4344-bee4-a2967b880bd3",
    "Letters": "77aea3e9-b732-4217-92f4-1bc153361245",
}

DIALOG_ORDER = ["General", "Ores", "Flags", "Tapestry", "Orbs", "Numbers", "Letters"]
EXCLUDED_LAYERS = {"Question Mark", "Cross", "Skull", "Skull Red", "Diamond", "Ellipse"}

VANILLA_ADDRESSES = {  # read at runtime on 1.3.0.4; see the handbook, world-and-mechanics.md
    "Cross": "adbecb0c-1236-bf84-d9ea-0516e188e2d0",
    "Dot": "f9203606-618b-6384-7a99-a790e5c6de35",
    "Flag": "3005a608-1b77-8604-8abe-d189ae05a0d8",
    "Home": "64007694-5b2f-5474-b8ad-9f972e822421",
    "Pickaxe": "a707985f-1e22-c2f4-e837-0cc32288f9c5",
    "Question": "7e09f30c-8838-5604-2b46-8c13b0ef771e",
    "Skull": "169f71d7-f86d-7234-abf0-0120b015262b",
    "Star": "0eafefb1-8776-40d4-3af9-98637e55183e",
}
VANILLA_TARGETS = {  # (retired icon, 1.x index, type) -> (vanilla block, variant), as in 1.1.0
    ("General", 0, "QuestionMark"): ("Question", 9),
    ("General", 3, "Cross"): ("Cross", 9),
    ("General", 16, "Skull"): ("Skull", 0),
    ("General", 17, "SkullRed"): ("Skull", 1),
    ("OresAndGems", 0, "AncientCrystal"): ("Dot", 2),
}

_LEGACY_ENTRY = re.compile(r'\{(\d+), \("([^"]+)", (\d+)\)\}')


@pytest.fixture(scope="module")
def table():
    """(icons, retired) as the generator reads them."""
    return gi.load_table(TABLE)


@pytest.fixture(scope="module")
def icons(table):
    """The new blocks."""
    return table[0]


@pytest.fixture(scope="module")
def retired(table):
    """The retired 1.x blocks."""
    return table[1]


@pytest.fixture(scope="module")
def sheets():
    """The two real sprite sheets, with stand-in GUIDs."""
    return (
        gi.Sheet(
            LARGE_META.name, gi.sprite_ids(LARGE_META.read_text(encoding="utf-8")), LARGE_GUID
        ),
        gi.Sheet(
            SMALL_META.name, gi.sprite_ids(SMALL_META.read_text(encoding="utf-8")), SMALL_GUID
        ),
    )


def legacy_entries(text):
    """Amount -> (address, variant) of the C# Legacy table."""
    block = text.split(" Legacy =", 1)[1].split("};", 1)[0]
    return {int(a): (addr, int(v)) for a, addr, v in _LEGACY_ENTRY.findall(block)}


# --- the new blocks -------------------------------------------------------------


def test_icon_order_and_counts(icons):
    """Seven icons in dialog order, with the spec's variant counts."""
    assert [icon.name for icon in icons] == DIALOG_ORDER
    assert [len(icon.variants) for icon in icons] == [18, 11, 14, 15, 19, 10, 26]


def test_addresses_ascend_and_start_low(icons):
    """Addresses are distinct, canonical, ascending, and start with 0-7."""
    addresses = [icon.address for icon in icons]
    assert len(set(addresses)) == len(addresses)
    assert addresses == sorted(addresses)
    assert all(a[0] in "01234567" for a in addresses)
    assert all(str(uuid.UUID(a)) == a for a in addresses)


def test_no_retired_address_reused(icons):
    """No new block sits at a 1.x address."""
    assert not {icon.address for icon in icons} & set(SHIPPED_ADDRESSES.values())


# The 2.0.0 identities, copied as literals. A saved marker stores (address, variant
# index), so these are shipped: the table may only grow at the end of a block.
NEW_ICONS = [
    ("General", "69ac8c2b-f5a2-45bd-8dcd-6004b352637b"),
    ("Ores", "715841ac-735e-4b1d-95db-ec6dd73bd12e"),
    ("Flags", "7259d242-79c6-429e-acfd-e5206ff6cd78"),
    ("Tapestry", "73d6f81d-077c-4548-b655-d4644b855323"),
    ("Orbs", "769702fa-b2cb-499f-9c7f-462442d995ec"),
    ("Numbers", "782323e6-7f6a-416d-8c63-edc0e05f87b1"),
    ("Letters", "7890a1b3-a5bd-42c6-a375-d116e12b8f10"),
]
_COLOURS = [
    "Red",
    "Orange",
    "Peach",
    "Yellow",
    "Green",
    "Teal",
    "Cyan",
    "Blue",
    "Purple",
    "Pink",
    "Brown",
    "Black",
    "Gray",
    "White",
]
NEW_VARIANTS = {
    "General": [
        "ExclamationMark",
        "MusicNote",
        "ArrowLeft",
        "ArrowRight",
        "ArrowUp",
        "ArrowDown",
        "Chest",
        "Sign",
        "Dagger",
        "Axe",
        "StructureWood",
        "Heart",
        "Flames",
        "StructureStone",
        "Leaf",
        "Fish",
        "Shield",
        "Cog",
    ],
    "Ores": [
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
        "RadiationCrystal",
    ],
    "Flags": [f"Flag{c}" for c in _COLOURS],
    "Tapestry": ["TapestryUnpainted"] + [f"Tapestry{c}" for c in _COLOURS],
    "Orbs": ["OrbEmpty"]
    + [f"Orb{c}" for c in _COLOURS]
    + ["OrbGold", "OrbYellowAlternative", "OrbLava", "OrbFlower"],
    "Numbers": [f"Number{n}" for n in [1, 2, 3, 4, 5, 6, 7, 8, 9, 0]],
    "Letters": [f"Letter{chr(c)}" for c in range(ord("A"), ord("Z") + 1)],
}


def test_new_icon_identities_are_pinned(icons):
    """The 2.0.0 addresses and variant order are shipped identities.

    A saved marker stores (address, variant index), so reordering or removing a
    variant, or changing an address, silently changes what existing markers show.
    test_variant_order_matches_the_pixaki cannot catch that: it compares the table
    with the sheet, and both can be reordered together. Appending at the end of a
    block is allowed: extend the literal above. Nothing else is.
    """
    assert [(icon.name, icon.address) for icon in icons] == NEW_ICONS
    for icon in icons:
        assert [v.name for v in icon.variants] == NEW_VARIANTS[icon.name], icon.name


def test_variant_sprite_is_the_layer_name():
    """A space goes before every inner capital or digit; MusicNote is the one exception."""
    assert gi.Variant("OrbYellowAlternative", None).sprite == "Orb Yellow Alternative"
    assert gi.Variant("Number1", None).sprite == "Number 1"
    assert gi.Variant("Copper", None).sprite == "Copper"
    assert gi.Variant("MusicNote", "Note").sprite == "Note"


def test_variant_order_matches_the_pixaki(icons):
    """Each icon's variants are its Pixaki Large group, top layer first, minus the excluded."""
    order = gi.pixaki_order(PIXAKI)
    for icon in icons:
        expected = [name for name in order[icon.name] if name not in EXCLUDED_LAYERS]
        assert [v.sprite for v in icon.variants] == expected, icon.name


def test_excluded_layers_match_the_sheet_definitions():
    """The generator's excluded layers are the ones both sheet definitions leave out."""
    assert gi.EXCLUDED_LAYERS == EXCLUDED_LAYERS
    for config, group in (("large", "Small"), ("small", "Large")):
        text = (REPO / f"sources/mme_markers.{config}.json").read_text(encoding="utf-8")
        assert set(json.loads(text)["excludeNested"]) == EXCLUDED_LAYERS | {group}


def test_every_variant_has_both_sprites(icons, sheets):
    """Every variant's sprite exists in both sheets."""
    large, small = sheets
    for v in (v for icon in icons for v in icon.variants):
        assert v.sprite in large.ids, v.name
        assert v.sprite in small.ids, v.name


def test_render_asset_references(icons, sheets):
    """The asset carries the script, the address, and each variant's large and small sprite."""
    large, small = sheets
    for icon in icons:
        text = gi.render_asset(icon, large, small)
        assert (
            "m_Script: {fileID: 1194909520, guid: 5a7e404e57a3ed387bf565f46c30b9c1, type: 3}"
            in text
        )
        assert f"m_Name: {icon.name}\n" in text
        low, high = gi.address_fields(icon.address)
        assert f"  m_address:\n    m_low: {low}\n    m_high: {high}\n" in text

        def refs(key, text=text):
            return [
                line.strip().removeprefix("- ") for line in text.splitlines() if f"{key}:" in line
            ]

        assert refs("largeMapSprite") == [
            f"largeMapSprite: {{fileID: {large.ids[v.sprite]}, guid: {LARGE_GUID}, type: 3}}"
            for v in icon.variants
        ]
        assert refs("miniMapSprite") == [
            f"miniMapSprite: {{fileID: {small.ids[v.sprite]}, guid: {SMALL_GUID}, type: 3}}"
            for v in icon.variants
        ]
        assert refs("colorIcon") == [
            f"colorIcon: {{fileID: {large.ids[v.sprite]}, guid: {LARGE_GUID}, type: 3}}"
            for v in icon.variants
        ]


def test_render_asset_rejects_missing_sprite(icons, sheets):
    """A sprite missing from either sheet aborts rendering, naming the sheet."""
    large, small = sheets
    icon = icons[0]
    broken = gi.Icon(icon.name, icon.address, (gi.Variant("NoSuchMarker", None),))
    with pytest.raises(ValueError, match=r"No Such Marker.*markers_large"):
        gi.render_asset(broken, large, small)
    only_large = gi.Sheet(small.name, {}, SMALL_GUID)
    with pytest.raises(ValueError, match="markers_small"):
        gi.render_asset(icon, large, only_large)


# --- the retired 1.x blocks -----------------------------------------------------


def test_retired_lists_still_mirror_mapmarkers(retired):
    """The five retired blocks list MapMarkers+ 1.1.1's categories, in 1.x index order."""
    assert [r.name for r in retired] == list(SHIPPED_ADDRESSES)
    got = [[v.type for v in r.variants] for r in retired]
    assert got == [GENERAL, ORES_AND_GEMS, FLAGS, NUMBERS, LETTERS]


def test_shipped_addresses_are_the_retired_ones(retired):
    """Every 1.x block keeps its name and address in [[retired]]."""
    assert {r.name: r.address for r in retired} == SHIPPED_ADDRESSES


def test_retired_vanilla_targets_are_the_five(retired):
    """Exactly the five 1.1.0 hidden variants carry a vanilla target, unchanged."""
    found = {
        (r.name, n, v.type): (v.vanilla.block, v.vanilla.variant)
        for r in retired
        for n, v in enumerate(r.variants)
        if v.vanilla
    }
    assert found == VANILLA_TARGETS


def test_every_retired_variant_has_exactly_one_target(icons, retired):
    """Each stored 1.x (address, index) maps to its vanilla target or its same-named variant."""
    targets = gi.retired_targets(icons, retired)
    assert len(targets) == 22 + 11 + 14 + 10 + 26
    new = {v.name: (icon.address, n) for icon in icons for n, v in enumerate(icon.variants)}
    for r in retired:
        for n, v in enumerate(r.variants):
            expected = (v.vanilla.address, v.vanilla.variant) if v.vanilla else new[v.type]
            assert targets[(r.address, n)] == expected, v.type
    general = SHIPPED_ADDRESSES["General"]
    ores = SHIPPED_ADDRESSES["OresAndGems"]
    assert targets[(general, 0)] == ("7e09f30c-8838-5604-2b46-8c13b0ef771e", 9)
    assert targets[(ores, 0)] == (VANILLA_ADDRESSES["Dot"], 2)
    by_name = {icon.name: icon for icon in icons}
    assert targets[(general, GENERAL.index("Heart"))] == (by_name["General"].address, 11)


def test_flag_green_goes_to_the_new_flags(icons, retired):
    """FlagGreen is a mod variant, not a vanilla duplicate."""
    targets = gi.retired_targets(icons, retired)
    flags = next(i for i in icons if i.name == "Flags")
    assert targets[(SHIPPED_ADDRESSES["Flags"], 4)] == (flags.address, 4)


# --- the generated C# -----------------------------------------------------------


def test_csharp_tables(icons, retired):
    """ModIconAddresses, Legacy and Retired agree with the table."""
    text = gi.render_csharp(icons, retired)
    assert "namespace MapMarkersEnhanced" in text
    assert "internal static class IconTable" in text
    block = text.split("ModIconAddresses", 1)[1].split(";", 1)[0]
    assert re.findall(r'"([^"]+)"', block) == [icon.address for icon in icons]

    targets = gi.retired_targets(icons, retired)
    assert (
        "public static readonly Dictionary<(string icon, int variant),"
        " (string address, int variant)> Retired" in text
    )
    retired_block = text.split(" Retired =", 1)[1].split("};", 1)[0]
    for (address, index), (target, variant) in targets.items():
        assert f'{{("{address}", {index}), ("{target}", {variant})}}' in retired_block
    assert retired_block.count('{("') == len(targets)
    assert "ToVanilla" not in text

    legacy = legacy_entries(text)
    expected = {}
    for r in retired:
        for n, v in enumerate(r.variants):
            if v.type not in gi.LEGACY_EXCLUDED:
                expected[6000 + gi.LEGACY_TYPES.index(v.type)] = targets[(r.address, n)]
    assert legacy == expected


def test_legacy_cross_and_skullred_go_to_vanilla(icons, retired):
    """MapMarkers+ Cross and SkullRed restore straight onto their vanilla targets."""
    legacy = legacy_entries(gi.render_csharp(icons, retired))
    assert legacy[6000 + gi.LEGACY_TYPES.index("Cross")] == (VANILLA_ADDRESSES["Cross"], 9)
    assert legacy[6000 + gi.LEGACY_TYPES.index("SkullRed")] == (VANILLA_ADDRESSES["Skull"], 1)


def test_legacy_coverage(retired):
    """Every PlusMarkerType is a retired legacy variant or excluded, never both."""
    legacy = {v.type for r in retired for v in r.variants if v.type not in gi.LEGACY_EXCLUDED}
    for name in gi.LEGACY_TYPES:
        assert (name in legacy) != (name in gi.LEGACY_EXCLUDED), name
    assert gi.LEGACY_TYPES.index("Copper") == 16
    assert gi.LEGACY_TYPES.index("MusicNote") == 28


def test_legacy_types_match_upstream_enum():
    """LEGACY_TYPES is PlusMarkerType, every name in enum order."""
    assert list(gi.LEGACY_TYPES) == PLUS_MARKER_TYPE
    assert len(PLUS_MARKER_TYPE) == 85


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


def test_address_fields_roundtrip():
    """m_low/m_high are the Guid's two little-endian halves."""
    address = "7e09f30c-8838-5604-2b46-8c13b0ef771e"
    raw = uuid.UUID(address).bytes_le
    low, high = gi.address_fields(address)
    assert low == int.from_bytes(raw[:8], "little", signed=True)
    assert high == int.from_bytes(raw[8:], "little", signed=True)
    assert gi.address_fields("00000000-0000-0000-0000-000000000000") == (0, 0)


def test_generation_is_deterministic(icons, retired, sheets):
    """Rendering twice gives identical text; meta GUIDs are name-derived."""
    large, small = sheets
    for icon in icons:
        assert gi.render_asset(icon, large, small) == gi.render_asset(icon, large, small)
        expected_guid = uuid.uuid5(uuid.NAMESPACE_URL, "MapMarkersEnhanced/" + icon.name).hex
        assert f"guid: {expected_guid}\n" in gi.render_meta(icon)
    assert gi.render_csharp(icons, retired) == gi.render_csharp(*gi.load_table(TABLE))


def test_committed_outputs_match_the_generator():
    """Every generated file on disk is byte-identical to what the table produces."""
    for path, text in gi.outputs().items():
        assert path.read_bytes() == text.encode("utf-8"), path.name


def test_vanilla_table_is_the_measured_one():
    """The [vanilla] table holds the eight measured vanilla block addresses."""
    assert gi.load_vanilla(TABLE) == VANILLA_ADDRESSES


MIGRATION_SYSTEM = REPO / "unity/MapMarkersEnhanced/Scripts/MarkerMigrationSystem.cs"


def test_migration_question_mark_matches_the_table():
    """MarkerMigrationSystem's question-mark constants agree with [vanilla] Question, variant 9."""
    source = MIGRATION_SYSTEM.read_text(encoding="utf-8")
    address = re.search(r'const string QuestionMarkAddress = "([^"]+)";', source)
    variant = re.search(r"const int QuestionMarkVariant = (\d+);", source)
    assert address and variant, "constants not found in MarkerMigrationSystem.cs"
    assert address.group(1) == gi.load_vanilla(TABLE)["Question"]
    assert int(variant.group(1)) == 9


# --- refusals: exit 2 before anything is written --------------------------------


def run_check(monkeypatch, capsys, *, table=None, small_meta=None):
    """main(["--check"]) against the real sources, with a table or small meta swapped in."""
    if table is not None:
        monkeypatch.setattr(gi, "TABLE", table)
    if small_meta is not None:
        monkeypatch.setattr(gi, "SHEET_METAS", (gi.SHEET_METAS[0], small_meta))
    code = gi.main(["--check"])
    return code, capsys.readouterr().err


def edited_table(tmp_path, old, new, count=1):
    """The real table with `old` replaced by `new` (`count` times), as a temp file."""
    text = TABLE.read_text(encoding="utf-8")
    assert text.count(old) >= count, old
    path = tmp_path / "icons.toml"
    path.write_text(text.replace(old, new, count), encoding="utf-8")
    return path


def test_real_sources_pass_the_check(monkeypatch, capsys):
    """The baseline the refusal tests vary: the real sources pass --check."""
    assert run_check(monkeypatch, capsys) == (0, "")


def test_missing_small_sprite_refuses(tmp_path, monkeypatch, capsys):
    """A variant whose sprite the small sheet lacks refuses, naming sprite and sheet."""
    meta = tmp_path / "markers_small.png.meta"
    text = SMALL_META.read_text(encoding="utf-8")
    assert "      name: Heart\n" in text
    meta.write_text(text.replace("      name: Heart\n", "      name: Hurt\n"), encoding="utf-8")
    code, err = run_check(monkeypatch, capsys, small_meta=meta)
    assert code == 2
    assert "Heart" in err and "markers_small" in err


def test_missing_sheet_meta_exits_2_not_a_traceback(tmp_path, monkeypatch, capsys):
    """A sheet .meta that is absent is broken input (exit 2), not drift (exit 1)."""
    code, err = run_check(monkeypatch, capsys, small_meta=tmp_path / "markers_small.png.meta")
    assert code == 2
    assert "markers_small.png.meta" in err


def test_malformed_pixaki_exits_2_not_a_traceback(tmp_path, monkeypatch, capsys):
    """A Pixaki that is no readable archive or document is broken input too."""
    bad = tmp_path / "mme_markers.pixaki"
    bad.write_bytes(b"not a pixaki")
    monkeypatch.setattr(gi, "PIXAKI", bad)
    code = gi.main(["--check"])
    assert code == 2
    assert "mme_markers.pixaki" in capsys.readouterr().err


def test_order_mismatch_refuses(tmp_path, monkeypatch, capsys):
    """Variants in a different order than the Pixaki layers refuse, naming the icon."""
    table = edited_table(tmp_path, 'name = "Copper"', 'name = "@"')
    table.write_text(
        table.read_text(encoding="utf-8")
        .replace('name = "Tin"', 'name = "Copper"')
        .replace('name = "@"', 'name = "Tin"'),
        encoding="utf-8",
    )
    code, err = run_check(monkeypatch, capsys, table=table)
    assert code == 2
    assert "Ores" in err and "order" in err


def test_retired_variant_without_target_refuses(tmp_path, monkeypatch, capsys):
    """A 1.x variant with neither a vanilla nor a same-named target refuses, naming it."""
    table = edited_table(
        tmp_path,
        'type = "QuestionMark"\nvanilla = { icon = "Question", variant = 9 }\n',
        'type = "QuestionMark"\n',
    )
    code, err = run_check(monkeypatch, capsys, table=table)
    assert code == 2
    assert "QuestionMark" in err and "target" in err


def test_retired_address_in_new_block_refuses(tmp_path, monkeypatch, capsys):
    """A new block at a retired address refuses, naming the address."""
    general = gi.load_table(TABLE)[0][0].address
    table = edited_table(tmp_path, general, SHIPPED_ADDRESSES["General"])
    code, err = run_check(monkeypatch, capsys, table=table)
    assert code == 2
    assert SHIPPED_ADDRESSES["General"] in err and "retired" in err


# --- table defects on crafted tables ----------------------------------------------

GOOD_A = "0aaaaaaa-7e74-4b3f-b822-4d0f052e1b60"
GOOD_B = "1bbbbbbb-8037-44e9-97a9-1c69a3f57156"
OLD_A = "2ccccccc-b732-4217-92f4-1bc153361245"
QUESTION = VANILLA_ADDRESSES["Question"]


def write_table(tmp_path, icons=(), retired=(), vanilla=None):
    """A minimal icons.toml.

    `icons` and `retired` are (name, address, rows); an icon row is a variant
    name or a dict of raw TOML fields, a retired row a type or such a dict. A
    dict value that is a str is quoted, anything else written verbatim.
    """

    def fields(row, key):
        row = {key: row} if isinstance(row, str) else row
        return "".join(
            f'{k} = "{v}"\n' if isinstance(v, str) and k != "vanilla" else f"{k} = {v}\n"
            for k, v in row.items()
        )

    parts = []
    if vanilla:
        parts.append(
            "[vanilla]\n"
            + "".join(
                f'{k} = "{v}"\n' if isinstance(v, str) else f"{k} = {v}\n"
                for k, v in vanilla.items()
            )
        )
    for kind, key, entries in (("icon", "name", icons), ("retired", "type", retired)):
        for name, address, rows in entries:
            text = f'[[{kind}]]\nname = "{name}"\naddress = "{address}"\n'
            for row in rows:
                text += f"\n[[{kind}.variant]]\n" + fields(row, key)
            parts.append(text)
    path = tmp_path / "icons.toml"
    path.write_text("\n".join(parts), encoding="utf-8")
    return path


def test_valid_crafted_table_loads(tmp_path):
    """The crafted-table helper itself produces a table that passes validation."""
    icons, retired = gi.load_table(
        write_table(
            tmp_path,
            icons=[("A", GOOD_A, ["Heart"]), ("B", GOOD_B, ["Fish"])],
            retired=[
                (
                    "Old",
                    OLD_A,
                    ["Heart", {"type": "Cross", "vanilla": '{ icon = "Q", variant = 9 }'}],
                )
            ],
            vanilla={"Q": QUESTION},
        )
    )
    assert [icon.name for icon in icons] == ["A", "B"]
    assert gi.retired_targets(icons, retired) == {
        (OLD_A, 0): (GOOD_A, 0),
        (OLD_A, 1): (QUESTION, 9),
    }


@pytest.mark.parametrize(
    ("icons", "retired", "message"),
    [
        ([("A", GOOD_A, ["Heart"]), ("A", GOOD_B, ["Fish"])], [], "name A"),
        ([("A", GOOD_A, ["Heart"]), ("B", GOOD_A, ["Fish"])], [], "address .* twice"),
        ([("A", GOOD_A.upper(), ["Heart"])], [], "canonical"),
        ([("A", "not-a-uuid", ["Heart"])], [], "canonical"),
        ([("A", GOOD_B, ["Heart"]), ("B", GOOD_A, ["Fish"])], [], "ascend"),
        ([("A", "8" + GOOD_A[1:], ["Heart"])], [], "0-7"),
        ([("A", GOOD_A, [])], [], "no variant"),
        ([("A", GOOD_A, ["Heart", "Heart"])], [], "Heart.*twice"),
        ([("A", GOOD_A, [{"name": "Heart", "type": "Heart"}])], [], "type"),
        ([("A", GOOD_A, ["Heart"])], [("Old", OLD_A.upper(), ["Heart"])], "canonical"),
        ([("A", GOOD_A, ["Heart"])], [("Old", GOOD_A, ["Heart"])], "retired"),
        ([("A", GOOD_A, ["Heart"])], [("Old", OLD_A, ["NoSuchType"])], "NoSuchType"),
        ([("A", GOOD_A, ["Heart"])], [("Old", OLD_A, ["Fish"])], "Fish.*target"),
        (
            [("A", GOOD_A, ["Heart"])],
            [("Old", OLD_A, ["Heart"]), ("Old2", OLD_A, ["Heart"])],
            "twice",
        ),
        (
            [("A", GOOD_A, ["Heart"])],
            [("Old", OLD_A, [{"type": "Cross", "vanilla": '{ icon = "Nope", variant = 9 }'}])],
            "Nope",
        ),
        (
            [("A", GOOD_A, ["Heart"])],
            [("Old", OLD_A, [{"type": "Cross", "vanilla": '{ icon = "Q", variant = 10 }'}])],
            "0-9",
        ),
    ],
    ids=[
        "duplicate-name",
        "duplicate-address",
        "uppercase-address",
        "malformed-address",
        "descending-addresses",
        "address-from-8",
        "no-variant",
        "duplicate-variant",
        "unknown-variant-field",
        "uppercase-retired-address",
        "retired-address-reused",
        "unknown-retired-type",
        "retired-without-target",
        "duplicate-retired-address",
        "unknown-vanilla-block",
        "vanilla-variant-out-of-range",
    ],
)
def test_load_table_rejects(tmp_path, icons, retired, message):
    """Every table defect is a ValueError naming it, before anything is rendered."""
    with pytest.raises(ValueError, match=message):
        gi.load_table(write_table(tmp_path, icons, retired, vanilla={"Q": QUESTION}))


def test_vanilla_address_must_not_be_a_mod_address(tmp_path):
    """A [vanilla] entry pointing at one of the mod's own addresses is rejected."""
    path = write_table(tmp_path, [("A", GOOD_A, ["Heart"])], vanilla={"Q": GOOD_A})
    with pytest.raises(ValueError, match="vanilla"):
        gi.load_table(path)


@pytest.mark.parametrize(
    "address",
    [QUESTION.upper(), "not-a-uuid", QUESTION.replace("-", ""), "{" + QUESTION + "}", 7],
    ids=["uppercase", "malformed", "unhyphenated", "braced", "integer"],
)
def test_vanilla_address_must_be_canonical(tmp_path, address):
    """A [vanilla] address is held to the same lowercase canonical form as a mod address."""
    path = write_table(tmp_path, [("A", GOOD_A, ["Heart"])], vanilla={"Q": address})
    with pytest.raises(ValueError, match="canonical"):
        gi.load_table(path)


@pytest.mark.parametrize(
    "raw",
    [
        '{ icon = "Q" }',
        "{ variant = 9 }",
        '"Q"',
        '{ icon = "Q", variant = "9" }',
        '{ icon = "Q", variant = true }',
        '{ icon = "Q", variant = 9.0 }',
        "{ icon = 1, variant = 9 }",
        '{ icon = "Q", variant = 9, note = "x" }',
    ],
    ids=[
        "missing-variant",
        "missing-icon",
        "string",
        "string-variant",
        "bool-variant",
        "float-variant",
        "integer-icon",
        "extra-key",
    ],
)
def test_malformed_vanilla_target_is_a_value_error(tmp_path, raw, monkeypatch, capsys):
    """A malformed `vanilla = {...}` is a ValueError, so main exits 2 rather than 1 (drift)."""
    path = write_table(
        tmp_path,
        [("A", GOOD_A, ["Heart"])],
        [("Old", OLD_A, [{"type": "QuestionMark", "vanilla": raw}])],
        vanilla={"Q": QUESTION},
    )
    with pytest.raises(ValueError, match="vanilla"):
        gi.load_table(path)
    monkeypatch.setattr(gi, "TABLE", path)
    assert gi.main(["--check"]) == 2
    assert "error:" in capsys.readouterr().err


def test_vanilla_table_must_be_a_table(tmp_path):
    """A top-level `vanilla = ...` that is not a table is a ValueError."""
    path = tmp_path / "icons.toml"
    path.write_text(
        f'vanilla = "x"\n\n[[icon]]\nname = "A"\naddress = "{GOOD_A}"\n\n'
        '[[icon.variant]]\nname = "Heart"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=r"\[vanilla\]"):
        gi.load_table(path)


def test_load_vanilla_reads_the_table(tmp_path):
    """load_vanilla returns the [vanilla] table, and {} when there is none."""
    with_table = write_table(tmp_path, [("A", GOOD_A, ["Heart"])], vanilla={"Q": QUESTION})
    assert gi.load_vanilla(with_table) == {"Q": QUESTION}
    assert gi.load_vanilla(write_table(tmp_path, [("A", GOOD_A, ["Heart"])])) == {}


# --- orphans ----------------------------------------------------------------------


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
