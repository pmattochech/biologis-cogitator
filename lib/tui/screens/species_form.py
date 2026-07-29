"""Dynamic species profile forms driven by templates/*.yaml schema."""
from __future__ import annotations

from typing import Any, Callable

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Input, Label, Select, Static

from ... import profile_schema as qschema
from ... import species_profile as speciesmod


def _is_select_blank(value: object) -> bool:
    if value is None:
        return True
    if value is Select.BLANK:
        return True
    # Newer Textual: Select.NULL sentinel
    null = getattr(Select, "NULL", None)
    if null is not None and value is null:
        return True
    return str(value) in {"Select.BLANK", "Select.NULL"}


def _clear_select(sel: Select) -> None:
    """Blank a Select safely (Select.BLANK is False on current Textual — cannot assign)."""
    try:
        sel.clear()
    except Exception:
        # Fallback: pick first option if clear unsupported
        try:
            options = list(getattr(sel, "_options", []) or [])
            if options:
                first = options[0]
                sel.value = first[0] if isinstance(first, tuple) else first
        except Exception:
            pass


def yield_step_fields(
    step: dict[str, Any],
    *,
    trophic_slots: list[str] | None = None,
) -> ComposeResult:
    """Yield Label + Input/Select widgets for one schema step."""
    if step.get("hint"):
        yield Static(str(step["hint"]), classes="litany")
    for field in step.get("fields") or []:
        wid = qschema.widget_id(field)
        label = str(field.get("label") or field.get("id") or wid)
        yield Label(label)
        ftype = str(field.get("type") or "text")
        if ftype in ("select", "yes_no", "trophic_slot"):
            if ftype == "yes_no":
                opts = [("no", "no"), ("yes", "yes")]
            elif ftype == "trophic_slot":
                slots = trophic_slots or ["apex"]
                opts = [(s, s) for s in slots]
            else:
                opts = qschema.option_pairs(field) or [("—", "")]
                # Placeholder until depends_on resolves
                if field.get("depends_on") and not opts:
                    opts = [("(pick parent first)", "")]
            yield Select(
                opts,
                id=wid,
                allow_blank=ftype == "select",
            )
        else:
            default = field.get("default")
            yield Input(
                value=""
                if default is None or isinstance(default, (list, bool))
                else str(default),
                id=wid,
                placeholder=str(field.get("placeholder") or ""),
            )


def apply_profile_to_widgets(
    root: Widget,
    profile: dict[str, Any],
    schema: dict[str, Any] | None = None,
    *,
    trophic_slots: list[str] | None = None,
) -> None:
    sch = schema or qschema.load_schema()
    for field in qschema.all_fields(sch):
        wid = qschema.widget_id(field)
        store = str(field.get("store") or "")
        raw = qschema.get_store(profile, store)
        ftype = str(field.get("type") or "text")
        try:
            if ftype in ("select", "yes_no", "trophic_slot"):
                sel = root.query_one(f"#{wid}", Select)
                if ftype == "yes_no":
                    sel.set_options([("no", "no"), ("yes", "yes")])
                    sel.value = "yes" if raw else "no"
                elif ftype == "trophic_slot":
                    slots = trophic_slots or ["apex"]
                    sel.set_options([(s, s) for s in slots])
                    val = str(raw or "apex")
                    sel.value = val if val in slots else slots[0]
                else:
                    # Refresh dependent options from current profile
                    pairs = qschema.option_pairs(field, profile)
                    if not pairs:
                        pairs = [("(none)", "")]
                    sel.set_options(pairs)
                    val = str(raw or "").strip()
                    values = {v for _, v in pairs}
                    if val and val in values:
                        sel.value = val
                    else:
                        _clear_select(sel)
            else:
                inp = root.query_one(f"#{wid}", Input)
                if ftype == "comma_list":
                    if isinstance(raw, list):
                        inp.value = ", ".join(str(x) for x in raw)
                    else:
                        inp.value = str(raw or "")
                else:
                    inp.value = "" if raw is None else str(raw)
        except Exception:
            pass


