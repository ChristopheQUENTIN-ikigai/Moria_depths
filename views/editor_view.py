"""
EditorView — a keyboard-driven, two-pane editor for the game's JSON content
files (data/*.json).  One generic engine drives four editors (items, equipment,
monsters, spells); each editor is just a schema config.

Style matches the rest of the game: monospace text + key handlers, no GUI lib.

Controls
  ↑/↓            move within the focused pane
  TAB / ←/→      switch between the entry list and its fields
  ENTER          (list) edit selected entry · (field) edit/toggle/cycle value
  A              add a new entry          D  delete selected entry
  X / DEL        unset the selected field (remove the key)
  S              save to disk (and reload content)
  ESC            leave the editor (prompts if there are unsaved changes)

While editing a text/number value: type to change, BACKSPACE to delete,
ENTER to commit, ESC to cancel.
"""
from __future__ import annotations
import copy
import json
import os

import arcade

from constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG
from core import content

FONT = "Courier New"
_MISSING = object()

RARITIES = ["common", "uncommon", "rare", "epic", "legendary"]
DAMAGE_TYPES = ["physical", "fire", "cold", "lightning", "poison", "holy", "none"]


class Field:
    def __init__(self, key: str, label: str, ftype: str, choices=None):
        self.key = key
        self.label = label
        self.ftype = ftype          # str int float bool color choice kvint
        self.choices = choices or []


class EditorConfig:
    def __init__(self, title, filename, is_dict, id_key, fields, template):
        self.title = title
        self.filename = filename
        self.is_dict = is_dict      # creatures.json is a dict keyed by id
        self.id_key = id_key        # synthetic "id" for dicts, real "name" for lists
        self.fields = fields
        self.template = template


# ── Editor schemas ───────────────────────────────────────

def _creature_editor() -> EditorConfig:
    fields = [
        Field("id", "id", "str"),
        Field("char", "char", "str"),
        Field("color", "color", "color"),
        Field("texture", "texture", "str"),
        Field("hp", "hp", "int"),
        Field("armor", "armor", "int"),
        Field("str", "str", "int"),
        Field("dex", "dex", "int"),
        Field("con", "con", "int"),
        Field("int", "int", "int"),
        Field("wis", "wis", "int"),
        Field("cha", "cha", "int"),
        Field("damage", "damage", "str"),
        Field("xp", "xp", "int"),
        Field("behavior", "behavior", "choice", ["aggressive", "guard", "boss", "passive"]),
        Field("aggro", "aggro range", "int"),
    ]
    template = {"id": "new_monster", "char": "x", "color": [200, 200, 200], "texture": "",
                "hp": 10, "armor": 0, "str": 10, "dex": 10, "con": 10, "int": 10,
                "wis": 10, "cha": 10, "damage": "1d4", "xp": 5,
                "behavior": "aggressive", "aggro": 5}
    return EditorConfig("Monster Editor", "creatures.json", True, "id", fields, template)


def _item_editor() -> EditorConfig:
    fields = [
        Field("name", "name", "str"),
        Field("kind", "kind", "choice", ["consumable", "ammo"]),
        Field("char", "char", "str"),
        Field("color", "color", "color"),
        Field("texture", "texture", "str"),
        Field("effect_type", "effect", "choice", ["food", "drink", "heal", "mana", "cure", ""]),
        Field("potency", "potency", "int"),
        Field("hunger_restore", "hunger+", "float"),
        Field("thirst_restore", "thirst+", "float"),
        Field("sleep_restore", "sleep+", "float"),
        Field("stress_reduce", "stress-", "float"),
        Field("willpower_restore", "willpower+", "float"),
        Field("hp_restore", "hp+", "int"),
        Field("mana_restore", "mana+", "int"),
        Field("ammo_type", "ammo type", "choice", ["", "arrow", "bolt"]),
        Field("qty_min", "qty min", "int"),
        Field("qty_max", "qty max", "int"),
        Field("value", "value", "int"),
        Field("weight", "weight", "float"),
        Field("rarity", "rarity", "choice", RARITIES),
        Field("min_depth", "min depth", "int"),
    ]
    template = {"name": "New Item", "kind": "consumable", "char": "?",
                "color": [200, 200, 200], "texture": "", "effect_type": "heal",
                "hp_restore": 10, "value": 5, "weight": 0.3,
                "rarity": "common", "min_depth": 1}
    return EditorConfig("Item Editor", "items.json", False, "name", fields, template)


