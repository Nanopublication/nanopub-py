import pytest

from nanopub.trustyuri.rdf.RdfUtils import get_format, get_str, normalize, get_suffix


class TestGetFormat:

    @pytest.mark.parametrize("filename,expected", [
        ("graph.xml", "trix"),
        ("data.ttl", "turtle"),
        ("dataset.nq", "nquads"),
        ("triples.nt", "nt"),
        ("ontology.rdf", "xml"),
    ])
    def test_known_extensions(self, filename, expected):
        assert get_format(filename) == expected

    @pytest.mark.parametrize("filename", [
        "file.json",
        "archive.zip",
        "README",
        "",
    ])
    def test_unknown_or_missing_extension_returns_none(self, filename):
        assert get_format(filename) is None


class TestGetStr:

    def test_returns_bytes(self):
        assert isinstance(get_str("hello"), bytes)

    def test_ascii_string(self):
        assert get_str("hello") == b"hello"

    def test_empty_string(self):
        assert get_str("") == b""

    def test_whitespace_string(self):
        assert get_str("   ") == b"   "

    # --- unicode / multibyte -------------------------------------------------

    def test_unicode_latin(self):
        assert get_str("café") == "café".encode("utf-8")

    def test_unicode_chinese(self):
        assert get_str("你好") == "你好".encode("utf-8")

    def test_unicode_emoji(self):
        assert get_str("🚀") == "🚀".encode("utf-8")

    def test_unicode_arabic(self):
        assert get_str("مرحبا") == "مرحبا".encode("utf-8")

    # --- special characters --------------------------------------------------

    def test_newline(self):
        assert get_str("line1\nline2") == b"line1\nline2"

    def test_tab(self):
        assert get_str("col1\tcol2") == b"col1\tcol2"

    def test_null_character(self):
        assert get_str("\x00") == b"\x00"

    # --- round-trip ----------------------------------------------------------

    def test_roundtrip_decode(self):
        original = "Hello, 世界!"
        assert get_str(original).decode("utf-8") == original

    # --- encoding is utf-8, not latin-1 -------------------------------------

    def test_encoding_is_utf8_not_latin1(self):
        # 'é' is 0xC3 0xA9 in UTF-8, but 0xE9 in latin-1
        result = get_str("é")
        assert result == b"\xc3\xa9"
        assert result != b"\xe9"


class TestNormalize:

    def test_none_hashstr_returns_bytes(self):
        result = normalize("http://example.org/foo", None)
        assert result == b"http://example.org/foo"

    def test_none_hashstr_empty_uri(self):
        assert normalize("", None) == b""

    def test_str_hashstr_replaces_match(self):
        assert normalize("http://example.org/foo#bar", "#bar") == "http://example.org/foo "

    def test_str_hashstr_no_match_leaves_uri_unchanged(self):
        assert normalize("http://example.org/foo", "#bar") == "http://example.org/foo"

    def test_empty_uri_with_str_hashstr(self):
        assert normalize("", "#") == ""


class TestGetSuffix:

    def test_identical_uris_return_none(self):
        assert get_suffix("http://example.org/foo", "http://example.org/foo") is None

    def test_identical_empty_strings_return_none(self):
        assert get_suffix("", "") is None

    def test_returns_suffix_when_plain_uri_starts_with_base_uri(self):
        assert get_suffix("http://example.org/foo#bar", "http://example.org/foo") == "#bar"

    def test_returns_suffix_for_path_segment(self):
        assert get_suffix("http://example.org/foo/bar", "http://example.org/foo/") == "bar"

    def test_empty_base_uri_returns_full_plain_uri_as_suffix(self):
        assert get_suffix("http://example.org/foo", "") == "http://example.org/foo"

    def test_no_common_prefix_returns_none(self):
        assert get_suffix("http://example.org/foo", "http://other.org/") is None

    def test_partial_prefix_mismatch_returns_none(self):
        assert get_suffix("http://example.org/foo", "http://example.org/bar") is None

    def test_base_uri_longer_than_plain_uri_returns_none(self):
        assert get_suffix("http://example.org/", "http://example.org/foo/bar") is None

    def test_reversed_order_returns_none(self):
        assert get_suffix("http://example.org/foo", "http://example.org/foo#bar") is None
