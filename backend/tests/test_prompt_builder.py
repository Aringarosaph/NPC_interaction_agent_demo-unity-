from __future__ import annotations

from app.data_loader import DataLoader
from app.prompt_builder import PromptBuilder


def test_yae_profile_conversation_guidance_reaches_system_prompt() -> None:
    profile = DataLoader().get_bundle("genshin_yae_miko").profile

    system_prompt = PromptBuilder()._system(profile)

    assert "【对话策略】" in system_prompt
    assert "不要句句都捉弄人" in system_prompt
    assert "不只说“有趣”" in system_prompt
    assert "默认可称玩家“小家伙”" in system_prompt


def test_profiles_without_conversation_guidance_keep_default_policy() -> None:
    profile = DataLoader().get_bundle("arknights_amiya").profile

    system_prompt = PromptBuilder()._system(profile)

    assert "没有额外规则，按核心性格回应" in system_prompt


def test_yae_performance_policy_discourages_repeated_soft_laugh() -> None:
    profile = DataLoader().get_bundle("genshin_yae_miko").profile

    system_prompt = PromptBuilder()._system(profile, ["idle", "soft_laugh", "nod"])

    assert "soft_laugh 是低频动作" in system_prompt
    assert "普通的从容、觉得有趣、机敏调侃都不构成轻笑" in system_prompt
    assert "idle -> soft_laugh -> nod" in system_prompt