def _equipment_editor() -> EditorConfig:
    fields = [
        Field("name", "name", "str"),
        Field("char", "char", "str"),
        Field("color", "color", "color"),
        Field("texture", "texture", "str"),
        Field("slot", "slot", "choice",
              ["weapon", "armor", "helmet", "shield", "gloves", "boots", "amulet", "ring", "talisman"]),
        Field("armor_bonus", "armor+", "int"),
        Field("damage_dice", "damage", "str"),
        Field("damage_type", "dmg type", "choice", DAMAGE_TYPES),
        Field("stat_bonuses", "stat bonuses", "kvint"),
        Field("special", "special", "str"),
        Field("ranged", "ranged", "bool"),
        Field("ammo_type", "ammo type", "choice", ["", "arrow", "bolt"]),
        Field("max_hp_bonus", "max hp+", "int"),
        Field("max_mana_bonus", "max mana+", "int"),
        Field("regen", "regen", "int"),
        Field("value", "value", "int"),
        Field("weight", "weight", "float"),
        Field("rarity", "rarity", "choice", RARITIES),
        Field("min_depth", "min depth", "int"),
    ]
    template = {"name": "New Equipment", "char": "/", "color": [200, 200, 200],
                "texture": "", "slot": "weapon", "damage_dice": "1d6",
                "value": 10, "weight": 2.0, "rarity": "common", "min_depth": 1}
    return EditorConfig("Weapon & Armor Editor", "equipment.json", False, "name", fields, template)


def _spell_editor() -> EditorConfig:
    fields = [
        Field("name", "name", "str"),
        Field("mana_cost", "mana cost", "int"),
        Field("range", "range", "int"),
        Field("effect_type", "effect", "choice", ["damage", "heal", "buff", "debuff", "utility"]),
        Field("potency", "potency", "int"),
        Field("damage_type", "dmg type", "choice", DAMAGE_TYPES),
        Field("description", "description", "str"),
    ]
    template = {"name": "New Spell", "mana_cost": 5, "range": 5, "effect_type": "damage",
                "potency": 10, "damage_type": "fire", "description": ""}
    return EditorConfig("Spell Editor", "spells.json", False, "name", fields, template)


EDITORS = {
    "item": _item_editor,
    "equipment": _equipment_editor,
    "creature": _creature_editor,
    "spell": _spell_editor,
}


# ── The editor view ──────────────────────────────────────

