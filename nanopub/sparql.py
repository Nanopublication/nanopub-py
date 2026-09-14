"""Syntax checking for the SPARQL carried by grlc query nanopublications.

A nanopublication cannot be edited after the fact, so a query whose SPARQL is broken is
broken permanently: it can never run, and the only remedy is publishing a corrected
version. These checks run before a nanopublication carrying such a query is signed or
published.

The queries end up being run by grlc against RDF4J, so what this has to match is what
RDF4J's parser accepts. rdflib's parser stands in for it: it is already a dependency,
``prepareQuery`` parses without executing anything, and measured against the grlc queries
published so far it refuses the same ones, in the same place.

What the parser decides is left to the parser. The scan below only comes in afterwards,
to say which character a failed parse tripped over, since rdflib reports the position it
backtracked to rather than the offending character in some cases.
"""
import logging
import re
import unicodedata
from functools import lru_cache
from typing import Optional, Tuple

from pyparsing import ParseBaseException
from rdflib.plugins.sparql import prepareQuery

logger = logging.getLogger(__name__)

CHARACTER_ADVICE = (
    "Characters like this one tend to slip in when a query is copied from a word "
    "processor or a web page, and replacing them with their plain equivalents makes "
    "the query valid again."
)

#: The only whitespace the SPARQL grammar allows: WS ::= #x20 | #x9 | #xD | #xA
_SPARQL_WHITESPACE = " \t\n\r"

#: The non-ASCII characters SPARQL allows outside literals, comments and IRIs:
#: PN_CHARS_BASE plus the two ranges and one character PN_CHARS adds.
_SPARQL_NAME_CHARS = re.compile(
    "[\u00B7\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0300-\u036F"
    "\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u203F-\u2040"
    "\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF"
    "\uFDF0-\uFFFD\U00010000-\U000EFFFF]"
)

#: IRIREF ::= '<' ([^<>"{}|^`\]-[#x00-#x20])* '>'
_IRI_FORBIDDEN = '<>"{}|^`\\'


def _iri_length(sparql: str, start: int) -> int:
    """The length of the IRI starting at ``start``, or 0 where that '<' is an operator."""
    for index in range(start + 1, len(sparql)):
        character = sparql[index]
        if character == ">":
            return index - start + 1
        if character in _IRI_FORBIDDEN or character <= " ":
            return 0
    return 0


def _find_disallowed_character(sparql: str) -> Optional[Tuple[str, int, int]]:
    """Find the first character the SPARQL grammar does not allow where it stands.

    Only code positions are examined: comments, string literals and IRIs may hold any
    character, and published queries do. What is left is a character that is either
    outside SPARQL's name characters or a whitespace character other than the four the
    grammar allows -- a no-break space, say, which reads as an ordinary space to whoever
    wrote the query but stops the parser on the way to grlc.

    :return: the character with its line and column, or None if there is none
    """
    index, line, column = 0, 1, 1

    def skip(count: int) -> None:
        nonlocal index, line, column
        for _ in range(count):
            if index >= len(sparql):
                return
            if sparql[index] == "\n":
                line += 1
                column = 1
            else:
                column += 1
            index += 1

    while index < len(sparql):
        character = sparql[index]

        # Comment: runs to the end of the line.
        if character == "#":
            end = sparql.find("\n", index)
            skip((len(sparql) if end == -1 else end) - index)
            continue

        # Long string literal: runs to the matching triple quote.
        triple = sparql[index : index + 3]
        if triple in ("'''", '"""'):
            end = index + 3
            while end < len(sparql) and sparql[end : end + 3] != triple:
                end += 2 if sparql[end] == "\\" else 1
            skip(min(end + 3, len(sparql)) - index)
            continue

        # Short string literal: runs to the matching quote, at most to the line end.
        if character in ("'", '"'):
            end = index + 1
            while end < len(sparql) and sparql[end] not in (character, "\n"):
                end += 2 if sparql[end] == "\\" else 1
            skip(min(end + 1, len(sparql)) - index)
            continue

        # IRI, if this '<' opens one rather than being a comparison operator.
        if character == "<":
            length = _iri_length(sparql, index)
            if length:
                skip(length)
                continue

        disallowed_whitespace = (
            character.isspace() and character not in _SPARQL_WHITESPACE
        )
        disallowed_name = not character.isascii() and not _SPARQL_NAME_CHARS.match(
            character
        )
        if disallowed_whitespace or disallowed_name:
            return character, line, column

        skip(1)

    return None


