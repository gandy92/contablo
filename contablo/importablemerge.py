import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from typing import Protocol

from contablo.importable import ImporTable

logger = logging.getLogger(__file__)


class AssetLookup(Protocol):
    def lookup_symbol(isin_or_wkn: str) -> str: ...


def is_undef(value: Any, ignore_undef):
    if not ignore_undef:
        return False
    for item in ignore_undef:
        if isinstance(value, Decimal):
            return Decimal is None
        if isinstance(value, type(item)):
            if value == item:
                return True
    return False


def dicts_match_by_map(
    left: dict[str, Any],
    right: dict[str, Any],
    match_map: dict[str, str] = None,
    ignore_left: list[str] = None,
    ignore_right: list[str] = None,
    ignore_undef: list[Any] = None,
) -> bool:
    """Check if two dicts match, considering a subset of dict keys.
    Keys can be mapped between the two dicts.
    Remaining keys will be checked for same values in both dicts unless mentioned in ignore lists.
    Optionally, individual (non-mapped) keys may be missing on either side if value matches ignore_undef
    """
    if match_map is None:
        raise ValueError("match_map cannot be empty.")
    ignore_left = ignore_left or []
    ignore_right = ignore_right or []
    if any([k not in right for k in match_map.keys()]):
        # logger.debug(f"missing at least one of {match_map.keys()} in {right.keys()}")
        return False
    if any([v not in left for v in match_map.values()]):
        # logger.debug(f"missing at least one of {match_map.values()} in {left.keys()}")
        return False
    for right_key, left_key in match_map.items():
        if left.get(left_key, None) != right.get(right_key, None):
            # logger.debug(
            #     f"Mismatch 1: left[{left_key}]={left.get(left_key, None)} and right[{right_key}]={right.get(right_key, None)}"
            # )
            return False

    for key in left.keys():
        if key in ignore_left:
            continue
        if key in match_map.keys() or key in match_map.values():
            continue
        if ignore_undef and key not in right:
            continue
        if is_undef(left[key], ignore_undef):
            continue
        if key in right and is_undef(right[key], ignore_undef):
            continue
        if left.get(key, None) != right.get(key, None):
            logger.debug(f"Mismatch 2: left[{key}]={left.get(key, None)} and right[{key}]={right.get(key, None)}")
            return False
    for key in right.keys():
        if key in ignore_right:
            continue
        if key in match_map.keys() or key in match_map.values():
            continue
        if ignore_undef and key not in left:
            continue
        if is_undef(right[key], ignore_undef):
            continue
        if key in left and is_undef(left[key], ignore_undef):
            continue
        if left.get(key, None) != right.get(key, None):
            logger.debug(f"Mismatch 3: left[{key}]={left.get(key, None)} and right[{key}]={right.get(key, None)}")
            return False

    return True


def pick_one(
    left: list[dict[str, Any]],
    right: dict[str, Any],
    match_map: dict[str, str],
    ignore_left: list[str] = None,
    ignore_right: list[str] = None,
    ignore_values: list[Any] = None,
    *,
    remove_match: bool = False,
) -> dict[str, Any]:
    """Try to find an entry in the left list matching the right dict.

    match_map dictates, which keys from "right" (key) must match keys in "left" (value).
    """
    match_idx = set()
    for idx, row in enumerate(left):
        if dicts_match_by_map(row, right, match_map, ignore_left, ignore_right, ignore_values):
            match_idx.add(idx)
    # print(f"{match_idx=}")
    if len(match_idx) == 0:
        # logger.warning(f"No match for {right}, ignoring {ignore_right}.")
        return {}
    if len(match_idx) > 1:
        logger.warning(f"multiple matches: {match_idx=}")
        return {}
    logger.debug(f"Found match at idx {idx}")
    idx = match_idx.pop()
    result = left[idx].copy()
    if remove_match:
        del left[idx]
    return result


@dataclass
class LeftRightMatchRule:
    left_right_map: dict[str, str]
    ignored_fields: list[str]


def already_in(from_data: dict[str, str], to_data: dict[str, str], ignore_keys: list[str], undef: list[str]):
    for key, value in from_data.items():
        if key in ignore_keys:
            continue
        if is_undef(value, undef):
            continue
        if key not in to_data:
            # print(f"  not yet in: {key}")
            return False
        if is_undef(to_data[key], undef):
            continue
        if to_data[key] != value:
            # print(f"  not yet in: {key}={value}")
            return False
    return True


