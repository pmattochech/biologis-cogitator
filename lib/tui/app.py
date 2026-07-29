"""CogitatorApp — Textual entry for biologis-cogitator wizard."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from textual.app import App
from textual.widgets import Input, Select, TextArea

from .. import update as updatemod
from ..profile_schema import clear_schema_cache
from ..wizard_session import WizardSession
from .screens.boot import BootScreen
from .screens.splash import SplashScreen
from .theme import COGITATOR_CSS
from .widgets.confirm_dirty import ConfirmDirtyScreen
from .widgets.header import CogitatorHeader


class CogitatorApp(App[None]):
    CSS = COGITATOR_CSS
    TITLE = "Biologis Cogitator"
    BINDINGS = [("q", "request_terminate", "Terminate")]

    def __init__(
        self,
        *,
        seed: int | None = None,
        pack: str | None = None,
        splash: bool = True,
    ) -> None:
        super().__init__()
        self.session = WizardSession(seed=seed, pack_id=pack)
        self._show_splash = splash
        # Ignore widget Changed events until the new screen finishes hydrating
        self._dirty_armed: bool = True
        self._dirty_was_before_push: bool = False
        self._update_notice_shown: bool = False
        self._current_notice_shown: bool = False
        self._update_banner_kind: str = "update"
        self._update_banner_text: str = updatemod.BANNER_TEXT
        self._status_toast_sent: bool = False

    def on_mount(self) -> None:
        # Background poll — apply only on next launch; banners report status live.
        if updatemod.auto_update_enabled() and updatemod.is_git_checkout():
            self.set_interval(
                updatemod.poll_interval_seconds(),
                self._poll_for_updates,
                name="biologis-update-poll",
            )
            self.set_timer(3.0, self._poll_for_updates)
        if self._show_splash:
            self.push_screen(SplashScreen())
        else:
            self.push_screen(BootScreen())

    def _poll_for_updates(self) -> None:
        if not updatemod.auto_update_enabled():
            return
        try:
            status = updatemod.check_for_update(fetch=True)
        except Exception:
            return
        if status.available:
            first = not self._update_notice_shown
            self._update_notice_shown = True
            self._current_notice_shown = False
            self._update_banner_kind = "update"
            self._update_banner_text = updatemod.banner_text(status)
            self._show_status_banner(
                self._update_banner_text, kind="update", toast=first
            )
            return
        # Up to date — show once, then auto-hide (update banner stays sticky).
        if self._update_notice_shown:
            return
        if self._current_notice_shown:
            return
        if not status.local or status.error:
            return
        self._current_notice_shown = True
        self._update_banner_kind = "current"
        self._update_banner_text = updatemod.current_banner_text(status)
        self._show_status_banner(
            self._update_banner_text, kind="current", toast=True
        )
        self.set_timer(12.0, self._hide_current_banner)

    def _hide_current_banner(self) -> None:
        if self._update_notice_shown:
            return
        if self._update_banner_kind != "current":
            return
        try:
            for hdr in self.screen.query(CogitatorHeader):
                hdr.hide_update_notice()
        except Exception:
            pass

    def _show_status_banner(
        self, text: str, *, kind: str, toast: bool = False
    ) -> None:
        try:
            for hdr in self.screen.query(CogitatorHeader):
                hdr.show_status_banner(text, kind=kind)
        except Exception:
            pass
        if not toast or self._status_toast_sent:
            return
        self._status_toast_sent = True
        if kind == "update":
            try:
                self.notify(
                    "Update available — save work, Terminate, and reopen.",
                    severity="warning",
                    timeout=12,
                )
            except Exception:
                pass
        elif kind == "current":
            try:
                self.notify(
                    "Cogitator current — latest build.",
                    severity="information",
                    timeout=6,
                )
            except Exception:
                pass

    def _show_update_banner(self, text: str) -> None:
        self._show_status_banner(text, kind="update", toast=False)

    def push_screen(self, screen, *args, **kwargs):  # type: ignore[no-untyped-def]
        """Disarm dirty tracking while the new screen hydrates widgets."""
        self._dirty_was_before_push = self.session.is_dirty()
        self._dirty_armed = False
        result = super().push_screen(screen, *args, **kwargs)
        self.call_after_refresh(self._arm_dirty_tracking)
        if self._update_notice_shown or (
            self._current_notice_shown and self._update_banner_kind == "current"
        ):
            text = self._update_banner_text
            kind = self._update_banner_kind

            def _reapply() -> None:
                # Re-paint header banner only — never re-toast on navigation.
                self._show_status_banner(text, kind=kind, toast=False)

            self.call_after_refresh(_reapply)
        return result

    def _arm_dirty_tracking(self) -> None:
        self._dirty_armed = True
        # Drop false dirty from programmatic Input/Select fills on open
        if not self._dirty_was_before_push:
            self.session.clear_dirty()

    def _should_track_widget_dirty(self, widget: object | None) -> bool:
        if not self._dirty_armed:
            return False
        if not getattr(self.screen, "TRACK_DIRTY", False):
            return False
        if widget is None:
            return False
        # Programmatic .value / load_text during hydrate usually has no focus
        try:
            return bool(getattr(widget, "has_focus", False))
        except Exception:
            return False

    # --- dirty tracking from live edits ---

    def on_input_changed(self, event: Input.Changed) -> None:
        if self._should_track_widget_dirty(getattr(event, "input", None) or event.control):
            self.session.mark_dirty()

    def on_select_changed(self, event: Select.Changed) -> None:
        if self._should_track_widget_dirty(getattr(event, "select", None) or event.control):
            self.session.mark_dirty()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if self._should_track_widget_dirty(
            getattr(event, "text_area", None) or event.control
        ):
            self.session.mark_dirty()

    # --- navigation with unsaved guard ---

    def guard_unsaved(self, action: Callable[[], None], *, reason: str = "") -> None:
        if not self.session.is_dirty():
            action()
            return
        msg = "Unsaved changes detected. Save before continuing?"
        if reason:
            msg = f"{reason}\n\n{msg}"

        def _after(result: str | None) -> None:
            if result is None or result == "cancel":
                return
            if result == "save":
                err = self.save_unsaved()
                if err:
                    try:
                        from .widgets.warn_log import WarnLog

                        self.screen.query_one(WarnLog).push(f"save failed: {err}")
                    except Exception:
                        self.notify(f"save failed: {err}", severity="error")
                    return
            else:
                # discard
                self.session.clear_dirty()
            action()

        self.push_screen(ConfirmDirtyScreen(message=msg), _after)

    def save_unsaved(self) -> str | None:
        """Flush current screen + pack lock if possible. None = ok."""
        screen = self.screen
        if hasattr(screen, "flush_unsaved"):
            try:
                err = screen.flush_unsaved()  # type: ignore[misc]
            except Exception as exc:
                return str(exc)
            if err:
                return str(err)
        sess = self.session
        if sess.body is not None and sess.pack_id:
            try:
                sess.save_pack_lock()
            except Exception as exc:
                return str(exc)
        sess.clear_dirty()
        return None

    def request_back(self) -> None:
        self.guard_unsaved(
            lambda: self.pop_screen() if len(self.screen_stack) > 1 else None,
            reason="Leaving this page.",
        )

    def _pop_to_boot(self) -> None:
        """Pop pushed screens until Boot is current. Never pop Boot itself."""
        while len(self.screen_stack) > 1 and not isinstance(self.screen, BootScreen):
            self.pop_screen()
        if isinstance(self.screen, BootScreen):
            return
        # Only the mode's base placeholder remains
        self.switch_screen(BootScreen())

    def _boot_message(self, message: str) -> None:
        try:
            from .widgets.warn_log import WarnLog

            self.screen.query_one(WarnLog).push(message)
        except Exception:
            try:
                self.notify(message)
            except Exception:
                pass

    def _refresh_boot_packs(self) -> None:
        """Re-fill pack list on boot after reload/menu."""
        if not isinstance(self.screen, BootScreen):
            return
        try:
            from ... import packs as packsmod
            from textual.widgets import Label, ListItem, ListView

            lv = self.screen.query_one("#pack-list", ListView)
            lv.clear()
            for meta in packsmod.list_packs():
                title = meta.get("title") or meta.get("id")
                item = ListItem(Label(f"{meta.get('id')} — {title}"))
                item.pack_id = meta.get("id")  # type: ignore[attr-defined]
                lv.append(item)
        except Exception:
            pass

    def request_menu(self) -> None:
        def _go() -> None:
            seed = self.session.seed
            self.session = WizardSession(seed=seed)
            self._pop_to_boot()
            self._refresh_boot_packs()
            self._boot_message("returned to main menu")

        self.guard_unsaved(_go, reason="Return to main menu.")

    def request_reload(self) -> None:
        def _go() -> None:
            clear_schema_cache()
            sess = self.session
            resume = dict(sess.edit_resume or {})
            seed = sess.seed
            pack = sess.pack_id
            slug = resume.get("slug") or sess.body_slug()
            from_results = bool(resume.get("from_results"))

            self.session = WizardSession(seed=seed, pack_id=pack)
            self._pop_to_boot()
            self._refresh_boot_packs()

            if not slug:
                self._boot_message("reloaded cogitator (schema cache cleared)")
                return

            try:
                self.session.load_body_for_edit(
                    slug, pack_id=pack, from_results=from_results
                )
                self.session.clear_dirty()
                from .screens.edit_hub import EditHubScreen

                self.push_screen(EditHubScreen())
                try:
                    from .widgets.warn_log import WarnLog

                    self.screen.query_one(WarnLog).push(
                        f"reloaded {slug} + profile schema"
                    )
                except Exception:
                    pass
            except Exception as exc:
                self._boot_message(f"reload failed: {exc}")

        self.guard_unsaved(_go, reason="Reload cogitator from last saved state.")

    def request_terminate(self) -> None:
        self.guard_unsaved(lambda: self.exit(), reason="Terminate cogitator process.")

    def action_request_terminate(self) -> None:
        self.request_terminate()


def run_wizard(
    *,
    seed: int | None = None,
    pack: str | None = None,
    splash: bool = True,
) -> None:
    # Apply any pending git update before importing/running UI code paths that
    # already loaded — primarily for `./run wizard`. Launchers also update first.
    try:
        updatemod.apply_startup_update(verbose=True)
    except Exception as exc:
        print(f"[biologis-cogitator] startup update skipped: {exc}", flush=True)
    # Hybrid: real SWF-derived GIF in a Tk window, then Textual hub (no TTY art splash).
    if splash:
        from ..hybrid_splash import maybe_show_hybrid_splash

        maybe_show_hybrid_splash()
    # textual-image must probe the terminal *before* App.run() (TGP/Sixel query).
    from .widgets.profile_plate import ensure_image_support

    ensure_image_support()
    CogitatorApp(seed=seed, pack=pack, splash=False).run()
