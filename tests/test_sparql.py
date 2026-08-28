"""The SPARQL syntax check that keeps a broken grlc query from being published."""
from nanopub.sparql import is_valid_sparql, sparql_syntax_error

VALID = "select ?np where { ?np ?p ?o }"

#: A published grlc query, shortened: placeholders and a magic property.
REAL_GRLC_QUERY = """prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix npa: <http://purl.org/nanopub/admin/>
prefix search: <http://www.openrdf.org/contrib/lucenesail#>

select ?np ?label where {
  graph npa:graph {
    ?np npa:hasValidSignatureForPublicKey ?__pubkey .
    optional { ?np rdfs:label ?label . }
  }
  ?np search:matches [ search:query ?_query ; search:property rdfs:label ] .
}
limit 100"""


class TestAcceptedQueries:
    def test_accepts_a_valid_query(self):
        assert sparql_syntax_error(VALID) is None
        assert is_valid_sparql(VALID)

    def test_accepts_a_published_grlc_query_with_placeholders(self):
        assert sparql_syntax_error(REAL_GRLC_QUERY) is None

    def test_accepts_a_values_block(self):
        query = (
            'select ?a ?b where { values (?a ?b) { (<http://1> "x") (<http://2> UNDEF) }'
            " ?a ?p ?b }"
        )
        assert sparql_syntax_error(query) is None

    def test_treats_a_missing_query_as_valid(self):
        assert sparql_syntax_error(None) is None
        assert is_valid_sparql(None)

    def test_accepts_the_characters_sparql_allows_where_they_stand(self):
        """Comments, string literals and IRIs may hold any character, and do."""
        query = (
            "# a comment with a\u00a0no-break space\n"
            "select ?x where {\n"
            '  ?x <http://example.org/a\u00a0b> "quoted “hello”, a\u00a0space" .\n'
            "}"
        )
        assert sparql_syntax_error(query) is None

    def test_accepts_a_non_ascii_letter_in_a_prefixed_name(self):
        query = "prefix ex: <http://example.org/>\nselect ?x where { ?x ex:café ?o }"
        assert sparql_syntax_error(query) is None


class TestRejectedQueries:
    def test_rejects_an_empty_query(self):
        error = sparql_syntax_error("")
        assert error is not None
        assert error.startswith("This is not valid SPARQL")
        assert not is_valid_sparql("")

    def test_rejects_a_hand_written_syntax_error(self):
        error = sparql_syntax_error("select ?x where { ?x ?p }")
        assert "This is not valid SPARQL." in error
        assert "The SPARQL parser reports:" in error

    def test_rejects_a_sparql_update(self):
        error = sparql_syntax_error("insert data { <http://a> <http://b> <http://c> }")
        assert error is not None

    def test_rejects_an_undeclared_prefix(self):
        error = sparql_syntax_error("select ?x where { ?x foo:bar ?o }")
        assert "Unknown namespace prefix" in error


class TestNamedCharacters:
    """The characters this check mainly exists for read as their plain counterparts, so
    naming them is the whole fix."""

    def test_names_a_no_break_space(self):
        error = sparql_syntax_error("select ?x\nwhere {\u00a0?x ?p ?o }")

        assert "U+00A0 (NO-BREAK SPACE)" in error
        assert "line 2, column 8" in error
        assert "word processor" in error

    def test_names_a_typographic_quotation_mark(self):
        """rdflib backtracks to the start of the triples block here, so the position it
        reports is not the offending character and the scan has to find it."""
        error = sparql_syntax_error("select ?x where { ?x ?p “hello” }")

        assert "U+201C (LEFT DOUBLE QUOTATION MARK)" in error
        assert "line 1, column 25" in error

    def test_names_a_zero_width_space(self):
        error = sparql_syntax_error("select ?x\u200b where { ?x ?p ?o }")

        assert "U+200B (ZERO WIDTH SPACE)" in error
        assert "line 1, column 10" in error

    def test_counts_the_position_past_a_multi_line_literal(self):
        query = (
            "select ?x where {\n"
            '  ?x ?p """first\n'
            "second\n"
            'third""" .\n'
            "  ?x ?q \u00a0?z .\n"
            "}"
        )
        error = sparql_syntax_error(query)

        assert "line 5, column 9" in error

    def test_leaves_an_ascii_character_to_the_parser(self):
        error = sparql_syntax_error("select ?x where { ?x ?p ?o } }")

        assert "The SPARQL parser reports:" in error
        assert "U+" not in error
