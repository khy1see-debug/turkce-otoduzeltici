import sys

import pytest

from src import dictionary
from src.cli import main


@pytest.fixture
def isolated_personal_dictionary(tmp_path, monkeypatch):
    original_words = set(dictionary.PERSONAL_WORDS)
    original_path = dictionary.PERSONAL_DICT_PATH
    original_signature = dictionary._PERSONAL_DICT_SIGNATURE
    config_path = tmp_path / "config" / "turkce-otoduzeltici" / "kisisel_sozluk.txt"
    legacy_path = tmp_path / "legacy" / "kisisel_sozluk.txt"
    monkeypatch.setattr(dictionary, "CONFIG_PERSONAL_DICT_PATH", str(config_path))
    monkeypatch.setattr(dictionary, "LEGACY_PERSONAL_DICT_PATH", str(legacy_path))
    dictionary.refresh_personal_dictionary(force=True)
    try:
        yield config_path
    finally:
        dictionary.PERSONAL_WORDS.clear()
        dictionary.PERSONAL_WORDS.update(original_words)
        dictionary.PERSONAL_DICT_PATH = original_path
        dictionary._PERSONAL_DICT_SIGNATURE = original_signature
        dictionary.get_word_prob.cache_clear()


def test_personal_words_can_be_added_removed_and_listed(isolated_personal_dictionary):
    word = "kişiselkodexqz"
    assert dictionary.add_personal_word("KİŞİSELKODEXQZ")
    assert not dictionary.add_personal_word(word)
    assert dictionary.is_valid_word(word)
    assert dictionary.list_personal_words() == [word]
    assert dictionary.remove_personal_word(word)
    assert not dictionary.is_valid_word(word)
    assert not dictionary.remove_personal_word(word)


def test_running_correction_reloads_edited_dictionary(isolated_personal_dictionary):
    from src.grammar import fix_sentence

    word = "çalışmazamakozq"
    isolated_personal_dictionary.parent.mkdir(parents=True)
    isolated_personal_dictionary.write_text(word + "\n", encoding="utf-8")
    assert fix_sentence(word)
    assert dictionary.is_valid_word(word)

    isolated_personal_dictionary.write_text("başkaözelkelimeqz\n", encoding="utf-8")
    assert fix_sentence("Merhaba") == "Merhaba."
    assert not dictionary.is_valid_word(word)


def test_running_correction_clears_spelling_cache_on_dictionary_reload(
    isolated_personal_dictionary,
):
    from src.grammar import fix_sentence
    from src.speller import correct_word

    custom_word = "codexpersonalwordqz"
    misspelling = "codexpersonalwordqx"
    assert dictionary.add_personal_word(custom_word)
    assert correct_word(misspelling) == custom_word

    # Simulate a separate CLI process changing the file used by the service.
    isolated_personal_dictionary.write_text("", encoding="utf-8")
    assert fix_sentence("Merhaba") == "Merhaba."
    assert correct_word(misspelling) == misspelling


def test_cli_exposes_personal_dictionary_commands(
    isolated_personal_dictionary, monkeypatch, capsys
):
    word = "oyunmekaniqz"
    monkeypatch.setattr(sys, "argv", ["turkce-duzelt", "--add-word", word])
    assert main() == 0
    assert "eklendi" in capsys.readouterr().out

    monkeypatch.setattr(sys, "argv", ["turkce-duzelt", "--list-words"])
    assert main() == 0
    assert word in capsys.readouterr().out

    monkeypatch.setattr(sys, "argv", ["turkce-duzelt", "--remove-word", word])
    assert main() == 0
    assert "kaldırıldı" in capsys.readouterr().out


def test_personal_word_rejects_spaces(isolated_personal_dictionary):
    with pytest.raises(ValueError):
        dictionary.add_personal_word("iki kelime")
