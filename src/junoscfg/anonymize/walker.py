"""Schema-guided tree walker for anonymization.

Walks the dict IR and the structure tree in parallel and offers every value
the tree places to the rules. A key the tree resolves through
`junoscfg.display.schema_child` -- a universal statement below the root
included -- is walked against its node; a transparent container's other
children against the container, its transparent child's entries against the
child; each entry of a list a container holds against the container.

What the walk cannot place -- a key the tree does not name, a value of a shape
its node does not take, a statement kept whole in the record
`junoscfg.display.UNPLACED_STATEMENTS` -- is rewritten word by word by the
rules that recognise a word by its shape alone (`Rule.lexical`: an address, a
password hash, a sensitive word), never by a keyword, and its place is
returned by its schema path (owner answer 5; spec anonymization/placed-values).

An entry's name in angle brackets inside a group (`<*>`, `<ge-*>`) is a
pattern that selects names (Junos OS "Configuration Groups"), not a name. A
pattern of `*` alone selects every name and passes every rule. Any other keeps
its brackets, and its text goes to the rules as a name of that place, or to a
rule that knows patterns of its values (`Rule.wildcard`). One whose rewritten
form selects other names among those the configuration holds at its place,
inside and outside groups, or whose text a rule could not rewrite as a
pattern, is returned by its schema path (ANON-P3; specification challenges
S1-S3).

A value no rule takes whole is free text, as an annotation (`"@"`, `"@<key>"`)
is: one chain rewrites each part of it a rule recognises by its shape (an
address, a URL's user or password, a password hash, a sensitive word, an AS
number), rule by rule, and never offers text one rule wrote to another
(`Rule.spans`; spec anonymization/embedded-values). An `apply-path` is read
against the tree: its names go to the rules as the values they name.
"""

from __future__ import annotations

import re
from fnmatch import fnmatchcase
from typing import TYPE_CHECKING, Any

from junoscfg.anonymize.path_filter import PathFilter
from junoscfg.anonymize.rules import has_wildcard_characters, rewrite, wildcard_text

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from junoscfg.anonymize.config import AnonymizeConfig
    from junoscfg.anonymize.rules import Rule

#: A word of text the walk cannot place: anything between whitespace and quotes.
_WORD = re.compile(r'[^\s"]+')


def walk(
    ir: dict[str, Any],
    rules: list[Rule],
    config: AnonymizeConfig,
    *,
    diagnostic_sink: Callable[[str], None] | None = None,
) -> tuple[str, ...]:
    """Walk the IR in place, applying anonymization rules to every placed value.

    Args:
        ir: The full IR dict (mutated in-place).
        rules: Ordered list of active rules.
        config: Anonymization config (for include/exclude filters, log level).
        diagnostic_sink: Optional receiver for debug diagnostics.

    Returns:
        The schema path (dot-joined schema names, ``""`` for the top level) of
        each piece of content the walk could not place, once per piece, in
        tree order. No path holds an unplaced key, an entry name or a value.
    """
    return walk_with_patterns(ir, rules, config, diagnostic_sink=diagnostic_sink)[0]


