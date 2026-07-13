import streamlit as st


GLOBAL_CSS = """
<style>
:root {
--bg: #0e1117;
--panel: #111827;
--panel-soft: rgba(17, 24, 39, 0.94);
--scenario-panel: rgba(255,255,255,0.018);
--border: rgba(255,255,255,0.16);
--border-soft: rgba(255,255,255,0.10);
--text-muted: #a9a9a9;
--accent: #35aef5;
--danger: #f87171;
--success: #4ade80;
--warning: #facc15;
}

.block-container {
max-width: 100%;
padding-top: 324px;
padding-left: 255px;
padding-right: 48px;
padding-bottom: 235px;
}

header[data-testid="stHeader"] {
background: transparent;
}

.fixed-top,
.st-key-decision_launchpad_fixed {
position: fixed;
top: 0;
left: 0;
right: 0;
z-index: 1100;
background: var(--panel);
padding: 20px 48px 16px 255px;
border-bottom: 1px solid var(--border);
box-shadow: 0 10px 28px rgba(0,0,0,0.38);
}
.fixed-top h1,
.st-key-decision_launchpad_fixed h1 {
margin: 0;
padding: 0;
font-size: 2rem;
line-height: 1.1;
color: #ffffff;
letter-spacing: -0.025em;
}
.fixed-top p,
.st-key-decision_launchpad_fixed p {
margin-top: 0.45rem;
margin-bottom: 0.65rem;
color: var(--text-muted);
font-size: 0.95rem;
}
.decision-shell p {
margin-bottom: 0.65rem;
}
.decision-prompt {
font-size: 0.82rem;
letter-spacing: 0.08em;
text-transform: uppercase;
font-weight: 800;
color: var(--accent);
margin-bottom: 0.55rem;
}
.st-key-decision_launchpad_fixed [data-testid="stHorizontalBlock"] {
width: 100%;
}
.st-key-decision_launchpad_fixed [data-testid="column"] {
min-width: 0;
}
.decision-grid {
display: grid;
grid-template-columns: repeat(5, minmax(0, 1fr));
gap: 12px;
width: 100%;
}
.decision-card {
box-sizing: border-box;
height: 136px;
border-radius: 8px;
border: 1px solid rgba(53,174,245,0.22);
background: rgba(53,174,245,0.075);
color: #ffffff;
position: relative;
box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
}
.decision-card:hover {
border-color: rgba(53,174,245,0.58);
background: rgba(53,174,245,0.13);
}
.decision-card.active {
border-color: rgba(74,222,128,0.86);
background: linear-gradient(90deg, rgba(74,222,128,0.18), rgba(53,174,245,0.13));
color: #ffffff;
box-shadow: inset 4px 0 0 rgba(74,222,128,0.95), inset 0 1px 0 rgba(255,255,255,0.07);
}
.decision-entry {
box-sizing: border-box;
display: grid;
grid-template-columns: 28px minmax(0, 1fr) 16px;
align-items: center;
gap: 10px;
height: 100%;
min-height: inherit;
padding: 13px 12px;
color: #ffffff;
text-decoration: none;
}
.decision-entry:not(:has(.decision-entry-title)) {
display: none;
}
.decision-entry:hover {
color: #ffffff;
text-decoration: none;
}
div[class*="st-key-decision_card_"] {
position: relative;
height: 136px;
}
div[class*="st-key-decision_card_"] div[class*="st-key-decision_intent_"] {
position: absolute;
inset: 0;
z-index: 4;
height: 100%;
width: 100%;
}
div[class*="st-key-decision_card_"] .stButton {
position: static;
height: 100%;
}
div[class*="st-key-decision_card_"] .stButton button {
width: 100%;
height: 136px;
padding: 0;
border: 0;
border-radius: 8px;
background: transparent;
color: transparent;
box-shadow: none;
}
div[class*="st-key-decision_card_"] .stButton button [data-testid="stMarkdownContainer"],
div[class*="st-key-decision_card_"] .stButton button [data-testid="stMarkdownContainer"] p {
color: transparent;
font-size: 0;
line-height: 0;
margin: 0;
}
div[class*="st-key-decision_card_"] .stButton button:hover {
border: 0;
background: transparent;
color: transparent;
box-shadow: none;
}
div[class*="st-key-decision_card_"] .stButton button:focus-visible {
outline: 2px solid rgba(255,255,255,0.86);
outline-offset: -4px;
box-shadow: none;
}
.decision-icon {
display: flex;
align-items: center;
justify-content: center;
width: 28px;
height: 28px;
border-radius: 7px;
background: rgba(53,174,245,0.12);
color: var(--accent);
}
.decision-icon svg {
width: 18px;
height: 18px;
fill: none;
stroke: currentColor;
stroke-width: 1.9;
stroke-linecap: round;
stroke-linejoin: round;
}
.decision-entry-copy {
display: block;
min-width: 0;
position: relative;
}
.decision-entry-title {
display: block;
font-size: 0.98rem;
font-weight: 900;
line-height: 1.2;
margin-bottom: 0.3rem;
}
.decision-entry-support {
display: block;
color: #cfd8e3;
font-size: 0.76rem;
line-height: 1.35;
}
.decision-card.active .decision-entry-support {
color: #e7fff1;
}
.decision-card.active .decision-entry-title {
color: #ffffff;
padding-right: 0;
}
.decision-entry-marker {
position: absolute;
top: -3px;
right: 0;
border: 1px solid rgba(74,222,128,0.55);
border-radius: 999px;
padding: 2px 6px;
color: #dfffea;
font-size: 0.58rem;
font-weight: 900;
letter-spacing: 0.05em;
text-transform: uppercase;
}
.decision-card.active .decision-entry-copy {
padding-top: 0.7rem;
}
.decision-arrow {
color: rgba(207,216,227,0.62);
font-size: 1rem;
font-weight: 900;
line-height: 1;
text-align: right;
}
.decision-card.active .decision-arrow {
color: #dfffea;
}
.decision-mode-row {
display: flex;
align-items: center;
gap: 14px;
margin-top: 0.55rem;
flex-wrap: wrap;
}
.decision-mode {
border: 1px solid rgba(53,174,245,0.28);
border-radius: 8px;
background: rgba(53,174,245,0.075);
padding: 6px 9px;
color: #dcefff;
font-size: 0.84rem;
font-weight: 800;
}
.decision-mode span {
color: var(--accent);
text-transform: uppercase;
letter-spacing: 0.06em;
font-size: 0.72rem;
}
.decision-general-link {
color: #cfd8e3;
font-size: 0.82rem;
font-weight: 800;
text-decoration: none;
border-bottom: 1px solid rgba(207,216,227,0.36);
}
.decision-general-link:hover {
color: #ffffff;
border-bottom-color: var(--accent);
text-decoration: none;
}
.st-key-decision_intent_general button {
color: #cfd8e3;
font-size: 0.82rem;
font-weight: 800;
text-decoration: none;
border: 0;
border-bottom: 1px solid rgba(207,216,227,0.36);
border-radius: 0;
padding: 4px 2px;
min-height: 30px;
background: transparent;
}
.st-key-decision_intent_general button:hover {
color: #ffffff;
border-bottom-color: var(--accent);
background: transparent;
}

.workspace-guidance {
border: 1px solid rgba(53,174,245,0.22);
border-radius: 8px;
background: rgba(17,24,39,0.72);
box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
padding: 12px 14px 13px;
margin-bottom: 16px;
}
.workspace-guidance-kicker {
color: var(--accent);
font-size: 0.7rem;
font-weight: 900;
letter-spacing: 0.08em;
line-height: 1.2;
margin-bottom: 4px;
text-transform: uppercase;
}
.workspace-guidance-question {
color: #ffffff;
font-size: 1rem;
font-weight: 900;
line-height: 1.25;
margin-bottom: 10px;
}
.workspace-guidance-grid {
display: grid;
grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1.2fr);
gap: 10px;
}
.workspace-guidance-item {
border-left: 2px solid rgba(53,174,245,0.34);
color: #d6dee9;
font-size: 0.78rem;
line-height: 1.35;
padding-left: 9px;
}
.workspace-guidance-item span {
color: #ffffff;
display: block;
font-size: 0.68rem;
font-weight: 900;
letter-spacing: 0.06em;
line-height: 1.2;
margin-bottom: 3px;
text-transform: uppercase;
}
.workspace-guidance-evidence {
border-left-color: rgba(74,222,128,0.58);
}

@media (max-width: 1180px) and (min-width: 981px) {
.decision-grid {
grid-template-columns: repeat(5, minmax(0, 1fr));
gap: 9px;
}
.decision-card {
height: 140px;
}
div[class*="st-key-decision_card_"] {
height: 140px;
}
div[class*="st-key-decision_card_"] .stButton button {
height: 140px;
}
.decision-entry {
grid-template-columns: 24px minmax(0, 1fr) 12px;
gap: 7px;
padding: 11px 9px;
}
.decision-icon {
width: 24px;
height: 24px;
}
.decision-icon svg {
width: 16px;
height: 16px;
}
.decision-entry-title {
font-size: 0.9rem;
}
.decision-entry-support {
font-size: 0.7rem;
line-height: 1.32;
}
.workspace-guidance {
padding: 11px 12px 12px;
}
.workspace-guidance-grid {
gap: 8px;
}
.workspace-guidance-item {
font-size: 0.73rem;
}
.block-container {
padding-top: 332px;
}
}

@media (max-width: 980px) {
.block-container {
padding-top: 730px;
padding-left: 28px;
padding-right: 28px;
}
.fixed-top {
padding-left: 28px;
padding-right: 28px;
}
.st-key-decision_launchpad_fixed {
padding-left: 28px;
padding-right: 28px;
}
.decision-grid {
grid-template-columns: 1fr;
}
.decision-card {
height: 97px;
}
div[class*="st-key-decision_card_"] {
height: 97px;
}
div[class*="st-key-decision_card_"] .stButton button {
height: 97px;
}
.decision-entry-title {
font-size: 1.02rem;
}
.decision-entry-support {
font-size: 0.8rem;
}
.workspace-guidance {
padding: 12px;
}
.workspace-guidance-grid {
grid-template-columns: 1fr;
gap: 9px;
}
.workspace-guidance-question {
font-size: 0.96rem;
}
.fixed-left {
display: none;
}
}

.fixed-left {
position: fixed;
top: 284px;
left: 0;
bottom: 190px;
width: 210px;
z-index: 999;
background: var(--panel-soft);
border-right: 1px solid var(--border);
box-shadow: 10px 0 24px rgba(0,0,0,0.22);
padding: 24px 18px 24px 48px;
white-space: nowrap;
overflow: hidden;
}
@media (max-width: 1180px) and (min-width: 981px) {
.fixed-left {
top: 292px;
}
}
.fixed-left h3 {
margin-top: 0;
margin-bottom: 0.45rem;
font-size: 1.15rem;
}
.nav-note {
color: var(--text-muted);
font-size: 0.78rem;
margin-bottom: 1.15rem;
}
.nav-item {
margin: 0.85rem 0;
color: #d6d6d6;
font-size: 0.95rem;
}

.fixed-bottom {
position: fixed;
left: 210px;
right: 0;
bottom: 0;
z-index: 1000;
background: var(--panel);
padding: 14px 48px 16px 45px;
border-top: 1px solid var(--border);
box-shadow: 0 -10px 28px rgba(0,0,0,0.44);
}
.fixed-bottom h2 {
margin: 0 0 0.15rem 0;
padding: 0;
font-size: 1.35rem;
}
.bottom-caption {
color: var(--text-muted);
margin-bottom: 0.65rem;
font-size: 0.86rem;
}

.scenario-verdict {
background: rgba(53,174,245,0.08);
border: 1px solid rgba(53,174,245,0.18);
border-radius: 9px;
padding: 8px 11px;
margin: 0.55rem 0 0.75rem 0;
font-size: 0.86rem;
color: #dcefff;
}
.scenario-verdict b {
color: #ffffff;
}
.decision-context {
border: 1px solid rgba(53,174,245,0.28);
border-radius: 10px;
background: rgba(53,174,245,0.055);
padding: 10px 12px;
margin: 0.65rem 0 0.65rem 0;
}
.decision-context-title {
font-size: 0.72rem;
font-weight: 900;
letter-spacing: 0.1em;
text-transform: uppercase;
color: var(--accent);
margin-bottom: 0.25rem;
}
.decision-context-main {
font-size: 0.98rem;
font-weight: 900;
color: #ffffff;
margin-bottom: 0.25rem;
}
.decision-context-meta {
font-size: 0.82rem;
color: #d6d6d6;
line-height: 1.4;
}

.questions-card{
border:1px solid rgba(255,255,255,.12);
border-radius:10px;
padding:10px 12px;
background:rgba(255,255,255,.025);
margin:.65rem 0;
}
.questions-title{font-size:.72rem;font-weight:900;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:.3rem;}
.questions-list{color:#d6d6d6;font-size:.82rem;line-height:1.6;}

.diff-grid {
display: grid;
grid-template-columns: repeat(6, 1fr);
gap: 12px;
margin-bottom: 0.7rem;
}
.diff-card {
background: rgba(255,255,255,0.035);
border: 1px solid var(--border-soft);
border-radius: 9px;
padding: 9px 11px;
min-height: 68px;
}
.diff-label {
font-size: 0.76rem;
color: #cfcfcf;
margin-bottom: 0.15rem;
}
.diff-value {
font-size: 1.16rem;
font-weight: 700;
color: #ffffff;
line-height: 1.25;
}
.diff-positive {
color: var(--success);
font-size: 0.78rem;
margin-top: 0.15rem;
}
.diff-negative {
color: var(--danger);
font-size: 0.78rem;
margin-top: 0.15rem;
}
.diff-neutral {
color: var(--text-muted);
font-size: 0.78rem;
margin-top: 0.15rem;
}
.bottom-tabs {
display: flex;
gap: 10px;
margin-top: 0.45rem;
}
.bottom-tab {
padding: 6px 12px;
border-radius: 999px;
border: 1px solid rgba(255,255,255,0.18);
color: #d6d6d6;
font-size: 0.82rem;
}
.bottom-tab.active {
background: #ff4b4b;
color: white;
border-color: #ff4b4b;
}

.ride-title-card {
border-bottom: 1px solid var(--border);
margin-bottom: 1.25rem;
padding: 0 0 0.85rem 0;
}
.ride-title-card h2 {
margin: 0;
font-size: 2rem;
line-height: 1.05;
letter-spacing: -0.025em;
}
.ride-title-card p {
margin: 0.35rem 0 0 0;
color: var(--text-muted);
font-size: 0.95rem;
}
.section-divider {
margin: 2rem 0 1rem 0;
border-top: 1px solid var(--border);
}
.zone-label {
font-size: 0.82rem;
letter-spacing: 0.08em;
text-transform: uppercase;
color: var(--accent);
font-weight: 700;
margin-bottom: 0.45rem;
}

.input-note {
margin-bottom: 1rem;
color: var(--text-muted);
font-size: 0.82rem;
}

.comparison-label {
font-size: 0.82rem;
letter-spacing: 0.08em;
text-transform: uppercase;
color: var(--accent);
font-weight: 700;
margin-bottom: 0.45rem;
}

.zone-title-row {
display: flex;
align-items: baseline;
justify-content: space-between;
gap: 12px;
margin-bottom: 0.65rem;
}
.zone-subtitle {
color: var(--text-muted);
font-size: 0.82rem;
line-height: 1.45;
margin-bottom: 1rem;
}
.input-zone-marker,
.outcome-zone-marker {
font-size: 0.78rem;
letter-spacing: 0.12em;
text-transform: uppercase;
font-weight: 800;
color: var(--accent);
}
.input-zone-marker::before,
.outcome-zone-marker::before {
content: "";
display: inline-block;
width: 7px;
height: 7px;
border-radius: 999px;
background: var(--accent);
margin-right: 8px;
box-shadow: 0 0 12px rgba(53,174,245,0.55);
}

/* Visually separate assumptions from consequences. */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.input-zone-marker) {
background: linear-gradient(180deg, rgba(17,24,39,0.74), rgba(17,24,39,0.42));
border-color: rgba(255,255,255,0.16) !important;
box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 8px 24px rgba(0,0,0,0.14);
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.outcome-zone-marker) {
background: linear-gradient(180deg, rgba(21,33,48,0.78), rgba(21,33,48,0.48));
border-color: rgba(53,174,245,0.24) !important;
box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 8px 26px rgba(0,0,0,0.18);
}

/* Give major sections stronger rhythm inside each ride. */
div[data-testid="stVerticalBlockBorderWrapper"] h3 {
margin-top: 0.95rem;
}
div[data-testid="stVerticalBlockBorderWrapper"] h4 {
margin-top: 1.1rem;
margin-bottom: 0.55rem;
}

.briefing-grid {
display: grid;
grid-template-columns: repeat(2, minmax(0, 1fr));
gap: 10px;
margin-top: 0.75rem;
}
.briefing-card {
background: rgba(255,255,255,0.035);
border: 1px solid var(--border-soft);
border-radius: 8px;
padding: 10px 12px;
}
.briefing-label {
font-size: 0.76rem;
color: #cfcfcf;
margin-bottom: 0.15rem;
}
.briefing-value {
font-size: 1.2rem;
font-weight: 700;
color: white;
}
.briefing-note {
margin-top: 0.85rem;
color: var(--text-muted);
font-size: 0.82rem;
}

.recommendation-grid {
display: grid;
grid-template-columns: repeat(2, minmax(0, 1fr));
gap: 10px;
margin-top: 0.75rem;
}
.recommendation-card {
background: rgba(255,255,255,0.035);
border: 1px solid var(--border-soft);
border-radius: 8px;
padding: 10px 12px;
}
.recommendation-title {
font-weight: 800;
color: #ffffff;
margin-bottom: 0.45rem;
}
.recommendation-card ul {
margin: 0;
padding-left: 1.1rem;
color: #d6d6d6;
font-size: 0.84rem;
line-height: 1.45;
}
.recommendation-card li {
margin-bottom: 0.25rem;
}
.recommendation-note {
margin-top: 0.85rem;
color: var(--text-muted);
font-size: 0.82rem;
}


.performance-list {
margin-top: 0.75rem;
display: grid;
gap: 9px;
}
.performance-row {
background: rgba(255,255,255,0.035);
border: 1px solid var(--border-soft);
border-radius: 8px;
padding: 9px 11px;
}
.performance-head {
display: flex;
justify-content: space-between;
gap: 12px;
font-size: 0.84rem;
font-weight: 700;
color: #ffffff;
margin-bottom: 0.45rem;
}
.performance-value {
color: var(--accent);
white-space: nowrap;
}
.performance-track {
height: 7px;
border-radius: 999px;
background: rgba(255,255,255,0.10);
overflow: hidden;
}
.performance-fill {
height: 100%;
border-radius: 999px;
background: var(--accent);
}
.performance-insight {
margin-top: 0.85rem;
background: rgba(53, 174, 245, 0.10);
border: 1px solid rgba(53, 174, 245, 0.22);
border-radius: 8px;
padding: 10px 12px;
color: #dcefff;
font-size: 0.86rem;
line-height: 1.45;
}
.performance-note {
margin-top: 0.85rem;
color: var(--text-muted);
font-size: 0.82rem;
}


.opportunity-section-title {
margin-top: 1.2rem;
margin-bottom: 0.4rem;
font-weight: 800;
color: #ffffff;
}
.opportunity-grid {
display: grid;
grid-template-columns: repeat(2, minmax(0, 1fr));
gap: 10px;
margin-top: 0.7rem;
}
.opportunity-card {
background: rgba(53, 174, 245, 0.055);
border: 1px solid rgba(53, 174, 245, 0.18);
border-radius: 8px;
padding: 10px 12px;
position: relative;
overflow: hidden;
}
.opportunity-card.priority-1 {
border-color: rgba(74, 222, 128, 0.55);
background: linear-gradient(90deg, rgba(74, 222, 128, 0.12), rgba(53, 174, 245, 0.035));
}
.opportunity-card.priority-2 {
border-color: rgba(53, 174, 245, 0.42);
background: linear-gradient(90deg, rgba(53, 174, 245, 0.10), rgba(53, 174, 245, 0.035));
}
.opportunity-card.priority-low {
border-color: rgba(255,255,255,0.14);
background: rgba(255,255,255,0.025);
}
.opportunity-rank {
font-size: 0.72rem;
letter-spacing: 0.09em;
text-transform: uppercase;
color: var(--accent);
font-weight: 900;
margin-bottom: 0.35rem;
}
.opportunity-card.priority-1 .opportunity-rank {
color: #4ade80;
}
.opportunity-title {
font-size: 0.94rem;
font-weight: 900;
color: #ffffff;
margin-bottom: 0.25rem;
}
.opportunity-meta {
font-size: 0.82rem;
color: #d6d6d6;
line-height: 1.45;
}
.opportunity-decision-grid {
display: grid;
grid-template-columns: repeat(3, minmax(0, 1fr));
gap: 6px;
margin: 0.55rem 0;
}
.opportunity-pill {
border: 1px solid rgba(255,255,255,0.12);
border-radius: 7px;
padding: 6px 8px;
background: rgba(255,255,255,0.025);
}
.opportunity-pill-label {
font-size: 0.68rem;
color: var(--text-muted);
margin-bottom: 0.1rem;
}
.opportunity-pill-value {
font-size: 0.82rem;
font-weight: 900;
color: #ffffff;
}
.opportunity-score {
margin-top: 0.55rem;
font-size: 0.82rem;
color: #9ee7ff;
font-weight: 800;
}
.opportunity-focus {
border: 1px solid rgba(74, 222, 128, 0.42);
border-radius: 8px;
background: rgba(74, 222, 128, 0.08);
padding: 10px 12px;
margin-top: 0.55rem;
margin-bottom: 0.75rem;
}
.opportunity-focus-title {
font-size: 0.85rem;
font-weight: 900;
color: #4ade80;
margin-bottom: 0.2rem;
}
.opportunity-focus-main {
font-size: 1rem;
font-weight: 900;
color: #ffffff;
margin-bottom: 0.2rem;
}
.opportunity-portfolio-grid {
display: grid;
grid-template-columns: repeat(2, minmax(0, 1fr));
gap: 10px;
margin-top: 0.7rem;
}
.opportunity-note {
margin-top: 0.85rem;
color: var(--text-muted);
font-size: 0.82rem;
}


.upgrade-section-title {
margin-top: 1.25rem;
margin-bottom: 0.55rem;
font-weight: 900;
color: #ffffff;
}
.upgrade-advisor-grid {
display: grid;
grid-template-columns: repeat(3, minmax(0, 1fr));
gap: 10px;
margin-top: 0.65rem;
}
.upgrade-card {
border: 1px solid rgba(255,255,255,0.14);
border-radius: 10px;
padding: 12px;
background: rgba(255,255,255,0.025);
}
.upgrade-card.best {
border-color: rgba(74, 222, 128, 0.55);
background: linear-gradient(90deg, rgba(74, 222, 128, 0.12), rgba(53, 174, 245, 0.03));
}
.upgrade-card.second {
border-color: rgba(53, 174, 245, 0.45);
background: linear-gradient(90deg, rgba(53, 174, 245, 0.10), rgba(53, 174, 245, 0.025));
}
.upgrade-card.third {
border-color: rgba(255,255,255,0.18);
}
.upgrade-rank {
font-size: 0.78rem;
font-weight: 900;
letter-spacing: 0.08em;
text-transform: uppercase;
color: var(--accent);
margin-bottom: 0.35rem;
}
.upgrade-card.best .upgrade-rank {
color: #4ade80;
}
.upgrade-title {
font-size: 1.05rem;
font-weight: 900;
color: #ffffff;
margin-bottom: 0.25rem;
}
.upgrade-gain {
font-size: 1.25rem;
font-weight: 900;
color: #9ee7ff;
margin-bottom: 0.55rem;
}
.upgrade-meta-grid {
display: grid;
grid-template-columns: repeat(3, minmax(0, 1fr));
gap: 6px;
margin-bottom: 0.65rem;
}
.upgrade-meta-pill {
border: 1px solid rgba(255,255,255,0.12);
border-radius: 7px;
padding: 6px 7px;
background: rgba(0,0,0,0.12);
}
.upgrade-meta-label {
font-size: 0.66rem;
color: var(--text-muted);
margin-bottom: 0.1rem;
}
.upgrade-meta-value {
font-size: 0.78rem;
font-weight: 900;
color: #ffffff;
}
.upgrade-actions-title {
font-size: 0.78rem;
font-weight: 900;
color: #ffffff;
margin-top: 0.45rem;
margin-bottom: 0.25rem;
}
.upgrade-actions {
margin: 0.2rem 0 0 1rem;
padding: 0;
font-size: 0.8rem;
line-height: 1.45;
color: #d6d6d6;
}
.upgrade-actions li {
margin-bottom: 0.15rem;
}
.upgrade-note {
margin-top: 0.75rem;
font-size: 0.82rem;
color: var(--text-muted);
}


.placeholder-block {
margin-top: 1rem;
padding: 10px 12px;
border: 1px dashed rgba(255,255,255,0.16);
border-radius: 8px;
color: var(--text-muted);
font-size: 0.86rem;
}

/* Make scenario columns feel like two separate dashboards. */
div[data-testid="column"]:has(.ride-title-card) {
background: var(--scenario-panel);
border: 1px solid rgba(255,255,255,0.07);
border-radius: 12px;
padding: 18px 22px 28px 22px;
box-shadow: inset 0 1px 0 rgba(255,255,255,0.025);
}

/* Subtle center divider between Ride A and Ride B. */
div[data-testid="column"]:has(.ride-title-card):first-of-type {
border-right: 1px solid rgba(255,255,255,0.18);
}

.stSlider, .stSelectbox {
margin-bottom: 0.55rem;
}

.route-intelligence-grid {
display: grid;
grid-template-columns: repeat(4, 1fr);
gap: 8px;
margin: 0.75rem 0 0.35rem 0;
}

.route-intelligence-card {
border: 1px solid var(--border-soft);
border-radius: 8px;
padding: 0.65rem;
background: rgba(53,174,245,0.035);
}

.route-intelligence-section-title {
color: var(--accent);
font-size: 0.78rem;
font-weight: 800;
letter-spacing: 0.11rem;
text-transform: uppercase;
margin-top: 0.95rem;
margin-bottom: 0.35rem;
}

.route-intelligence-wide-card {
border: 1px solid var(--border-soft);
border-radius: 8px;
padding: 0.75rem;
background: rgba(53,174,245,0.045);
margin: 0.75rem 0 0.35rem 0;
}

.route-intelligence-subtle {
color: var(--text-muted);
font-size: 0.82rem;
margin-top: 0.3rem;
}

.route-intelligence-empty {
border: 1px dashed var(--border);
border-radius: 8px;
padding: 0.75rem;
color: var(--text-muted);
background: rgba(255,255,255,0.025);
margin-top: 0.75rem;
}

.route-intelligence-note {
color: var(--text-muted);
font-size: 0.82rem;
margin-bottom: 1rem;
}

/* Phase 12.4 — comparison becomes a document-flow decision workspace. */
.block-container {
padding-bottom: 142px;
}

.fixed-left {
bottom: 104px;
}

.decision-workspace {
margin-top: 28px;
padding-top: 24px;
border-top: 1px solid var(--border);
}

.investigation-step,
.workspace-layer-label {
font-size: 0.72rem;
font-weight: 900;
letter-spacing: 0.11em;
text-transform: uppercase;
color: var(--accent);
}

.investigation-question {
font-size: 1.15rem;
font-weight: 850;
line-height: 1.35;
color: #ffffff;
margin: 0.3rem 0 1rem;
}

.decision-summary-card {
border: 1px solid rgba(53,174,245,0.5);
border-radius: 14px;
background: linear-gradient(135deg, rgba(53,174,245,0.16), rgba(17,24,39,0.86));
box-shadow: inset 4px 0 0 var(--accent), 0 14px 34px rgba(0,0,0,0.2);
padding: 22px 24px;
}

.decision-summary-verdict {
font-size: 1.28rem;
line-height: 1.48;
color: #eef8ff;
margin-top: 0.35rem;
max-width: 1050px;
}

.decision-summary-verdict b {
color: #ffffff;
}

.evidence-section {
margin-top: 24px;
}

.evidence-focus {
font-size: 0.9rem;
font-weight: 800;
color: #ffffff;
margin: 0.35rem 0 0.75rem;
}

.decision-workspace .diff-grid {
grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
gap: 12px;
margin: 0;
}

.decision-workspace .diff-card {
min-height: 112px;
padding: 12px 14px;
transition: border-color 120ms ease, background 120ms ease;
}

.decision-workspace .diff-card.evidence-primary {
border-color: rgba(74,222,128,0.55);
background: linear-gradient(145deg, rgba(74,222,128,0.12), rgba(53,174,245,0.05));
box-shadow: inset 0 3px 0 rgba(74,222,128,0.75);
}

.decision-workspace .diff-card.evidence-balanced {
border-color: rgba(53,174,245,0.34);
background: rgba(53,174,245,0.055);
}

.decision-workspace .diff-card.evidence-secondary {
opacity: 0.82;
}

.evidence-rank {
font-size: 0.64rem;
font-weight: 900;
letter-spacing: 0.08em;
text-transform: uppercase;
color: var(--text-muted);
margin-bottom: 0.45rem;
}

.evidence-primary .evidence-rank {
color: var(--success);
}

.evidence-balanced .evidence-rank {
color: var(--accent);
}

.modeled-gain-card {
grid-column: span 2;
}

.next-action-card {
border: 1px solid rgba(74,222,128,0.48);
border-radius: 12px;
background: linear-gradient(110deg, rgba(74,222,128,0.12), rgba(17,24,39,0.72));
padding: 18px 20px;
margin-top: 24px;
}

.next-action-card .workspace-layer-label {
color: var(--success);
}

.next-action-question {
font-size: 0.82rem;
color: #bfeecf;
margin-top: 0.5rem;
}

.next-action-copy {
font-size: 1.16rem;
font-weight: 900;
line-height: 1.4;
color: #ffffff;
margin-top: 0.2rem;
}

.next-action-source {
font-size: 0.74rem;
color: var(--text-muted);
margin-top: 0.55rem;
}

/* Live Decision Bar — persistent experiment feedback using existing outputs. */
.live-decision-bar {
position: fixed;
left: 235px;
right: 48px;
bottom: max(12px, env(safe-area-inset-bottom));
z-index: 1050;
display: flex;
align-items: stretch;
gap: 0;
min-height: 76px;
border: 1px solid rgba(53,174,245,0.42);
border-radius: 12px;
background: rgba(11,17,27,0.97);
box-shadow: 0 -8px 30px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06);
backdrop-filter: blur(14px);
overflow: hidden;
}

.live-decision-identity {
display: flex;
flex-direction: column;
justify-content: center;
flex: 0 0 auto;
padding: 11px 14px;
border-right: 1px solid rgba(255,255,255,0.1);
background: rgba(53,174,245,0.08);
}

.live-decision-identity span {
color: var(--success);
font-size: 0.64rem;
font-weight: 950;
letter-spacing: 0.13em;
text-transform: uppercase;
}

.live-decision-identity strong {
color: #ffffff;
font-size: 0.78rem;
line-height: 1.2;
white-space: nowrap;
}

.live-decision-signals {
display: flex;
align-items: stretch;
min-width: 0;
overflow-x: auto;
scrollbar-width: thin;
}

.live-decision-signal {
display: flex;
flex: 0 0 auto;
flex-direction: column;
justify-content: center;
min-width: 112px;
max-width: 210px;
padding: 10px 14px;
border-right: 1px solid rgba(255,255,255,0.075);
}

.live-decision-outcome {
min-width: 210px;
background: linear-gradient(90deg, rgba(74,222,128,0.1), rgba(53,174,245,0.055));
}

.live-decision-label {
color: var(--text-muted);
font-size: 0.62rem;
font-weight: 850;
letter-spacing: 0.055em;
line-height: 1.2;
text-transform: uppercase;
white-space: nowrap;
}

.live-decision-value {
color: #ffffff;
font-size: 0.84rem;
font-weight: 850;
line-height: 1.25;
margin-top: 4px;
white-space: nowrap;
}

.live-decision-outcome .live-decision-value {
color: #e5ffed;
font-size: 0.94rem;
}

.live-decision-link {
display: flex;
align-items: center;
justify-content: center;
flex: 0 0 auto;
padding: 10px 13px;
color: #b8e6ff;
font-size: 0.7rem;
font-weight: 850;
line-height: 1.25;
text-align: center;
text-decoration: none;
white-space: nowrap;
}

.live-decision-link:hover {
background: rgba(53,174,245,0.1);
color: #ffffff;
text-decoration: none;
}

.live-decision-empty {
display: flex;
align-items: center;
flex: 1 1 auto;
padding: 10px 18px;
color: #d4dbe5;
font-size: 0.88rem;
font-weight: 750;
}

.live-decision-bar.is-inactive {
border-color: rgba(255,255,255,0.2);
}

.live-decision-bar.is-inactive .live-decision-identity span {
color: var(--text-muted);
}

.experiment-workspace-heading {
margin: 30px 0 14px;
padding-top: 22px;
border-top: 1px solid var(--border);
}

.experiment-workspace-copy {
margin-top: 0.35rem;
color: var(--text-muted);
font-size: 0.86rem;
}

@media (max-width: 980px) {
.block-container {
padding-bottom: 132px;
}
.st-key-decision_launchpad_fixed {
position: absolute;
}
.decision-workspace {
margin-top: 22px;
padding-top: 20px;
}
.decision-summary-card {
padding: 18px;
}
.decision-summary-verdict {
font-size: 1.08rem;
}
.decision-workspace .diff-grid {
grid-template-columns: repeat(2, minmax(0, 1fr));
gap: 9px;
}
.modeled-gain-card {
grid-column: span 2;
}
.live-decision-bar {
left: 14px;
right: 14px;
bottom: max(10px, env(safe-area-inset-bottom));
min-height: 70px;
}
.live-decision-identity {
padding: 9px 11px;
}
.live-decision-identity strong {
display: none;
}
.live-decision-outcome {
min-width: 190px;
}
.live-decision-signal {
min-width: 104px;
padding: 9px 11px;
}
.live-decision-link {
padding: 8px 10px;
}
}

@media (max-width: 560px) {
.decision-workspace .diff-grid {
grid-template-columns: 1fr;
}
.modeled-gain-card {
grid-column: span 1;
}
.next-action-card {
padding: 16px;
}
.live-decision-bar {
left: 8px;
right: 8px;
}
.live-decision-identity {
padding: 8px;
}
.live-decision-outcome {
min-width: 176px;
}
.live-decision-link {
font-size: 0;
padding: 8px 9px;
}
.live-decision-link::after {
content: "↑";
font-size: 0.9rem;
}
}

</style>
"""


def render_html(html: str) -> None:
    """Render raw HTML without leading indentation so Streamlit does not treat it as code."""
    cleaned = "\n".join(line.strip() for line in html.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


def inject_global_styles() -> None:
    render_html(GLOBAL_CSS)
