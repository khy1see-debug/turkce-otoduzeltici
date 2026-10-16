"""Tests for Windows hotkey parsing, AltGr safety and modifier handling."""
import sys
import pytest
from src.app_tray import _parse_hotkey_string, _release_and_mask_modifiers


def test_parse_hotkey_string():
    mods, vk = _parse_hotkey_string("alt+q")
    assert vk == ord("Q")
    assert bool(mods & 0x0001)  # MOD_ALT

    mods_w, vk_w = _parse_hotkey_string("alt+w")
    assert vk_w == ord("W")
    assert bool(mods_w & 0x0001)

    mods_e, vk_e = _parse_hotkey_string("alt+e")
    assert vk_e == ord("E")
    assert bool(mods_e & 0x0001)

    mods_ctrl, vk_ctrl = _parse_hotkey_string("ctrl+alt+k")
    assert vk_ctrl == ord("K")
    assert bool(mods_ctrl & 0x0002)  # MOD_CONTROL
    assert bool(mods_ctrl & 0x0001)  # MOD_ALT


def test_release_and_mask_modifiers_no_crash():
    # Should not raise exception
    _release_and_mask_modifiers(max_wait_sec=0.01)
