"""Amber→green phosphor theme for Textual (CRT cogitator)."""
from __future__ import annotations

COGITATOR_CSS = """
Screen {
    background: #050a06;
    color: #33ff66;
}

#header {
    dock: top;
    height: 3;
    background: #0a1810;
    color: #66ff99;
    border: heavy #2a8040;
    padding: 0 1;
    text-style: bold;
}

#warn-log {
    dock: bottom;
    height: 6;
    background: #081208;
    border: solid #1a5028;
    color: #2a9960;
    overflow-y: auto;
}

#main {
    padding: 1 2;
    overflow-y: auto;
    height: 1fr;
}

TextArea {
    background: #081008;
    color: #b8ffd0;
    height: 1fr;
    min-height: 8;
    margin-bottom: 1;
}

.title {
    text-style: bold;
    color: #66ff99;
    height: auto;
    margin: 0 0 1 0;
}

.litany {
    color: #3a9960;
    height: auto;
    margin: 0 0 1 0;
}

Button {
    background: #0a1810;
    color: #33ff66;
    border: solid #2a8040;
    margin: 0 1 1 0;
    min-width: 16;
    height: 3;
}

Button:hover {
    background: #143020;
    color: #b8ffd0;
}

Button.-primary {
    background: #1a4030;
    border: heavy #40c070;
}

.panel {
    border: solid #2a8040;
    background: #081008;
    padding: 1;
    margin: 0 0 1 0;
    height: auto;
}

.label {
    color: #40c070;
}

.value {
    color: #b8ffd0;
    text-style: bold;
}

/* Fixed control heights — Textual Select defaults to height:auto and overlaps Labels */
Screen Input {
    background: #050a06;
    border: solid #2a8040;
    color: #b8ffd0;
    height: 3;
    margin: 0 0 1 0;
    width: 1fr;
}

Screen Select {
    background: #050a06;
    border: none;
    color: #33ff66;
    height: 3 !important;
    max-height: 3;
    min-height: 3;
    margin: 0 0 1 0;
    width: 1fr;
}

Screen Select > SelectCurrent {
    height: 3 !important;
    max-height: 3;
    min-height: 3;
    background: #050a06;
    /* solid not tall — tall borders inflate height and overlap Labels */
    border: solid #2a8040 !important;
    color: #b8ffd0;
    padding: 0 1 !important;
}

Screen Select:focus > SelectCurrent {
    border: solid #40c070 !important;
}

SelectCurrent {
    height: 3 !important;
    max-height: 3;
    border: solid #2a8040 !important;
    padding: 0 1 !important;
}

Screen Label {
    height: 1;
    min-height: 1;
    max-height: 1;
    margin: 1 0 0 0;
    color: #40c070;
}

/* List rows are height 1 — Label top margin would push text out of the clip */
Screen ListItem > Label {
    height: 1;
    min-height: 1;
    max-height: 1;
    margin: 0;
    color: #b8ffd0;
}

/* Pipeline form rows — do not apply to header / docked chrome */
#main Horizontal,
VerticalScroll > Horizontal {
    height: 3;
    min-height: 3;
    max-height: 3;
    margin: 0 0 1 0;
    align: left middle;
}

#main Horizontal.-toolbar,
VerticalScroll > Horizontal.-toolbar {
    height: auto;
    max-height: 8;
    min-height: 3;
}

Screen ListView {
    border: solid #2a8040;
    background: #081008;
    height: 8;
    max-height: 8;
    margin: 0 0 1 0;
}

Screen ListItem {
    padding: 0 1;
    height: 1;
}

Screen ListItem:hover {
    background: #143020;
}

/* Vertical stacks inside scroll areas keep natural flow */
VerticalScroll {
    height: 1fr;
}

"""