class EditorView(arcade.View):
    def __init__(self, config: EditorConfig):
        super().__init__()
        self.cfg = config
        self.records: list[dict] = []
        self.sel = 0                 # selected entry index
        self.field_idx = 0           # selected field index
        self.focus = "list"          # "list" or "fields"
        self.editing = False
        self.buffer = ""
        self.status = ""
        self.status_color = (150, 200, 150)
        self.dirty = False
        self.modal = None            # None | "delete" | "exit"
        self._load()

    # ── Load / save ─────────────────────────────────

    def _path(self) -> str:
        return os.path.join(content.DATA_DIR, self.cfg.filename)

    def _load(self):
        try:
            with open(self._path(), "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            data = {} if self.cfg.is_dict else []
            self._set_status(f"Could not load {self.cfg.filename}: {exc}", err=True)
        if self.cfg.is_dict:
            self.records = [{**copy.deepcopy(v), self.cfg.id_key: k} for k, v in data.items()]
        else:
            self.records = [copy.deepcopy(e) for e in data]
        self.dirty = False

    def _save(self):
        if self.cfg.is_dict:
            out = {}
            for rec in self.records:
                r = copy.deepcopy(rec)
                key = str(r.pop(self.cfg.id_key, "")) or "unnamed"
                out[key] = r
            payload = out
        else:
            payload = self.records
        try:
            with open(self._path(), "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
                f.write("\n")
        except OSError as exc:
            self._set_status(f"Save failed: {exc}", err=True)
            return False
        content.reload()
        self.dirty = False
        self._set_status(f"Saved {self.cfg.filename}  ({len(self.records)} entries) and reloaded.")
        return True

    # ── Helpers ─────────────────────────────────────

    def _set_status(self, msg, err=False):
        self.status = msg
        self.status_color = (220, 110, 110) if err else (150, 200, 150)

    def _cur(self) -> dict | None:
        if 0 <= self.sel < len(self.records):
            return self.records[self.sel]
        return None

    def _display_name(self, rec) -> str:
        return str(rec.get(self.cfg.id_key, "???"))

    def _field(self) -> Field | None:
        if 0 <= self.field_idx < len(self.cfg.fields):
            return self.cfg.fields[self.field_idx]
        return None

    @staticmethod
    def _fmt(fs: Field, value):
        if value is _MISSING:
            return "(unset)"
        if fs.ftype == "bool":
            return "yes" if value else "no"
        if fs.ftype == "color":
            try:
                r, g, b = value[:3]
                return f"[{r}, {g}, {b}]"
            except Exception:
                return str(value)
        if fs.ftype == "kvint":
            if not value:
                return "(none)"
            return ", ".join(f"{k}:{v}" for k, v in value.items())
        return str(value)

    @staticmethod
    def _edit_seed(fs: Field, value):
        if value is _MISSING:
            return ""
        if fs.ftype == "color":
            try:
                r, g, b = value[:3]
                return f"{r},{g},{b}"
            except Exception:
                return ""
        if fs.ftype == "kvint":
            return ", ".join(f"{k}:{v}" for k, v in (value or {}).items())
        return str(value)

    @staticmethod
    def _parse(fs: Field, text: str):
        text = text.strip()
        if fs.ftype == "int":
            return int(text)
        if fs.ftype == "float":
            return float(text)
        if fs.ftype == "color":
            parts = [int(p) for p in text.replace(" ", "").split(",") if p != ""]
            if len(parts) != 3 or any(not (0 <= p <= 255) for p in parts):
                raise ValueError("color needs r,g,b in 0-255")
            return parts
        if fs.ftype == "kvint":
            out = {}
            for chunk in text.split(","):
                chunk = chunk.strip()
                if not chunk:
                    continue
                k, _, v = chunk.partition(":")
                out[k.strip()] = int(v.strip())
            return out
        return text  # str

    # ── Input ───────────────────────────────────────

    def on_text(self, text):
        if self.editing:
            self.buffer += text

    def on_key_press(self, key, modifiers):
        # Modal prompts take precedence.
        if self.modal is not None:
            self._handle_modal(key)
            return

        if self.editing:
            self._handle_edit_key(key)
            return

        K = arcade.key
        if key == K.ESCAPE:
            if self.dirty:
                self.modal = "exit"
            else:
                self._exit()
            return
        if key == K.S:
            self._save()
            return
        if key in (K.TAB,):
            self.focus = "fields" if self.focus == "list" else "list"
            return

        if self.focus == "list":
            self._list_key(key)
        else:
            self._fields_key(key)

    def _list_key(self, key):
        K = arcade.key
        if key == K.UP:
            if self.records:
                self.sel = (self.sel - 1) % len(self.records)
        elif key == K.DOWN:
            if self.records:
                self.sel = (self.sel + 1) % len(self.records)
        elif key in (K.RIGHT, K.ENTER, K.RETURN):
            if self.records:
                self.focus = "fields"
                self.field_idx = 0
        elif key == K.A:
            self._add_entry()
        elif key == K.D:
            if self.records:
                self.modal = "delete"

    def _fields_key(self, key):
        K = arcade.key
        if key == K.UP:
            self.field_idx = (self.field_idx - 1) % len(self.cfg.fields)
        elif key == K.DOWN:
            self.field_idx = (self.field_idx + 1) % len(self.cfg.fields)
        elif key in (K.LEFT,):
            self.focus = "list"
        elif key in (K.X, K.DELETE):
            self._unset_field()
        elif key in (K.ENTER, K.RETURN):
            self._activate_field()

    def _activate_field(self):
        rec = self._cur()
        fs = self._field()
        if rec is None or fs is None:
            return
        if fs.ftype == "bool":
            rec[fs.key] = not rec.get(fs.key, False)
            self.dirty = True
        elif fs.ftype == "choice":
            cur = rec.get(fs.key, _MISSING)
            choices = fs.choices
            if cur in choices:
                nxt = choices[(choices.index(cur) + 1) % len(choices)]
            else:
                nxt = choices[0]
            rec[fs.key] = nxt
            self.dirty = True
        else:
            self.editing = True
            self.buffer = self._edit_seed(fs, rec.get(fs.key, _MISSING))
            self._set_status(f"Editing {fs.label} — ENTER to commit, ESC to cancel.")

    def _unset_field(self):
        rec = self._cur()
        fs = self._field()
        if rec is None or fs is None:
            return
        if fs.key == self.cfg.id_key:
            self._set_status("Can't unset the identifier field.", err=True)
            return
        if fs.key in rec:
            del rec[fs.key]
            self.dirty = True
            self._set_status(f"Unset {fs.label}.")

    def _handle_edit_key(self, key):
        K = arcade.key
        if key == K.BACKSPACE:
            self.buffer = self.buffer[:-1]
        elif key == K.ESCAPE:
            self.editing = False
            self._set_status("Edit cancelled.")
        elif key in (K.ENTER, K.RETURN):
            rec = self._cur()
            fs = self._field()
            if rec is None or fs is None:
                self.editing = False
                return
            try:
                rec[fs.key] = self._parse(fs, self.buffer)
                self.dirty = True
                self.editing = False
                self._set_status(f"Set {fs.label} = {self._fmt(fs, rec[fs.key])}")
            except ValueError as exc:
                self._set_status(f"Invalid {fs.label}: {exc}", err=True)

    def _handle_modal(self, key):
        K = arcade.key
        if self.modal == "delete":
            if key in (K.Y,):
                name = self._display_name(self._cur()) if self._cur() else "?"
                del self.records[self.sel]
                self.sel = max(0, min(self.sel, len(self.records) - 1))
                self.dirty = True
                self._set_status(f"Deleted '{name}'.")
                self.modal = None
            elif key in (K.N, K.ESCAPE):
                self.modal = None
        elif self.modal == "exit":
            if key in (K.S,):
                if self._save():
                    self.modal = None
                    self._exit()
            elif key in (K.D,):
                self.modal = None
                self._exit()
            elif key in (K.ESCAPE, K.N):
                self.modal = None

    def _add_entry(self):
        rec = copy.deepcopy(self.cfg.template)
        # Ensure a unique display id/name.
        base = str(rec.get(self.cfg.id_key, "new"))
        existing = {self._display_name(r) for r in self.records}
        name = base
        i = 2
        while name in existing:
            name = f"{base} {i}"
            i += 1
        rec[self.cfg.id_key] = name
        self.records.append(rec)
        self.sel = len(self.records) - 1
        self.focus = "fields"
        self.field_idx = 0
        self.dirty = True
        self._set_status(f"Added '{name}'. Edit its fields, then S to save.")

    def _exit(self):
        from views.title_view import TitleView
        self.window.show_view(TitleView())

    # ── Rendering ───────────────────────────────────

    def on_show_view(self):
        self.window.background_color = COLOR_BG

    def on_draw(self):
        self.clear()
        W, H = SCREEN_WIDTH, SCREEN_HEIGHT
        line_h = 22
        pane_top = H - 118
        footer_y = 34
        visible_rows = max(6, int((pane_top - footer_y - 28) / line_h))

        # Header
        dirty_mark = "  *unsaved*" if self.dirty else ""
        arcade.draw_text(self.cfg.title, 50, H - 52, (200, 170, 100), 26,
                         font_name=FONT, bold=True)
        arcade.draw_text(f"{self.cfg.filename}{dirty_mark}", 50, H - 82,
                         (210, 150, 90) if self.dirty else (130, 130, 140), 14, font_name=FONT)

        # ── List pane ──
        list_x = 50
        arcade.draw_text("ENTRIES", list_x, pane_top + 6, (150, 160, 180), 13,
                         font_name=FONT, bold=True)
        if not self.records:
            arcade.draw_text("(empty — press A to add)", list_x, pane_top - line_h,
                             (120, 120, 130), 14, font_name=FONT)
        start = self._scroll(self.sel, len(self.records), visible_rows)
        y = pane_top - line_h
        for i in range(start, min(start + visible_rows, len(self.records))):
            selected = (i == self.sel)
            if selected:
                hl = (60, 60, 40) if self.focus == "list" else (40, 40, 50)
                arcade.draw_lrbt_rectangle_filled(list_x - 8, list_x + 320, y - 4, y + 16, hl)
            col = (240, 220, 150) if selected else (170, 175, 185)
            arcade.draw_text(self._display_name(self.records[i])[:34], list_x, y, col, 14, font_name=FONT)
            y -= line_h
        if len(self.records) > visible_rows:
            arcade.draw_text(f"{self.sel + 1}/{len(self.records)}", list_x, footer_y + 4,
                             (120, 120, 130), 12, font_name=FONT)

        # Divider
        arcade.draw_lrbt_rectangle_filled(395, 397, footer_y, pane_top + 14, (50, 50, 60))

        # ── Fields pane ──
        fx = 420
        rec = self._cur()
        arcade.draw_text("FIELDS" + ("" if rec else " — select an entry"),
                         fx, pane_top + 6, (150, 160, 180), 13, font_name=FONT, bold=True)
        if rec is not None:
            fstart = self._scroll(self.field_idx, len(self.cfg.fields), visible_rows)
            y = pane_top - line_h
            for i in range(fstart, min(fstart + visible_rows, len(self.cfg.fields))):
                fs = self.cfg.fields[i]
                selected = (i == self.field_idx and self.focus == "fields")
                if selected:
                    arcade.draw_lrbt_rectangle_filled(fx - 8, W - 40, y - 4, y + 16, (40, 50, 65))
                label_col = (150, 200, 255) if selected else (140, 150, 165)
                arcade.draw_text(f"{fs.label:>14}", fx, y, label_col, 14, font_name=FONT)
                value = rec.get(fs.key, _MISSING)
                if self.editing and selected:
                    shown = self.buffer + "_"
                    arcade.draw_text(shown, fx + 200, y, (255, 240, 150), 14, font_name=FONT)
                else:
                    vcol = (120, 120, 130) if value is _MISSING else (220, 220, 210)
                    arcade.draw_text(self._fmt(fs, value), fx + 200, y, vcol, 14, font_name=FONT)
                    if fs.ftype == "color" and value is not _MISSING:
                        try:
                            r, g, b = value[:3]
                            arcade.draw_lrbt_rectangle_filled(fx + 360, fx + 392, y, y + 14, (r, g, b))
                        except Exception:
                            pass
                y -= line_h

        # ── Footer / status ──
        if self.modal == "delete":
            hint = f"Delete '{self._display_name(rec) if rec else '?'}'?   [Y] yes   [N] no"
            hint_col = (240, 160, 160)
        elif self.modal == "exit":
            hint = "Unsaved changes!   [S] save & exit   [D] discard & exit   [ESC] cancel"
            hint_col = (240, 200, 140)
        elif self.editing:
            hint = "TYPE to edit   BACKSPACE delete   ENTER commit   ESC cancel"
            hint_col = (200, 200, 150)
        elif self.focus == "list":
            hint = "↑/↓ select   ENTER/→ fields   A add   D delete   S save   ESC exit"
            hint_col = (140, 150, 160)
        else:
            hint = "↑/↓ field   ENTER edit/toggle   X unset   ← list   S save   ESC exit"
            hint_col = (140, 150, 160)
        arcade.draw_text(hint, 50, footer_y - 16, hint_col, 13, font_name=FONT)
        if self.status:
            arcade.draw_text(self.status, 50, H - 104, self.status_color, 13, font_name=FONT)

    @staticmethod
    def _scroll(index, total, visible):
        if total <= visible:
            return 0
        start = index - visible // 2
        return max(0, min(start, total - visible))
