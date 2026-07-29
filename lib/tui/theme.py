"""Amber phosphor cogitator theme for Textual."""
from __future__ import annotations

COGITATOR_CSS = """
Screen {
    background: #0a0a08;
    color: #e6b84d;
}

#header {
    dock: top;
    height: 3;
    background: #1a1408;
    color: #ffcc66;
    border: heavy #8a6a20;
    padding: 0 1;
    text-style: bold;
}

#warn-log {
    dock: bottom;
    height: 6;
    background: #120e06;
    border: solid #5a4010;
    color: #c99030;
    overflow-y: auto;
}

#main {
    padding: 1 2;
    overflow-y: auto;
    height: 1fr;
}

TextArea {
    background: #100c06;
    color: #ffe08a;
    height: 1fr;
    min-height: 8;
    margin-bottom: 1;
}

.title {
    text-style: bold;
    color: #ffcc66;
    height: auto;
    margin: 0 0 1 0;
}

.litany {
    color: #a07830;
    height: auto;
    margin: 0 0 1 0;
}

Button {
    background: #1a1408;
    color: #e6b84d;
    border: solid #8a6a20;
    margin: 0 1 1 0;
    min-width: 16;
    height: 3;
}

Button:hover {
    background: #2a2010;
    color: #ffe08a;
}

Button.-primary {
    background: #3a2810;
    border: heavy #c9a040;
}

.panel {
    border: solid #8a6a20;
    background: #100c06;
    padding: 1;
    margin: 0 0 1 0;
    height: auto;
}

.label {
    color: #c9a040;
}

.value {
    color: #ffe08a;
    text-style: bold;
}

/* Fixed control heights — Textual Select defaults to height:auto and overlaps Labels */
Screen Input {
    background: #0a0a08;
    border: solid #8a6a20;
    color: #ffe08a;
    height: 3;
    margin: 0 0 1 0;
    width: 1fr;
}

Screen Select {
    background: #0a0a08;
    border: none;
    color: #e6b84d;
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
    background: #0a0a08;
    /* solid not tall — tall borders inflate height and overlap Labels */
    border: solid #8a6a20 !important;
    color: #ffe08a;
    padding: 0 1 !important;
}

Screen Select:focus > SelectCurrent {
    border: solid #c9a040 !important;
}

SelectCurrent {
    height: 3 !important;
    max-height: 3;
    border: solid #8a6a20 !important;
    padding: 0 1 !important;
}

Screen Label {
    height: 1;
    min-height: 1;
    max-height: 1;
    margin: 1 0 0 0;
    color: #c9a040;
}

/* List rows are height 1 — Label top margin would push text out of the clip */
Screen ListItem > Label {
    height: 1;
    min-height: 1;
    max-height: 1;
    margin: 0;
    color: #ffe08a;
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
    border: solid #8a6a20;
    background: #100c06;
    height: 8;
    max-height: 8;
    margin: 0 0 1 0;
}

Screen ListItem {
    padding: 0 1;
    height: 1;
}

Screen ListItem:hover {
    background: #2a2010;
}

/* Vertical stacks inside scroll areas keep natural flow */
VerticalScroll {
    height: 1fr;
}

"""
