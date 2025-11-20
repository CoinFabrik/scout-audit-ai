"""Discover Rust source dependencies for files listed in .scout configs.

The analyzer parses each referenced file with Tree-sitter, follows `mod foo;`
and `use crate::foo::...` statements, and returns a breadth-first-expanded file
list respecting the user-provided depth limit.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Set, Tuple

from tree_sitter import Node, Parser
from tree_sitter_languages import get_language

logger = logging.getLogger(__name__)

_PARSER = Parser()
_PARSER.set_language(get_language("rust"))


@dataclass
class UseEntry:
    """Represents a fully-qualified use path plus glob metadata."""
    segments: List[str]
    is_glob: bool = False


def _node_text(node: Node, source_bytes: bytes) -> str:
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8")


def _flatten_identifier(node: Node, source_bytes: bytes) -> List[str]:
    """Expand scoped identifiers into individual path segments."""
    if node.type == "scoped_identifier":
        parts: List[str] = []
        for child in node.children:
            if child.type == "::":
                continue
            parts.extend(_flatten_identifier(child, source_bytes))
        return parts
    if node.type in {"identifier", "crate", "self", "super"}:
        return [_node_text(node, source_bytes)]
    return []


def _extract_module_names(root: Node, source_bytes: bytes) -> List[str]:
    """Return `mod foo;` declarations detected via Tree-sitter."""
    modules: List[str] = []
    stack = [root]

    while stack:
        node = stack.pop()
        if node.type == "mod_item" and node.child_by_field_name("body") is None:
            identifier = node.child_by_field_name("name")
            if identifier is not None:
                modules.append(_node_text(identifier, source_bytes))
        stack.extend(node.children)

    return modules


def _collect_use_entries(
    node: Node, source_bytes: bytes, prefix: List[str]
) -> List[UseEntry]:
    """Flatten nested use declarations into usable UseEntry records."""
    entries: List[UseEntry] = []
    node_type = node.type

    if node_type == "use_list":
        for child in node.children:
            if child.type in {",", "{", "}"}:
                continue
            entries.extend(_collect_use_entries(child, source_bytes, prefix))
        return entries

    if node_type == "use_as_clause":
        # First child represents the underlying path.
        for child in node.children:
            if child.type == "as":
                break
            if child.type in {
                "identifier",
                "self",
                "super",
                "crate",
                "scoped_identifier",
                "scoped_use_list",
            }:
                return _collect_use_entries(child, source_bytes, prefix)
        return entries

    if node_type == "use_wildcard":
        path_node = next(
            (child for child in node.children if child.type not in {"::", "*"}),
            None,
        )
        if path_node is not None:
            segments = prefix + _flatten_identifier(path_node, source_bytes)
            entries.append(UseEntry(segments=segments, is_glob=True))
        return entries

    if node_type == "scoped_use_list":
        meaningful_children = [child for child in node.children if child.type != "::"]
        if not meaningful_children:
            return entries
        head = meaningful_children[0]
        rest = meaningful_children[1:]
        head_segments = _flatten_identifier(head, source_bytes)
        new_prefix = prefix + head_segments
        if not rest:
            entries.append(UseEntry(segments=new_prefix))
            return entries
        for child in rest:
            entries.extend(_collect_use_entries(child, source_bytes, new_prefix))
        return entries

    if node_type in {"identifier", "crate", "self", "super"}:
        entries.append(UseEntry(segments=prefix + [_node_text(node, source_bytes)]))
        return entries

    if node_type == "scoped_identifier":
        entries.append(
            UseEntry(segments=prefix + _flatten_identifier(node, source_bytes))
        )
        return entries

    if node_type == "use_declaration":
        for child in node.children:
            if child.type in {"use", ";"}:
                continue
            entries.extend(_collect_use_entries(child, source_bytes, []))
        return entries

    return entries


def _extract_use_entries(root: Node, source_bytes: bytes) -> List[UseEntry]:
    entries: List[UseEntry] = []
    stack = [root]
    while stack:
        node = stack.pop()
        if node.type == "use_declaration":
            entries.extend(_collect_use_entries(node, source_bytes, []))
        else:
            stack.extend(node.children)
    return entries


def _candidate_paths(module_name: str, parent_dir: Path) -> Tuple[Path, ...]:
    return (
        parent_dir / f"{module_name}.rs",
        parent_dir / module_name / "mod.rs",
    )


def _resolve_module_path(module_name: str, parent_dir: Path) -> Path | None:
    for candidate in _candidate_paths(module_name, parent_dir):
        # Explicit resolve so we can reliably dedupe later.
        resolved = candidate.resolve()
        if resolved.exists():
            return resolved
    return None


def _read_file_contents(path: Path) -> str | None:
    try:
        return path.read_text()
    except FileNotFoundError:
        logger.warning("Skipping missing dependency candidate: %s", path)
    except UnicodeDecodeError:
        logger.warning("Unable to decode dependency file %s as UTF-8.", path)
    return None


def _format_relative_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def _resolve_declared_modules(
    module_names: Iterable[str], current_file: Path, project_root: Path
) -> List[Path]:
    dependencies: List[Path] = []
    for module_name in module_names:
        resolved = _resolve_module_path(module_name, current_file.parent)
        if resolved is None:
            logger.warning(
                "Unable to resolve module '%s' declared in %s.",
                module_name,
                current_file,
            )
            continue

        try:
            relative_display = resolved.relative_to(project_root)
        except ValueError:
            logger.warning(
                "Ignoring module '%s' from %s because it is outside the target root.",
                module_name,
                current_file,
            )
            continue

        logger.info(
            "Dependency detected: %s declares module '%s' -> %s",
            current_file,
            module_name,
            relative_display,
        )
        dependencies.append(resolved)
    return dependencies


def _derive_use_base_directory(
    segments: Sequence[str], current_file: Path, project_root: Path
) -> Tuple[Path, List[str]]:
    """Return the filesystem base dir and remaining module segments for a use path."""
    if not segments:
        return current_file.parent, []

    base_dir = current_file.parent
    idx = 0

    while idx < len(segments):
        token = segments[idx]
        if token == "crate":
            base_dir = project_root
        elif token == "self":
            base_dir = current_file.parent
        elif token == "super":
            potential = base_dir.parent
            if potential != base_dir:
                base_dir = potential
        else:
            break
        idx += 1

    return base_dir, list(segments[idx:])


def _candidate_segment_lists(
    module_segments: List[str], is_glob: bool
) -> List[List[str]]:
    """Return raw segments plus potential parent module fallbacks for inline items."""
    if not module_segments:
        return []

    candidates = [module_segments]
    if not is_glob and len(module_segments) > 1:
        candidates.append(module_segments[:-1])
    return candidates


def _resolve_segments_to_path(base_dir: Path, segments: List[str]) -> Path | None:
    if not segments:
        return None
    relative = Path(*segments)
    candidates = (
        (base_dir / relative).with_suffix(".rs"),
        base_dir / relative / "mod.rs",
    )
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.exists():
            return resolved
    return None


def _resolve_use_entry(
    entry: UseEntry, current_file: Path, project_root: Path
) -> Path | None:
    """Resolve a use path to a concrete file if it lives under the target root."""
    base_dir, module_segments = _derive_use_base_directory(
        entry.segments, current_file, project_root
    )
    if not module_segments:
        return None

    for candidate_segments in _candidate_segment_lists(module_segments, entry.is_glob):
        resolved = _resolve_segments_to_path(base_dir, candidate_segments)
        if resolved is None:
            continue
        try:
            relative_display = resolved.relative_to(project_root)
        except ValueError:
            logger.warning(
                "Use path '%s' from %s resolves outside the target root; skipping.",
                "::".join(entry.segments),
                current_file,
            )
            continue

        logger.info(
            "Use dependency detected: %s references '%s' -> %s",
            current_file,
            "::".join(entry.segments),
            relative_display,
        )
        return resolved
    return None


def _resolve_use_dependencies(
    use_entries: Iterable[UseEntry], current_file: Path, project_root: Path
) -> List[Path]:
    """Return unique file paths referenced via use statements."""
    dependencies: List[Path] = []
    seen: Set[Path] = set()
    for entry in use_entries:
        resolved = _resolve_use_entry(entry, current_file, project_root)
        if resolved is None or resolved in seen:
            continue
        seen.add(resolved)
        dependencies.append(resolved)
    return dependencies


def _find_local_module_files(current_file: Path, project_root: Path) -> List[Path]:
    contents = _read_file_contents(current_file)
    if contents is None:
        return []

    source_bytes = contents.encode("utf-8")
    tree = _PARSER.parse(source_bytes)
    root = tree.root_node
    declared_modules = _extract_module_names(root, source_bytes)
    use_entries = _extract_use_entries(root, source_bytes)
    logger.info(
        "Scanning %s (declares %d modules, %d use statements).",
        _format_relative_path(current_file, project_root),
        len(declared_modules),
        len(use_entries),
    )

    dependencies: List[Path] = []
    dependencies.extend(
        _resolve_declared_modules(declared_modules, current_file, project_root)
    )
    dependencies.extend(
        _resolve_use_dependencies(use_entries, current_file, project_root)
    )

    return dependencies


def include_dependencies(
    file_paths: Iterable[str], target_root: Path, max_depth: int
) -> List[str]:
    """Return file list plus dependencies discovered up to ``max_depth``."""
    if max_depth < 1:
        logger.info("Dependency depth < 1 provided; returning original file list only.")
        max_depth = 0

    source_files = list(file_paths)
    ordered_files: List[str] = []
    seen_strings: Set[str] = set()
    traversed_paths: Set[Path] = set()
    queue: deque[Tuple[Path, int]] = deque()

    def _add_file_string(path_str: str):
        if path_str not in seen_strings:
            ordered_files.append(path_str)
            seen_strings.add(path_str)

    for entry in source_files:
        _add_file_string(entry)
        resolved_entry = (target_root / entry).resolve()
        if not resolved_entry.exists():
            logger.warning("File listed in config not found: %s", entry)
            continue
        if resolved_entry in traversed_paths:
            continue
        traversed_paths.add(resolved_entry)
        queue.append((resolved_entry, 0))

    if source_files:
        logger.info(
            "Dependency scan queued %d file(s) with depth limit %d.",
            len(source_files),
            max_depth,
        )

    while queue:
        current, depth = queue.popleft()
        if depth >= max_depth:
            continue

        dependencies = _find_local_module_files(current, target_root)
        if not dependencies:
            continue

        for dep_path in dependencies:
            dep_display = _format_relative_path(dep_path, target_root)
            _add_file_string(dep_display)
            if dep_path in traversed_paths:
                continue
            traversed_paths.add(dep_path)
            queue.append((dep_path, depth + 1))

    if max_depth > 0:
        logger.info(
            "Dependency inclusion enabled. Base files: %d total files after expansion: %d.",
            len(source_files),
            len(ordered_files),
        )

    return ordered_files


__all__ = ["include_dependencies"]
