"""Dynamic species profile forms driven by templates/*.yaml schema."""
from __future__ import annotations

from typing import Any, Callable

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Input, Label, Select, SelectionList, Static
from textual.widgets.selection_list import Selection

from ... import profile_schema as qschema
from ... import species_profile as speciesmod


def _is_select_blank(value: object) -> bool:
    if value is None:
        return True
    if value is Select.BLANK:
        return True
    null = getattr(Select, "NULL", None)
    if null is not None and value is null:
        return True
    return str(value) in {"Select.BLANK", "Select.NULL"}


def _clear_select(sel: Select) -> None:
    """Blank a Select safely (Select.BLANK is False on current Textual — cannot assign)."""
    try:
        sel.clear()
    except Exception:
        try:
            options = list(getattr(sel, "_options", []) or [])
            if options:
                first = options[0]
                sel.value = first[0] if isinstance(first, tuple) else first
        except Exception:
            pass


def _field_type(field: dict[str, Any]) -> str:
    return str(field.get("type") or "text").strip()


def _selection_list_from_opts(
    wid: str,
    opts: list[tuple[str, str]],
    *,
    selected: set[str] | None = None,
) -> SelectionList[str] | Static:
    picked = selected or set()
    if not opts:
        return Static(
            "(no planetary biomes on this body — secondary range empty)",
            classes="litany",
            id=f"{wid}-empty",
        )
    return SelectionList[str](
        *[Selection(lab, val, val in picked) for lab, val in opts],
        id=wid,
        classes="biome-multi",
    )


def yield_step_fields(
    step: dict[str, Any],
    *,
    trophic_slots: list[str] | None = None,
    biome_options: list[tuple[str, str]] | None = None,
    secondary_biome_options: list[tuple[str, str]] | None = None,
) -> ComposeResult:
    """Yield Label + Input/Select/SelectionList widgets for one schema step."""
    if step.get("hint"):
        yield Static(str(step["hint"]), classes="litany")
    for field in step.get("fields") or []:
        wid = qschema.widget_id(field)
        label = str(field.get("label") or field.get("id") or wid)
        yield Label(label)
        ftype = _field_type(field)
        if ftype == "biome_multi":
            yield _selection_list_from_opts(wid, secondary_biome_options or [])
            continue
        if ftype in ("select", "yes_no", "trophic_slot", "biome_select"):
            if ftype == "yes_no":
                opts = [("no", "no"), ("yes", "yes")]
            elif ftype == "trophic_slot":
                slots = trophic_slots or ["apex"]
                opts = [(s, s) for s in slots]
            elif ftype == "biome_select":
                opts = biome_options or list(speciesmod.SPECIAL_ORIGIN_PLACES)
                if not opts:
                    opts = list(speciesmod.SPECIAL_ORIGIN_PLACES)
            else:
                opts = qschema.option_pairs(field) or [("—", "")]
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
    biome_options: list[tuple[str, str]] | None = None,
    secondary_biome_options: list[tuple[str, str]] | None = None,
) -> None:
    sch = schema or qschema.load_schema()
    for field in qschema.all_fields(sch):
        wid = qschema.widget_id(field)
        store = str(field.get("store") or "")
        raw = qschema.get_store(profile, store)
        ftype = _field_type(field)
        try:
            if ftype == "biome_multi":
                selected = {
                    str(x).strip()
                    for x in (raw if isinstance(raw, list) else [])
                    if str(x).strip()
                }
                opts = list(secondary_biome_options or [])
                # Replace stale Input / empty Static with a SelectionList when needed.
                ensure_secondary_biome_widget(root, wid, opts, selected=selected)
                continue
            if ftype in ("select", "yes_no", "trophic_slot", "biome_select"):
                sel = root.query_one(f"#{wid}", Select)
                if ftype == "yes_no":
                    sel.set_options([("no", "no"), ("yes", "yes")])
                    sel.value = "yes" if raw else "no"
                elif ftype == "trophic_slot":
                    slots = trophic_slots or ["apex"]
                    sel.set_options([(s, s) for s in slots])
                    val = str(raw or "apex")
                    sel.value = val if val in slots else slots[0]
                elif ftype == "biome_select":
                    opts = list(biome_options or speciesmod.SPECIAL_ORIGIN_PLACES)
                    if not opts:
                        opts = list(speciesmod.SPECIAL_ORIGIN_PLACES)
                    val = str(raw or "").strip()
                    values = {v for _, v in opts}
                    if val and val not in values:
                        opts = [(f"{val} (not on this body)", val), *opts]
                    sel.set_options(opts)
                    if val:
                        sel.value = val
                    else:
                        sel.value = opts[0][1]
                else:
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


