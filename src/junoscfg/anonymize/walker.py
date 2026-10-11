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
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from junoscfg.anonymize.path_filter import PathFilter

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
    from junoscfg.display import load_schema_tree

    schema = load_schema_tree()
    if not schema:
        return ()

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
    walker.node(ir if cfg is None else cfg, schema_root, [])
    return tuple(walker.unplaced)


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
            if key.startswith("@") or key == skip:
                continue
            if key == UNPLACED_STATEMENTS:
                self._record(value, path)
                continue
            child = schema_child(schema_node, key, self.root)
            if child is not None:
                self._child(obj, key, value, child, path)
            elif self._is_key_field(key, schema_node):
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
        if not self.path_filter.matches(path):
            return
        items = value if isinstance(value, list) else [value]
        replaced = []
        for item in items:
            if isinstance(item, dict | list):
                # A shape a leaf does not take: no rule reads it as a value.
                replaced.append(self.unknown_value(item, path))
            elif item is None or item is True:
                replaced.append(item)
            else:
                replaced.append(self._try_rules(item, schema_node, path))
        parent[key] = replaced if isinstance(value, list) else replaced[0]

    def _try_rules(self, value: Any, schema_node: dict[str, Any], path: list[str]) -> Any:
        """Apply the first matching rule to *value* and return the result.

        A value from the leaf's own enum -- `as-list-group` for `list-type`,
        `bgp` for `from protocol` -- is configuration syntax, not data: a
        matching rule leaves it as it is. Replaced, it is a value the device
        rejects.
        """
        str_value = str(value)
        for index, rule in enumerate(self.rules):
            if rule.matches(str_value, schema_node, path):
                if str_value in _leaf_enum(schema_node):
                    return value
                result = rule.transform(str_value)
                self._debug(rule, path, str_value, result)
                if rule.keeps_text:
                    # The text around what it replaced may hold another shape.
                    result = self._chain(result, self.rules[index + 1 :], path)
                return result
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
        return self._chain(word, self.rules, path)

    def _chain(self, word: str, rules: Sequence[Rule], path: list[str]) -> str:
        """*word* through each rule that knows a shape in it, in turn.

        A rule that keeps the text around its replacement (an address) lets the
        next rule look at the rest (`acme-203.0.114.9`); one that replaces the
        whole word (a password hash) ends the chain.
        """
        for rule in rules:
            replaced = rule.lexical(word)
            if replaced is not None and replaced != word:
                self._debug(rule, path, word, replaced)
                word = replaced
                if not rule.keeps_text:
                    break
        return word

    def _debug(self, rule: Rule, path: list[str], before: str, after: str) -> None:
        if self.log_debug and self.sink is not None:
            self.sink(f"[{rule.name}] {'.'.join(path)}: {before!r} -> {after!r}")


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
