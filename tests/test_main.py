import os
import pytest
from md_to_conf import expand_file_globs


class TestExpandFileGlobs:
    """Tests for the expand_file_globs() helper in __init__.py"""

    def test_single_concrete_path_returned_as_absolute(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("# Hello")
        result = expand_file_globs([str(md)])
        assert result == [str(md.resolve())]

    def test_glob_pattern_expands_to_matching_files(self, tmp_path):
        (tmp_path / "a.md").write_text("# A")
        (tmp_path / "b.md").write_text("# B")
        (tmp_path / "c.txt").write_text("not markdown")

        result = expand_file_globs([str(tmp_path / "*.md")])
        result_names = sorted(os.path.basename(p) for p in result)
        assert result_names == ["a.md", "b.md"]

    def test_glob_results_are_absolute_paths(self, tmp_path):
        (tmp_path / "x.md").write_text("# X")
        result = expand_file_globs([str(tmp_path / "*.md")])
        for path in result:
            assert os.path.isabs(path)

    def test_duplicate_paths_deduplicated(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("# Doc")
        result = expand_file_globs([str(md), str(md)])
        assert len(result) == 1

    def test_duplicate_from_overlapping_globs_deduplicated(self, tmp_path):
        (tmp_path / "a.md").write_text("# A")
        result = expand_file_globs(
            [str(tmp_path / "*.md"), str(tmp_path / "a.md")]
        )
        assert len(result) == 1

    def test_non_matching_glob_passed_through_as_literal(self, tmp_path):
        """A glob that matches nothing is kept as-is so validate_args can report it."""
        pattern = str(tmp_path / "no_match_*.md")
        result = expand_file_globs([pattern])
        assert len(result) == 1
        # The path is resolved to absolute even if it doesn't exist
        assert os.path.isabs(result[0])

    def test_multiple_explicit_files_preserved_in_order(self, tmp_path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        c = tmp_path / "c.md"
        for f in [a, b, c]:
            f.write_text("# " + f.stem)
        result = expand_file_globs([str(a), str(b), str(c)])
        assert [os.path.basename(p) for p in result] == ["a.md", "b.md", "c.md"]

    def test_recursive_glob_finds_nested_files(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "top.md").write_text("# Top")
        (sub / "nested.md").write_text("# Nested")
        result = expand_file_globs([str(tmp_path / "**/*.md")])
        basenames = sorted(os.path.basename(p) for p in result)
        assert "top.md" in basenames
        assert "nested.md" in basenames

    def test_empty_list_returns_empty_list(self):
        result = expand_file_globs([])
        assert result == []

    def test_mixed_existing_and_glob(self, tmp_path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("# A")
        b.write_text("# B")
        # Pass one concrete path and one glob that matches the other
        result = expand_file_globs([str(a), str(tmp_path / "b.md")])
        basenames = sorted(os.path.basename(p) for p in result)
        assert basenames == ["a.md", "b.md"]

    # ------------------------------------------------------------------ #
    # Exclusion via --exclude (exclude_patterns kwarg)                    #
    # ------------------------------------------------------------------ #

    def test_exclude_single_file_by_literal_path(self, tmp_path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        a.write_text("# A")
        b.write_text("# B")
        result = expand_file_globs(
            [str(tmp_path / "*.md")],
            exclude_patterns=[str(b)],
        )
        assert [os.path.basename(p) for p in result] == ["a.md"]

    def test_exclude_glob_pattern(self, tmp_path):
        (tmp_path / "guide.md").write_text("# Guide")
        (tmp_path / "draft_guide.md").write_text("# Draft")
        (tmp_path / "draft_notes.md").write_text("# Notes")
        result = expand_file_globs(
            [str(tmp_path / "*.md")],
            exclude_patterns=[str(tmp_path / "draft_*.md")],
        )
        assert [os.path.basename(p) for p in result] == ["guide.md"]

    def test_exclude_recursive_glob(self, tmp_path):
        pub = tmp_path / "published"
        draft = tmp_path / "draft"
        pub.mkdir()
        draft.mkdir()
        (pub / "page.md").write_text("# Page")
        (draft / "wip.md").write_text("# WIP")
        result = expand_file_globs(
            [str(tmp_path / "**/*.md")],
            exclude_patterns=[str(draft / "**")],
        )
        assert [os.path.basename(p) for p in result] == ["page.md"]

    def test_exclude_all_leaves_empty_list(self, tmp_path):
        (tmp_path / "a.md").write_text("# A")
        result = expand_file_globs(
            [str(tmp_path / "*.md")],
            exclude_patterns=[str(tmp_path / "*.md")],
        )
        assert result == []

    def test_exclude_non_matching_pattern_ignored(self, tmp_path):
        (tmp_path / "a.md").write_text("# A")
        result = expand_file_globs(
            [str(tmp_path / "*.md")],
            exclude_patterns=[str(tmp_path / "nonexistent_*.md")],
        )
        assert [os.path.basename(p) for p in result] == ["a.md"]

    def test_multiple_exclude_patterns(self, tmp_path):
        for name in ["a.md", "b.md", "c.md", "d.md"]:
            (tmp_path / name).write_text(f"# {name}")
        result = expand_file_globs(
            [str(tmp_path / "*.md")],
            exclude_patterns=[str(tmp_path / "a.md"), str(tmp_path / "c.md")],
        )
        assert sorted(os.path.basename(p) for p in result) == ["b.md", "d.md"]

    # ------------------------------------------------------------------ #
    # Exclusion via inline !pattern in the positional args list           #
    # ------------------------------------------------------------------ #

    def test_inline_exclude_prefix(self, tmp_path):
        (tmp_path / "a.md").write_text("# A")
        (tmp_path / "b.md").write_text("# B")
        result = expand_file_globs(
            [str(tmp_path / "*.md"), "!" + str(tmp_path / "b.md")]
        )
        assert [os.path.basename(p) for p in result] == ["a.md"]

    def test_inline_exclude_glob(self, tmp_path):
        (tmp_path / "guide.md").write_text("# Guide")
        (tmp_path / "draft_one.md").write_text("# Draft 1")
        (tmp_path / "draft_two.md").write_text("# Draft 2")
        result = expand_file_globs(
            [str(tmp_path / "*.md"), "!" + str(tmp_path / "draft_*.md")]
        )
        assert [os.path.basename(p) for p in result] == ["guide.md"]

    def test_inline_and_flag_exclusions_combined(self, tmp_path):
        for name in ["a.md", "b.md", "c.md"]:
            (tmp_path / name).write_text(f"# {name}")
        result = expand_file_globs(
            [str(tmp_path / "*.md"), "!" + str(tmp_path / "a.md")],
            exclude_patterns=[str(tmp_path / "b.md")],
        )
        assert [os.path.basename(p) for p in result] == ["c.md"]

    def test_exclude_none_default_unchanged(self, tmp_path):
        (tmp_path / "a.md").write_text("# A")
        result_no_arg = expand_file_globs([str(tmp_path / "*.md")])
        result_none = expand_file_globs([str(tmp_path / "*.md")], exclude_patterns=None)
        assert result_no_arg == result_none