def ensure_secondary_biome_widget(
    root: Widget,
    wid: str,
    opts: list[tuple[str, str]],
    *,
    selected: set[str] | None = None,
) -> None:
    """Mount or refresh the secondary-biomes SelectionList (fixes stale Input)."""
    picked = selected or set()
    try:
        parent = root.query_one("#sp-scroll", Widget)
    except Exception:
        return

    existing_sl = None
    existing_input = None
    existing_empty = None
    try:
        existing_sl = root.query_one(f"#{wid}", SelectionList)
    except Exception:
        pass
    try:
        existing_input = root.query_one(f"#{wid}", Input)
    except Exception:
        pass
    try:
        existing_empty = root.query_one(f"#{wid}-empty", Static)
    except Exception:
        pass

    # Already a SelectionList — just sync ticks.
    if existing_sl is not None and existing_input is None:
        try:
            existing_sl.deselect_all()
            for val in picked:
                try:
                    existing_sl.select(val)
                except Exception:
                    continue
        except Exception:
            pass
        return

    # Stale Input / empty Static: schedule replace after remove settles.
    if existing_input is None and existing_empty is None and existing_sl is None:
        # Nothing to fix; compose should have created the control.
        return

    anchor = None
    for label in parent.query(Label):
        text = getattr(label, "content", None) or str(label.render())
        if "secondary" in str(text).lower():
            anchor = label
            break

    stale = [w for w in (existing_input, existing_empty, existing_sl) if w is not None]
    for w in stale:
        w.remove()

    def _mount() -> None:
        widget = _selection_list_from_opts(wid, opts, selected=picked)
        if anchor is not None and anchor in parent.children:
            parent.mount(widget, after=anchor)
        else:
            parent.mount(widget)

    try:
        root.app.call_after_refresh(_mount)
    except Exception:
        _mount()


def collect_profile_from_widgets(
    root: Widget,
    schema: dict[str, Any] | None = None,
    *,
    base: dict[str, Any] | None = None,
    secondary_biome_options: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    sch = schema or qschema.load_schema()
    profile = base or speciesmod.empty_profile()
    profile = dict(profile)
    profile.setdefault("answers", {})
    for field in qschema.all_fields(sch):
        wid = qschema.widget_id(field)
        store = str(field.get("store") or "")
        ftype = _field_type(field)
        try:
            if ftype == "biome_multi":
                try:
                    sl = root.query_one(f"#{wid}", SelectionList)
                    value: Any = [str(v) for v in (sl.selected or [])]
                except Exception:
                    # Legacy Input fallback (comma ids) if restart not yet done
                    try:
                        text = root.query_one(f"#{wid}", Input).value.strip()
                        value = [x.strip() for x in text.split(",") if x.strip()]
                    except Exception:
                        value = []
            elif ftype in ("select", "yes_no", "trophic_slot", "biome_select"):
                sel = root.query_one(f"#{wid}", Select)
                val = sel.value
                if _is_select_blank(val):
                    value = False if ftype == "yes_no" else ""
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
    # Auto multi-range when secondaries are selected.
    secondaries = list(profile.get("secondary_biomes") or [])
    if secondaries and str(profile.get("range") or "single") == "single":
        profile["range"] = "multi"
    return profile


def refresh_dependent_selects(
    root: Widget,
    profile: dict[str, Any],
    schema: dict[str, Any] | None = None,
) -> None:
    """When a parent select changes, refresh child options_by selects."""
    sch = schema or qschema.load_schema()
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
    body_slug: str | None = None,
) -> str:
    """Plain-text mirror of profile fields for Specimens read-only pane."""
    sch = schema or qschema.load_schema()
    lines: list[str] = []
    if body_slug:
        from ... import species_media as media

        sid = str(profile.get("id") or "").strip()
        lines.append("— Profile picture —")
        lines.append(media.profile_status_label(body_slug, sid))
        lines.append(f"  {media.resolve_profile_image(body_slug, sid)}")
        lines.append("")
    for step in qschema.steps(sch):
        title = str(step.get("title") or step.get("id") or "")
        lines.append(f"— {title} —")
        for field in step.get("fields") or []:
            label = str(field.get("label") or field.get("id") or "")
            store = str(field.get("store") or "")
            raw = qschema.get_store(profile, store)
            ftype = _field_type(field)
            if ftype == "yes_no":
                text = "yes" if raw else "no"
            elif ftype in ("comma_list", "biome_multi"):
                if isinstance(raw, list):
                    text = ", ".join(str(x) for x in raw)
                else:
                    text = str(raw or "").strip()
            elif ftype in ("select", "biome_select"):
                code = str(raw or "").strip()
                if not code:
                    text = ""
                elif ftype == "select":
                    text = qschema.resolve_option_label(field, code, profile)
                else:
                    # biome_select: prefer body biome labels when available
                    text = code
                    if body_slug:
                        try:
                            from ...species_profile import biomes_for_body_slug

                            opts = speciesmod.origin_place_options(
                                biomes_for_body_slug(body_slug)
                            )
                            for lab, val in opts:
                                if val == code:
                                    text = lab
                                    break
                        except Exception:
                            pass
            elif ftype == "trophic_slot":
                text = str(raw or "").strip()
            else:
                text = str(raw or "").strip()
            if not text:
                text = "—"
            lines.append(f"{label}")
            lines.append(f"  {text}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