def collect_profile_from_widgets(
    root: Widget,
    schema: dict[str, Any] | None = None,
    *,
    base: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sch = schema or qschema.load_schema()
    profile = base or speciesmod.empty_profile()
    profile = dict(profile)
    profile.setdefault("answers", {})
    for field in qschema.all_fields(sch):
        wid = qschema.widget_id(field)
        store = str(field.get("store") or "")
        ftype = str(field.get("type") or "text")
        try:
            if ftype in ("select", "yes_no", "trophic_slot"):
                sel = root.query_one(f"#{wid}", Select)
                val = sel.value
                if _is_select_blank(val):
                    value: Any = False if ftype == "yes_no" else ""
                elif ftype == "yes_no":
                    value = str(val) == "yes"
                else:
                    value = str(val)
            else:
                text = root.query_one(f"#{wid}", Input).value.strip()
                if ftype == "comma_list":
                    value = [x.strip() for x in text.split(",") if x.strip()]
                else:
                    value = text
            qschema.set_store(profile, store, value)
        except Exception:
            continue
    # Mirror G dossier into profile.dossier for lock convenience
    g_path = qschema.get_store(profile, "answers.G.dossier_path")
    if g_path:
        profile["dossier"] = str(g_path)
    return profile


def refresh_dependent_selects(
    root: Widget,
    profile: dict[str, Any],
    schema: dict[str, Any] | None = None,
) -> None:
    """When a parent select changes, refresh child options_by selects."""
    sch = schema or qschema.load_schema()
    # Merge current widgets into profile first for accurate depends_on
    live = collect_profile_from_widgets(root, sch, base=profile)
    for field in qschema.all_fields(sch):
        if not field.get("depends_on"):
            continue
        wid = qschema.widget_id(field)
        try:
            sel = root.query_one(f"#{wid}", Select)
        except Exception:
            continue
        pairs = qschema.option_pairs(field, live)
        if not pairs:
            pairs = [("(pick parent first)", "")]
        current = sel.value
        sel.set_options(pairs)
        values = {v for _, v in pairs}
        if not _is_select_blank(current) and str(current) in values:
            sel.value = str(current)
        else:
            _clear_select(sel)


def min_gate_hint() -> str:
    return qschema.min_gate_hint()


def show_min_errors(root: Widget, errors: list[str]) -> None:
    try:
        root.query_one("#sp-min-hint", Static).update(
            " | ".join(errors) if errors else min_gate_hint()
        )
    except Exception:
        pass


def on_select_changed_refresh(
    root: Widget,
    event_select_id: str,
    profile_getter: Callable[[], dict[str, Any]],
    schema: dict[str, Any] | None = None,
) -> None:
    """Call from screen.on_select_changed to refresh depends_on children."""
    sch = schema or qschema.load_schema()
    # Only refresh if this select is a dependency parent
    parents = {
        str(f.get("depends_on") or "")
        for f in qschema.all_fields(sch)
        if f.get("depends_on")
    }
    parent_wids = set()
    for store in parents:
        field = qschema.field_by_store(store, sch)
        if field:
            parent_wids.add(qschema.widget_id(field))
    if event_select_id in parent_wids:
        refresh_dependent_selects(root, profile_getter(), sch)


def format_profile_readonly(
    profile: dict[str, Any],
    schema: dict[str, Any] | None = None,
    *,
    trophic_slots: list[str] | None = None,
) -> str:
    """Plain-text mirror of profile fields for Specimens read-only pane."""
    sch = schema or qschema.load_schema()
    lines: list[str] = []
    for step in qschema.steps(sch):
        title = str(step.get("title") or step.get("id") or "")
        lines.append(f"— {title} —")
        for field in step.get("fields") or []:
            label = str(field.get("label") or field.get("id") or "")
            store = str(field.get("store") or "")
            raw = qschema.get_store(profile, store)
            ftype = str(field.get("type") or "text")
            if ftype == "yes_no":
                text = "yes" if raw else "no"
            elif ftype == "comma_list":
                if isinstance(raw, list):
                    text = ", ".join(str(x) for x in raw)
                else:
                    text = str(raw or "").strip()
            else:
                text = str(raw or "").strip()
            if not text:
                text = "—"
            lines.append(f"{label}")
            lines.append(f"  {text}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