def importable_merge_two(
    source: ImporTable,
    target: ImporTable,
    match_rules: list[LeftRightMatchRule],
    addable_fields: list[str],
) -> ImporTable:
    """Merge two importables, using a set of match rules to identify mergable entries. Not suitable for inner merges."""
    # this implementation consumes all merable items from both importables to produce new entries.
    # finally, all non-mergable items from both importables are also added.
    imp = target.clone_empty()

    tgt = target.data_vector.copy()
    src = source.data_vector.copy()
    undef = [None, ""]

    def try_merge(match_map: dict[str, str], ignore_keys: list[str]) -> None:
        rem = []
        if not tgt:
            # print(f"Already finished, skipping {match_map}")
            return src
        for row in src:
            ignored_keys = [k for k in ignore_keys]
            # logger.warning(f"#### {row=}")
            if row.get("_allow_add", False):
                ignored_keys.extend(addable_fields)
                # print(f"***** {ignored_keys}")
            match = pick_one(tgt, row, match_map, ignored_keys, ignored_keys, ignore_values=undef, remove_match=True)
            if not match:
                rem.append(row)
                continue
            if not already_in(row, match, ignored_keys, undef):
                msrc = "|".join([s for s in [match.get("imported_from", None), row.get("imported_from", None)] if s])
                # print(msrc)
                match.update(
                    {k: v for k, v in row.items() if not is_undef(v, undef) and is_undef(match.get(k, None), undef)}
                )
                match["imported_from"] = msrc
            imp.data_vector.append(match)
        return rem

    for match_rule in match_rules:
        if not tgt:
            break

        src = try_merge(match_rule.left_right_map, match_rule.ignored_fields)

    # Todo: find better means of debugging without adding pandas dependency
    # print()
    # if imp.data_vector:
    #     print("result:")
    #     print("\n".join(pd.DataFrame(imp.data_vector)["imported_from"].to_list()))
    # else:
    #     print("strange, nothing was merged...")
    # print()
    # if tgt:
    #     print("remaining target:")
    #     print("\n".join(pd.DataFrame(tgt)["imported_from"].to_list()))
    # else:
    #     print("all of target was comsumed")
    # print()
    # if src:
    #     print("remaining source:")
    #     print("\n".join(pd.DataFrame(src)["imported_from"].to_list()))
    # else:
    #     print("all of source was comsumed")

    for row in tgt:
        imp.data_vector.append(row)

    for row in src:
        imp.data_vector.append(row)

    return imp


def importable_merge_one(
    target: ImporTable,
    item: dict[str, Any],
    match_rules: list[LeftRightMatchRule],
    addable_fields: list[str],
) -> ImporTable:
    """Merge two importables, using a set of match rules to identify mergable entries. Not suitable for inner merges."""
    # this implementation consumes all merable items from the target importable to produce a new entry.
    # finally, all non-mergable items from both importables are also added.
    imp = target.clone_empty()

    tgt = target.data_vector.copy()
    undef = [None, ""]

    for match_rule in match_rules:
        match_map, ignore_keys = match_rule.left_right_map, match_rule.ignored_fields
        if not tgt:
            break
        ignored_keys = [k for k in ignore_keys]  # Todo: what???
        # logger.warning(f"#### {item=}")
        if item.get("_allow_add", False):
            ignored_keys.extend(addable_fields)
            # print(f"***** {ignored_keys}")
        match = pick_one(tgt, item, match_map, ignored_keys, ignored_keys, ignore_values=undef, remove_match=True)
        if not match:
            continue
        if not already_in(item, match, ignored_keys, undef):
            msrc = "|".join([s for s in [match.get("imported_from", None), item.get("imported_from", None)] if s])
            # print(msrc)
            match.update(
                {k: v for k, v in item.items() if not is_undef(v, undef) and is_undef(match.get(k, None), undef)}
            )
            match["imported_from"] = msrc
        elif item.get("_allow_add", False):
            for key in addable_fields:
                if match.get(key, None) is not None and item.get(key, None) is not None:
                    match[key] = match[key] + item[key]
        tgt.append(match)
        item = None
        break

    # if there was no match, ust append the item as is
    if item is not None:
        tgt.append(item)

    imp.data_vector = tgt

    return imp


def importable_merge(
    source: ImporTable,
    target: ImporTable,
    match_rules: list[LeftRightMatchRule] = None,
    addable_fields: list[str] = None,
) -> ImporTable:
    result = target
    for item in source.iter_data():
        result = importable_merge_one(result, item, match_rules or [], addable_fields or [])
    return result