def walk_with_patterns(
    ir: dict[str, Any],
    rules: list[Rule],
    config: AnonymizeConfig,
    *,
    diagnostic_sink: Callable[[str], None] | None = None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """`walk`, and the schema path of each wildcard name that selects other names
    than it did, or that a rule could not rewrite as a pattern: the entry's path
    (an `apply-path`'s own), once per wildcard or affected apply-path selector
    component, in tree order. Literal apply-path selectors are checked by
    equality, including excluded selectors whose text stays unchanged.
    """
    from junoscfg.display import load_schema_tree

    schema = load_schema_tree()
    if not schema:
        return (), ()

    walker = _Walker(
        schema,
        rules,
        PathFilter(config.include, config.exclude),
        config.log_level == "debug",
        diagnostic_sink,
    )
    # Navigate to configuration node in schema
    schema_root = schema.get("c", {}).get("configuration", schema)
    # The IR is {"configuration": {...}}; an unwrapped IR is walked as its content.
    cfg = ir.get("configuration")
    walker.schema_root = schema_root
    walker.node(ir if cfg is None else cfg, schema_root, [])
    return tuple(walker.unplaced), walker.patterns()


class _Walker:
    """One walk: the tree, the rules, and what the walk could not place."""

    def __init__(
        self,
        root: dict[str, Any],
        rules: list[Rule],
        path_filter: PathFilter,
        log_debug: bool,
        diagnostic_sink: Callable[[str], None] | None,
    ) -> None:
        self.root = root
        self.rules = rules
        self.path_filter = path_filter
        self.log_debug = log_debug
        self.sink = diagnostic_sink
        self.unplaced: list[str] = []
        self.schema_root: dict[str, Any] = root
        #: Each entry name the rules saw: its place, as written, and its entry
        #: and key, where the final value is read.
        self.names: list[tuple[tuple[str, ...], str, dict[str, Any], str]] = []
        #: Each wildcard name: its place, the path reported, its text as
        #: written, as rewritten, whether the rule that rewrote it vouches,
        #: and whether selection uses wildcard matching or literal equality.
        self.wildcards: list[tuple[tuple[str, ...], str, str, str, bool, bool]] = []

    # -- placed content ------------------------------------------------------

    def node(
        self, obj: Any, schema_node: dict[str, Any], path: list[str], skip: str | None = None
    ) -> None:
        """Walk *obj*, which the tree places at *schema_node*, past the key *skip*."""
        if isinstance(obj, list):
            for item in obj:
                self.node(item, schema_node, path)
            return
        if not isinstance(obj, dict):
            return
        from junoscfg.display import UNPLACED_STATEMENTS, schema_child

        renamed: dict[str, str] = {}
        for key, value in list(obj.items()):
            if key.startswith("@"):
                self._annotation(obj, key, path)
                continue
            if key == skip:
                continue
            if key == UNPLACED_STATEMENTS:
                self._record(value, path)
                continue
            child = schema_child(schema_node, key, self.root)
            name = (child is None or bool(child.get("l"))) and self._is_key_field(key, schema_node)
            if name and wildcard_text(value) is not None:
                self._wildcard(obj, key, child or {}, [*path, key])
            elif child is not None:
                self._child(obj, key, value, child, path)
                if name and isinstance(value, str):
                    self.names.append((_place([*path, key]), value, obj, key))
            elif name:
                # A key field the tree holds no leaf for (`apply-macro`'s
                # name): the rules see it with no type.
                self._leaf(obj, key, value, {}, [*path, key])
            elif not (value in (None, True, [None]) and self._is_switch_spelling(key, schema_node)):
                # A folded switch's spelling (`disable`) holds no value; any
                # other key the tree does not name is content it cannot place.
                new_key = self.unknown(obj, key, path)
                if new_key != key:
                    renamed[key] = new_key
        if renamed:
            # A tag on a renamed key (`@<key>`) follows it.
            for key in obj:
                if key.startswith("@") and key[1:] in renamed:
                    renamed[key] = "@" + renamed[key[1:]]
            _rename_keys(obj, renamed)

    def _child(
        self,
        obj: dict[str, Any],
        key: str,
        value: Any,
        child: dict[str, Any],
        path: list[str],
    ) -> None:
        """Walk the value of *key*, which the tree places at *child*."""
        here = [*path, key]
        transparent = child.get("t")
        if transparent and isinstance(value, dict | list):
            inner = child.get("c", {}).get(transparent)
            if isinstance(value, dict):
                if inner is not None and transparent in value:
                    self._items(value, transparent, value[transparent], inner, here)
                # Its other children are the container's own.
                self.node(value, child, here, skip=transparent if inner is not None else None)
            elif inner is not None:
                self._items(obj, key, value, inner, here)
            return
        if child.get("l"):
            self._leaf(obj, key, value, child, here)
            return
        self._items(obj, key, value, child, here)

    def _items(
        self, owner: dict[str, Any], key: str, value: Any, node: dict[str, Any], here: list[str]
    ) -> None:
        """Walk an entry, or each entry of a list, the tree places at *node*.

        A list under a container that is no list is walked entry by entry too
        (the port-mirroring `routing-instance` JSON holds as a list of one).
        A scalar where the tree has a container or a list is content the walk
        cannot place.
        """
        if value is None or value is True or value == [None]:
            return
        items = value if isinstance(value, list) else [value]
        for index, item in enumerate(items):
            if isinstance(item, dict):
                self.node(item, node, here)
            elif item is not None and item is not True:
                replaced = self.text(item, here)
                if isinstance(value, list):
                    value[index] = replaced
                else:
                    owner[key] = replaced

    def _leaf(
        self,
        parent: dict[str, Any],
        key: str,
        value: Any,
        schema_node: dict[str, Any],
        path: list[str],
    ) -> None:
        """Offer a leaf's value, or each value of a leaf-list, to the rules."""
        if value is None or value is True or value == "":
            return
        if not self.path_filter.matches(path) and path[-1] != "apply-path":
            return
        items = value if isinstance(value, list) else [value]
        replaced = []
        for item in items:
            if isinstance(item, dict | list):
                # A shape a leaf does not take: no rule reads it as a value.
                replaced.append(self.unknown_value(item, path))
            elif item is None or item is True:
                replaced.append(item)
            elif path[-1] == "apply-path" and isinstance(item, str):
                replaced.append(self._apply_path(item, path))
            else:
                replaced.append(self._try_rules(item, schema_node, path)[0])
        parent[key] = replaced if isinstance(value, list) else replaced[0]

    def _try_rules(
        self, value: Any, schema_node: dict[str, Any], path: list[str], *, pattern: bool = False
    ) -> tuple[Any, bool]:
        """Rewrite *value*, a placed value: the result, and whether it is vouched for.

        A value from the leaf's own enum -- `as-list-group` for `list-type`,
        `bgp` for `from protocol` -- is configuration syntax, not data, and
        stays: replaced, it is a value the device rejects. The first rule that
        replaces whole values and takes this one replaces it whole; any other
        value is free text, its shapes rewritten by the chain (`_chain`).

        The text of a wildcard name (*pattern*) goes first to a rule that
        knows patterns of its values (`Rule.wildcard`); a rule that takes text
        holding a wildcard character and leaves it as written does not vouch
        for it.
        """
        str_value = str(value)
        if pattern:
            for index, rule in enumerate(self.rules):
                answer = rule.wildcard(str_value, schema_node, path)
                if answer is not None:
                    result, vouched = answer
                    self._debug(rule, path, str_value, result)
                    return self._chain(result, path, self.rules[index + 1 :]), vouched
        enum = _leaf_enum(schema_node)
        for rule in self.rules:
            if not rule.keeps_text and rule.matches(str_value, schema_node, path):
                if str_value in enum:
                    return value, True
                result = rule.transform(str_value)
                self._debug(rule, path, str_value, result)
                vouched = result != str_value or not (pattern and has_wildcard_characters(result))
                return result, vouched
        if not isinstance(value, str) or str_value in enum:
            return value, True
        return self._chain(value, path, self.rules, whole=schema_node), True

    # -- wildcard names -------------------------------------------------------

    def _wildcard(
        self, obj: dict[str, Any], key: str, schema_node: dict[str, Any], path: list[str]
    ) -> None:
        """Rewrite the wildcard name of *key* at *path* as a pattern, and keep it for `patterns`."""
        text = str(wildcard_text(obj[key]))
        if not text.strip("*") or not self.path_filter.matches(path):
            return  # `*` alone selects every name and holds no value.
        rewritten, vouched = self._try_rules(text, schema_node, path, pattern=True)
        obj[key] = f"<{rewritten}>"
        self.wildcards.append(
            (_place(path), ".".join(path[:-1]), text, str(rewritten), vouched, True)
        )

    def patterns(self) -> tuple[str, ...]:
        """The path of each wildcard or apply-path selector whose selection
        changed, or whose rewrite was not vouched for, from the final values.

        The names are those the rules saw at the wildcard's place, in any
        group and outside them (`groups` left out of the place); a wildcard is
        no name. Junos's wildcard characters are read as `fnmatchcase` reads
        them.
        """
        names: dict[tuple[str, ...], list[tuple[str, str]]] = {}
        for place, before, entry, key in self.names:
            names.setdefault(place, []).append((before, str(entry[key])))
        report = []
        for place, path, before, after, vouched, pattern in self.wildcards:
            if not vouched or any(
                (fnmatchcase(old, before) != fnmatchcase(new, after))
                if pattern
                else (old == before) != (new == after)
                for old, new in names.get(place, ())
            ):
                report.append(path)
        return tuple(report)

    # -- apply-path ------------------------------------------------------------

    def _apply_path(self, text: str, path: list[str]) -> str:
        """*text*, an `apply-path`, with each name in it rewritten as the value it names.

        Read against the tree from the configuration root, through transparent
        containers: the word after a list's keyword is a value of that list's
        key field, even when it spells a keyword; any other word is a keyword
        and stays. A wildcard there is a wildcard name, reported by the
        `apply-path`'s path. Literal selectors use equality against the same
        final-name kernel. An excluded path is read only to record its
        unchanged selectors; its names are never rewritten. A path the tree
        cannot read to its end is content
        the walk cannot place (spec anonymization/embedded-values).
        """
        from junoscfg.display import entry_key_names, schema_child

        rewrite_names = self.path_filter.matches(path)
        words = text.split(" ")
        node = self.schema_root
        here: list[str] = []
        keys: list[str] = []
        out: list[str] = []
        found: list[tuple[tuple[str, ...], str, str, bool, bool]] = []
        for word in words:
            if not word:
                return str(self.unknown_value(text, path)) if rewrite_names else text
            if keys:
                field = keys.pop(0)
                where = [*here, field]
                field_node = node.get("c", {}).get(field, {})
                inside = wildcard_text(word)
                if inside is None:
                    rewritten = (
                        str(self._try_rules(word, field_node, where)[0]) if rewrite_names else word
                    )
                    out.append(rewritten)
                    found.append((_place(where), word, rewritten, True, False))
                elif not inside.strip("*"):
                    out.append(word)
                else:
                    rewritten, vouched = (
                        self._try_rules(inside, field_node, where, pattern=True)
                        if rewrite_names
                        else (inside, True)
                    )
                    out.append(f"<{rewritten}>")
                    found.append((_place(where), inside, str(rewritten), vouched, True))
                continue
            child = schema_child(node, word, self.root)
            if child is None:
                return str(self.unknown_value(text, path)) if rewrite_names else text
            out.append(word)
            here.append(word)
            transparent = child.get("t")
            inner = child.get("c", {}).get(transparent) if transparent else None
            if inner is not None and inner.get("L"):
                node, keys = inner, list(entry_key_names(inner))
            elif child.get("L"):
                node, keys = child, list(entry_key_names(child))
            elif child.get("l"):
                node, keys = {"c": {word: child}}, [word]
                here.pop()
            else:
                node = child
        reported = ".".join(path)
        self.wildcards.extend(
            (place, reported, before, after, vouched, pattern)
            for place, before, after, vouched, pattern in found
        )
        return " ".join(out)

    def _annotation(self, obj: dict[str, Any], key: str, path: list[str]) -> None:
        """Rewrite the text of an annotation (`"@"`, `"@<key>"`) as free text."""
        where = [*path, key[1:]] if len(key) > 1 else path
        if self.path_filter.matches(where):
            obj[key] = self._text_in(obj[key], where)

    def _text_in(self, value: Any, path: list[str]) -> Any:
        """*value* with every string in it rewritten as free text."""
        if isinstance(value, str):
            return self._chain(value, path, self.rules)
        if isinstance(value, list):
            return [self._text_in(item, path) for item in value]
        if isinstance(value, dict):
            return {k: self._text_in(v, path) for k, v in value.items()}
        return value

    def _is_key_field(self, key: str, schema_node: dict[str, Any]) -> bool:
        from junoscfg.display import entry_key_names

        return bool(schema_node.get("L")) and key in entry_key_names(schema_node)

    def _is_switch_spelling(self, key: str, schema_node: dict[str, Any]) -> bool:
        """Whether *key* spells a folded on/off switch (`disable` for `enable-disable`)."""
        from junoscfg.display import statement_name_spellings

        enums = self.root.get("_enums", [])
        for name, node in schema_node.get("c", {}).items():
            index = node.get("e")
            if not (node.get("nk") and node.get("l") and isinstance(index, int)):
                continue
            if index < len(enums) and key in statement_name_spellings(name, enums[index]):
                return True
        return False

    # -- content the walk cannot place ---------------------------------------

    def unknown(self, obj: dict[str, Any], key: str, path: list[str]) -> str:
        """Rewrite the key the tree does not name at *path* and its value; the new key."""
        if not self.path_filter.matches([*path, key]):
            return key
        self.unplaced.append(".".join(path))
        obj[key] = self._words_in(obj[key], path)
        return self._words(key, path)

    def unknown_value(self, value: Any, path: list[str]) -> Any:
        """Rewrite a value of a shape its node does not take, at *path*."""
        self.unplaced.append(".".join(path))
        return self._words_in(value, path)

    def text(self, value: Any, path: list[str]) -> Any:
        """Rewrite a scalar where the tree has a container or a list, at *path*."""
        if not self.path_filter.matches(path):
            return value
        return self.unknown_value(value, path)

    def _record(self, record: Any, path: list[str]) -> None:
        """Rewrite each statement a level keeps whole, and its meta commands."""
        if not isinstance(record, dict) or not self.path_filter.matches(path):
            return
        statements = [text for text in record if not str(text).startswith("@")]
        self.unplaced.extend([".".join(path)] * (len(statements) or len(record)))
        rewritten = {self._words(text, path): value for text, value in record.items()}
        record.clear()
        record.update(rewritten)

    def _words_in(self, value: Any, path: list[str]) -> Any:
        """*value* with every word of its keys and strings rewritten."""
        if isinstance(value, str):
            return self._words(value, path)
        if isinstance(value, list):
            return [self._words_in(item, path) for item in value]
        if isinstance(value, dict):
            return {self._words(k, path): self._words_in(v, path) for k, v in value.items()}
        return value

    def _words(self, text: str, path: list[str]) -> str:
        """*text* with each word a rule recognises by its shape alone replaced."""
        return _WORD.sub(lambda match: self._word(match.group(), path), text)

    def _word(self, word: str, path: list[str]) -> str:
        return self._chain(word, path, self.rules)

    def _chain(
        self,
        text: str,
        path: list[str],
        rules: Sequence[Rule],
        whole: dict[str, Any] | None = None,
    ) -> str:
        """*text* with each part a rule recognises by its shape replaced, rule by rule.

        Text one rule wrote is never offered to another (`acme-203.0.114.9`:
        the address, then the sensitive word in the rest; a sensitive pattern
        never reaches into the address's replacement). For a placed value
        (*whole* is its node), a part that is the whole value is replaced only
        where its rule takes the value (`matches`): an address alone where its
        type says syntax, an SNMP OID, stays.
        """
        written: list[tuple[int, int]] = []
        for rule in rules:
            spans = [
                (start, end)
                for start, end in rule.spans(text)
                if not any(start < stop and begin < end for begin, stop in written)
            ]
            if (
                whole is not None
                and spans == [(0, len(text))]
                and not rule.matches(text, whole, path)
            ):
                continue
            if not spans:
                continue
            before = text
            text, wrote = rewrite(rule, text, spans)
            self._debug(rule, path, before, text)
            written = [_shifted(span, spans, wrote) for span in written] + wrote
        return text

    def _debug(self, rule: Rule, path: list[str], before: str, after: str) -> None:
        if self.log_debug and self.sink is not None:
            self.sink(f"[{rule.name}] {'.'.join(path)}: {before!r} -> {after!r}")


def _shifted(
    span: tuple[int, int], replaced: list[tuple[int, int]], wrote: list[tuple[int, int]]
) -> tuple[int, int]:
    """Where *span*, untouched by a rewrite of *replaced* into *wrote*, stands after it."""
    shift = sum(
        (new_end - new_start) - (end - start)
        for (start, end), (new_start, new_end) in zip(replaced, wrote, strict=True)
        if end <= span[0]
    )
    return span[0] + shift, span[1] + shift


def _place(path: list[str]) -> tuple[str, ...]:
    """Where a name stands, the same inside a group and outside it."""
    return tuple(path[1:] if path[:1] == ["groups"] else path)


def _rename_keys(obj: dict[str, Any], renamed: dict[str, str]) -> None:
    """Rename keys of *obj* in place, keeping their order."""
    if not renamed:
        return
    items = [(renamed.get(key, key), value) for key, value in obj.items()]
    obj.clear()
    obj.update(items)


def _leaf_enum(schema_node: dict[str, Any]) -> Sequence[str]:
    """The values a leaf's own enum declares, from the tree's enum table."""
    from junoscfg.display import load_schema_tree

    index = schema_node.get("e")
    enums = (load_schema_tree() or {}).get("_enums", [])
    if not isinstance(index, int) or index >= len(enums):
        return ()
    return enums[index]