def _name_character(character: str) -> str:
    """Name a character by code point, and by Unicode name where it has one."""
    code = f"U+{ord(character):04X}"
    try:
        return f"{code} ({unicodedata.name(character)})"
    except ValueError:
        # Control characters and a few others have no name; the code point is enough
        # to find and replace them.
        return code


def _describe_character(character: str, line: int, column: int) -> str:
    return (
        f"This is not valid SPARQL. The character at line {line}, column {column} is "
        f"{_name_character(character)}, which SPARQL doesn't allow there. "
        f"{CHARACTER_ADVICE}"
    )


def _describe_parse_error(sparql: str, error: ParseBaseException) -> str:
    """Describe where the parser stopped, naming the character where that helps.

    A query is more often broken by a character picked up on the way through a word
    processor or a web page than by a hand-written syntax error, and such a character
    reads as the plain one it replaced, so the author has no way of spotting it by eye.
    An ASCII character is left to the parser's own report, which already shows it.
    """
    at_parser_position = error.line[error.col - 1 : error.col]
    if at_parser_position and not at_parser_position.isascii():
        return _describe_character(at_parser_position, error.lineno, error.col)

    # rdflib backtracks to the start of the construct it was reading, so the position it
    # reports is not always the offending character; where it is not, look for one.
    disallowed = _find_disallowed_character(sparql)
    if disallowed:
        return _describe_character(*disallowed)

    # The parser lists everything it would have accepted instead, which runs long and
    # does not survive being quoted in an error message.
    expected = " ".join(str(error.msg).split())
    if len(expected) > 120:
        expected = f"{expected[:117]}..."
    return (
        "This is not valid SPARQL. The SPARQL parser reports: "
        f"{expected} at line {error.lineno}, column {error.col}."
    )


@lru_cache(maxsize=32)
def sparql_syntax_error(sparql: Optional[str]) -> Optional[str]:
    """Describe what keeps a string from being a SPARQL query that grlc can run.

    Results are cached: parsing a query of the size these grlc nanopubs carry takes
    rdflib a few hundred milliseconds, and signing one asks the same question of the
    same query more than once, by way of ``is_valid``.

    :param sparql: the query to check
    :return: a description of the problem, in terms the author of the query can act on,
        or None if the query is fine (or absent)
    """
    if sparql is None:
        return None

    try:
        prepareQuery(sparql)
    except ParseBaseException as error:
        return _describe_parse_error(sparql, error)
    except Exception as error:  # noqa: BLE001 - rdflib raises bare exceptions here
        message = str(error).strip()
        if message.startswith("Unknown namespace prefix"):
            return f"This is not valid SPARQL. The SPARQL parser reports: {message}."
        # What is left are the restrictions rdflib applies while building the algebra,
        # which RDF4J does not, so whether they are worth refusing is for the endpoint
        # that runs the query to say, not for the signing step.
        logger.debug("Ignoring non-syntax complaint about a grlc query: %s", error)
        return None

    return None


def is_valid_sparql(sparql: Optional[str]) -> bool:
    """Report whether a string is a SPARQL query that grlc can run.

    :param sparql: the query to check; a missing query counts as valid, since that is
        the absence of a query rather than a broken one
    """
    return sparql_syntax_error(sparql) is None
