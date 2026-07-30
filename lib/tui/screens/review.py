"""Review — seal to cogitator-results/, save pack, propose-export preview."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Static

from ... import packs as packsmod
from ...wizard_session import WizardSession
from ..features import CONSULTATION_ENABLED
from ..widgets.header import CogitatorHeader
from ..widgets.warn_log import WarnLog

_NEW_PACK = "__new__"


class ReviewScreen(Screen):
    TRACK_DIRTY = True

    def compose(self) -> ComposeResult:
        yield CogitatorHeader("LAYER L7 / SEAL & ARCHIVE")
        with VerticalScroll(id="main"):
            yield Static("REVIEW / COMMIT", classes="title")
            yield Static(id="review-panel", classes="panel")
            yield Label("Pack destination:")
            yield Select([("…", "__init__")], id="pack-select", allow_blank=False)
            yield Label("New pack id (only if 'New pack…' selected):")
            yield Input(value="", id="pack-id", disabled=True)
            yield Label("Pack title:")
            yield Input(value="", id="pack-title")
            with Horizontal(classes="-toolbar"):
                yield Button("Seal to results (L7)", id="btn-out", variant="primary")
                yield Button(
                    "Open in Archive"
                    if CONSULTATION_ENABLED
                    else "Archive (offline)",
                    id="btn-archive",
                    disabled=not CONSULTATION_ENABLED,
                )
                yield Button("Save to pack", id="btn-pack")
                yield Button("Propose codex (dry-run)", id="btn-propose")
            yield Static(id="propose-panel", classes="panel")
            with Horizontal(classes="-toolbar"):
                yield Button("Return to menu", id="btn-done", variant="primary")
                yield Button("Back", id="btn-back")
        yield WarnLog()

    def on_mount(self) -> None:
        self.query_one(WarnLog).boot()
        self._setup_pack_select()
        self._refresh()

    def _session(self) -> WizardSession:
        return self.app.session  # type: ignore[attr-defined]

    def _setup_pack_select(self) -> None:
        session = self._session()
        packs = packsmod.list_packs()
        opts: list[tuple[str, str]] = []
        for p in packs:
            pid = str(p.get("id") or "")
            if not pid:
                continue
            title = str(p.get("title") or pid)
            label = pid if title == pid else f"{pid} — {title}"
            opts.append((label, pid))
        opts.append(("New pack…", _NEW_PACK))
        sel = self.query_one("#pack-select", Select)
        sel.set_options(opts)
        prefer = session.pack_id
        if prefer and any(v == prefer for _, v in opts):
            sel.value = prefer
            self._apply_pack_choice(prefer)
        elif packs:
            sel.value = str(packs[0].get("id"))
            self._apply_pack_choice(str(packs[0].get("id")))
        else:
            sel.value = _NEW_PACK
            self._apply_pack_choice(_NEW_PACK)

    def _apply_pack_choice(self, value: str) -> None:
        new_mode = value == _NEW_PACK
        pid_input = self.query_one("#pack-id", Input)
        title_input = self.query_one("#pack-title", Input)
        pid_input.disabled = not new_mode
        if new_mode:
            if not pid_input.value.strip():
                pid_input.value = "my-pack"
            if not title_input.value.strip():
                title_input.value = "Custom mesh"
            return
        pid_input.value = value
        try:
            meta = packsmod.load_pack_meta(value)
            title_input.value = str(meta.get("title") or value)
        except FileNotFoundError:
            title_input.value = value

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "pack-select" and event.value is not Select.BLANK:
            self._apply_pack_choice(str(event.value))

    def _resolve_pack_id(self) -> str | None:
        sel = self.query_one("#pack-select", Select)
        value = str(sel.value) if sel.value is not Select.BLANK else ""
        if value == _NEW_PACK or not value:
            return self.query_one("#pack-id", Input).value.strip() or None
        return value

    def _refresh(self) -> None:
        session = self._session()
        body = session.body or {}
        system = session.system or {}
        warns = list(session.warnings)
        warns += list((body.get("warnings") or []))
        warns += list((system.get("warnings") or []))
        # dedupe preserve order
        seen: set[str] = set()
        uniq = []
        for w in warns:
            if w not in seen:
                seen.add(w)
                uniq.append(w)
        dest = self._resolve_pack_id() or "(none)"
        text = (
            f"System: {(system.get('meta') or {}).get('slug')}\n"
            f"Body: {(body.get('meta') or {}).get('slug')}\n"
            f"Pack context: {session.pack_id or '(greenfield)'}\n"
            f"Save destination: {dest}\n"
            f"Provenance: {session.provenance}\n"
            f"Warnings ({len(uniq)}):\n"
            + ("\n".join(f"  - {w}" for w in uniq) if uniq else "  (none)")
        )
        self.query_one("#review-panel", Static).update(text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        session = self._session()
        log = self.query_one(WarnLog)
        if event.button.id == "btn-back":
            self.app.request_back()  # type: ignore[attr-defined]
            return
        if event.button.id == "btn-done":
            self.app.request_menu()  # type: ignore[attr-defined]
            return
        if event.button.id == "btn-out":
            if session.body is None:
                log.push("no body to finalize")
                return
            world = session.finalize()
            log.push(f"sealed cogitator-results/{world['meta']['slug']}/ (magos + literary + state.json)")
            self._refresh()
            return
        if event.button.id == "btn-archive":
            if not CONSULTATION_ENABLED:
                log.push(
                    "Archive offline — dossier redesign pending. "
                    "Use Amendment after seal to inspect the body."
                )
                return
            body = session.body or {}
            slug = (body.get("meta") or {}).get("slug")
            if not slug:
                log.push("no body slug — seal to results first")
                return
            from .out_archive import OutArchiveScreen

            # Prefer magos if present; Archive still opens even before write
            self.app.push_screen(
                OutArchiveScreen(kind="body", slug=slug, filename="magos.md")
            )
            return
        if event.button.id == "btn-pack":
            pack_id = self._resolve_pack_id()
            if not pack_id:
                log.push("select an existing pack or enter a new pack id")
                return
            title = self.query_one("#pack-title", Input).value.strip() or pack_id
            if session.system is None and session.body is None:
                log.push("nothing to save")
                return
            # Ensure body finalized if present
            if session.body and not (session.body.get("render") or {}).get("magos_path"):
                session.finalize()
            existed = (packsmod.pack_dir(pack_id) / "pack.yaml").is_file()
            desc = None if existed else "Exported from cogitator wizard"
            path = session.save_as_pack(pack_id, title=title, description=desc)
            session.pack_id = packsmod.slugify_pack_id(pack_id)
            verb = "updated" if existed else "created"
            log.push(f"{verb} pack → {path}")
            self._setup_pack_select()
            self._refresh()
            return
        if event.button.id == "btn-propose":
            if session.body is None:
                log.push("no body")
                return
            if not (session.body.get("render") or {}).get("magos_path"):
                session.finalize()
            text = session.propose_export_text()
            self.query_one("#propose-panel", Static).update(text)
            log.push("codex propose dry-run rendered")
            return
