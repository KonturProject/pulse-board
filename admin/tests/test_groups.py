from npsr_admin.groups import GROUPS, match_group


def test_match_group_variants():
    assert match_group("КЦПК_НП_СР_Тверь_СР1_ГБ") == "СР1"
    assert match_group("АП_НП_СР_Москва_СР5_ГБ_УД") == "СР5"
    assert match_group("КЦПК_НП_СР_Тверь_СР9_ГБА") == "СР9"
    assert match_group("КЦПК_НП_СР_Тверь_Ученики") is None
    assert match_group("КЦПК_НП_СР_Тверь_СР4_Упр") is None
    assert match_group("КЦПК_НП_СР_Москва") is None
    assert match_group("АП_НП_СС_ННовгород_СС4_СГБ") is None


def test_groups_branches():
    assert set(GROUPS) == {"СР1", "СР2", "СР3", "СР5", "СР6", "СР9"}
    assert {g.branch for g in GROUPS.values()} == {"Тверь"}  # one filial; СР5 is in Тверь
