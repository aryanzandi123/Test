"""
Visualizer with original styling & behavior restored, plus:
- De-densified layout (spacing, charge, collision)
- Header/search matches index styles (title centered, round search bar)
- Nodes: dark circles + WHITE labels (as before)
- Legend restored
- Modals match original styling; two distinct modal paths:
  (1) Interaction (main ↔ interactor) when clicking the interactor link/ circle
  (2) Function (interactor → function) when clicking the function link/box
- Function confidence labels on boxes (as before)
- Arrows: pointer on hover + thicker on hover
- Function boxes connect ONLY to their interactor (never to main)
- Progress bar on viz page updated using your exact IDs
- Snapshot hydrated with ctx_json for complete function/evidence details
- Expand-on-click preserved; depth limit = 3
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
import tempfile

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>ProPath - PLACEHOLDER_MAIN</title>
  <link rel="stylesheet" href="/static/styles.css"/>
  <script src="/static/script.js"></script>
  <script src="https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js"></script>
  <style>
    /* ===============================================================
       DESIGN SYSTEM - Typography-Focused Scientific UI
       =============================================================== */

    :root {
      /* -----------------------------------------------------------
         TYPOGRAPHY SYSTEM
         ----------------------------------------------------------- */
      --font-serif: 'Charter', 'Georgia', 'Cambria', serif;
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;

      /* Type Scale */
      --text-xs: 0.75rem;      /* 12px - tiny labels, metadata */
      --text-sm: 0.875rem;     /* 14px - table cells, captions, secondary */
      --text-base: 1rem;       /* 16px - body text, descriptions */
      --text-lg: 1.125rem;     /* 18px - emphasized body, subsection headers */
      --text-xl: 1.25rem;      /* 20px - small headings */
      --text-2xl: 1.5rem;      /* 24px - section headings, modal titles */
      --text-3xl: 2.25rem;     /* 36px - page titles */

      /* Line Heights */
      --leading-tight: 1.25;
      --leading-normal: 1.5;
      --leading-relaxed: 1.625;

      /* -----------------------------------------------------------
         COLOR SYSTEM - LIGHT MODE (Default)
         ----------------------------------------------------------- */
      --color-bg-primary: #ffffff;
      --color-bg-secondary: #f8f9fa;
      --color-bg-tertiary: #f3f4f6;
      --color-bg-elevated: #ffffff;

      --color-text-primary: #1a202c;
      --color-text-secondary: #6b7280;
      --color-text-tertiary: #9ca3af;
      --color-text-inverse: #ffffff;

      --color-border-subtle: #e5e7eb;
      --color-border-medium: #d1d5db;
      --color-border-strong: #9ca3af;

      /* Accent Colors */
      --color-accent-primary: #4f46e5;
      --color-accent-info: #3b82f6;

      /* Interaction Colors - Light Mode */
      --color-activation: #059669;
      --color-activation-light: #d1fae5;
      --color-activation-dark: #047857;
      --color-inhibition: #dc2626;
      --color-inhibition-light: #fee2e2;
      --color-inhibition-dark: #b91c1c;
      --color-binding: #6b7280;
      --color-binding-light: #f3f4f6;
      --color-binding-dark: #6d28d9;

      /* Semantic Colors */
      --color-warning: #f59e0b;
      --color-success: #10b981;
      --color-error: #ef4444;

      /* -----------------------------------------------------------
         SPACING SCALE (8px base unit)
         ----------------------------------------------------------- */
      --space-1: 0.25rem;   /* 4px */
      --space-2: 0.5rem;    /* 8px */
      --space-3: 0.75rem;   /* 12px */
      --space-4: 1rem;      /* 16px */
      --space-6: 1.5rem;    /* 24px */
      --space-8: 2rem;      /* 32px */
      --space-12: 3rem;     /* 48px */

      /* -----------------------------------------------------------
         COMPONENT STANDARDS
         ----------------------------------------------------------- */
      --radius-sm: 4px;
      --radius-md: 6px;
      --radius-lg: 8px;
      --radius-xl: 12px;

      /* Shadows */
      --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
      --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
      --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);

      /* Transitions */
      --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
      --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
      --transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);
      --transition-spring: 400ms cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    /* -----------------------------------------------------------
       DARK MODE COLOR OVERRIDES
       Pure blacks and grays - NO blue/indigo tints
       ----------------------------------------------------------- */
    body.dark-mode {
      /* Base Colors - Pure black backgrounds */
      --color-bg-primary: #000000;
      --color-bg-secondary: #0a0a0a;
      --color-bg-tertiary: #1a1a1a;
      --color-bg-elevated: #242424;

      /* Text Colors - High contrast whites and grays */
      --color-text-primary: #f5f5f5;
      --color-text-secondary: #a3a3a3;
      --color-text-tertiary: #737373;
      --color-text-inverse: #0a0a0a;

      /* Borders - Neutral grays */
      --color-border-subtle: #262626;
      --color-border-medium: #404040;
      --color-border-strong: #525252;

      /* Accent Colors - Neutral light gray (no blue) */
      --color-accent-primary: #d4d4d4;
      --color-accent-info: #a3a3a3;

      /* Interaction Colors - HIGH CONTRAST */
      /* Green: Bright, clearly green */
      --color-activation: #22c55e;
      --color-activation-light: #065f46;
      --color-activation-dark: #16a34a;

      /* Red: DARK RED for clear distinction */
      --color-inhibition: #dc2626;
      --color-inhibition-light: #7f1d1d;
      --color-inhibition-dark: #991b1b;

      /* Purple: Keep as-is */
      --color-binding: #a78bfa;
      --color-binding-light: #4c1d95;
      --color-binding-dark: #8b5cf6;

      /* Semantic Colors - Dark Mode */
      --color-warning: #fbbf24;
      --color-success: #22c55e;
      --color-error: #dc2626;

      /* Shadows - Dark Mode */
      --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.5);
      --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.5);
      --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.5);
    }

    /* ===============================================================
       CORE LAYOUT & TYPOGRAPHY
       =============================================================== */
    *{margin:0;padding:0;box-sizing:border-box}
    body{
      font-family: var(--font-sans);
      background: var(--color-bg-secondary);
      color: var(--color-text-primary);
      min-height: 100vh;
      transition: background var(--transition-slow) ease, color var(--transition-slow) ease;
    }
    body.table-view-active{
      overflow-y:auto;
    }
    body.graph-view-active{
      height:100vh; overflow:hidden;
    }
    body.dark-mode .header {
      background: #1a1a1a;
      border-bottom: 2px solid #404040;
      box-shadow: 0 1px 3px rgba(0,0,0,.3);
    }
    body.dark-mode .title {
      color: #f5f5f5;
    }
    body.dark-mode .subtitle {
      color: #a3a3a3;
    }
    body.dark-mode #protein-input {
      background: #262626;
      border-color: #404040;
      color: #f5f5f5;
    }
    body.dark-mode #network {
      background: #1a1a1a;
      border-color: #404040;
    }
    body.dark-mode .view-container {
      background: #0a0a0a;
    }
    body.dark-mode .controls {
      background: #1a1a1a;
      border-color: #262626;
    }
    body.dark-mode .control-btn {
      background: #262626;
      border-color: #404040;
      color: #d4d4d4;
    }
    body.dark-mode .control-btn:hover {
      background: #404040;
      border-color: #525252;
    }
    body.dark-mode .control-divider {
      background: #404040;
    }
    body.dark-mode .graph-filter-btn {
      background: #262626;
    }
    body.dark-mode .filter-label {
      color: #a3a3a3;
    }
    body.dark-mode .main-node {
      fill: #404040;
      stroke: #525252;
    }
    body.dark-mode .interactor-node {
      fill: #262626;
      stroke: #404040;
    }
    body.dark-mode .node-label {
      fill: #f5f5f5;
    }
    body.dark-mode .modal-content {
      background: #1a1a1a;
      color: #e5e5e5;
    }
    body.dark-mode .modal-title {
      color: #f5f5f5;
    }
    body.dark-mode .info-label {
      color: #a3a3a3;
    }
    body.dark-mode .info-value {
      color: #e5e5e5;
    }
    body.dark-mode .view-tabs {
      background: #1a1a1a;
    }
    body.dark-mode .tab-btn {
      background: #262626;
      color: #d4d4d4;
    }
    body.dark-mode .tab-btn.active {
      background: #4f46e5;
      color: #fff;
    }
    body.dark-mode .data-table {
      background: #1a1a1a;
    }
    body.dark-mode .data-table thead {
      background: linear-gradient(90deg, #1a1a1a 0%, #262626 100%);
    }
    body.dark-mode .data-table th {
      color: #f5f5f5;
    }
    body.dark-mode .data-table td {
      color: #e5e5e5;
      border-bottom-color: #262626;
    }
    body.dark-mode .data-table tbody tr {
      background: #1a1a1a;
    }
    body.dark-mode .data-table tbody tr:hover {
      background: #262626;
    }
    body.dark-mode .data-table tbody tr.function-row {
      background: #1a1a1a;
    }
    /* Dark mode - NEW clean text styles */
    body.dark-mode .interaction-text {
      color: #e5e5e5;
    }
    body.dark-mode .interaction-arrow-activates {
      color: #10b981;
    }
    body.dark-mode .interaction-arrow-inhibits {
      color: #ef4444;
    }
    body.dark-mode .interaction-arrow-binds {
      color: #a78bfa;
    }
    body.dark-mode .interaction-subtitle {
      color: #9ca3af;
    }
    body.dark-mode .function-text {
      color: #e5e5e5;
    }
    body.dark-mode .effect-text-activates {
      color: #10b981;
    }
    body.dark-mode .effect-text-inhibits {
      color: #ef4444;
    }
    body.dark-mode .effect-text-binds {
      color: #a78bfa;
    }
    body.dark-mode .effect-type-text {
      color: #d4d4d4;
    }
    body.dark-mode .mechanism-text {
      color: #fbbf24;
    }
    /* OLD styles for backward compatibility */
    body.dark-mode .interaction-name {
      color: #f5f5f5;
    }
    body.dark-mode .expanded-section {
      background: #262626;
      border-color: #404040;
      box-shadow: 0 1px 3px rgba(99, 102, 241, 0.15);
    }
    body.dark-mode .expanded-section:hover {
      box-shadow: 0 2px 6px rgba(99, 102, 241, 0.2);
    }
    /* Dark mode - NEW clean expanded content styles */
    body.dark-mode .effect-type-description,
    body.dark-mode .mechanism-description,
    body.dark-mode .cellular-process-text {
      color: #d4d4d4;
    }
    body.dark-mode .cascade-list-item,
    body.dark-mode .effects-list-item {
      background: #1a1a1a;
      color: #d4d4d4;
      border-left-color: #f59e0b;
    }
    body.dark-mode .cascade-list-item::before {
      color: #fbbf24;
    }
    body.dark-mode .effects-list-item {
      border-left-color: #06b6d4;
    }
    body.dark-mode .effects-list-item::before {
      color: #06b6d4;
    }
    body.dark-mode .expanded-evidence-card {
      background: #1a1a1a;
      border-color: #404040;
      border-left-color: #6366f1;
      box-shadow: 0 1px 3px rgba(99, 102, 241, 0.2);
    }
    body.dark-mode .expanded-evidence-card:hover {
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
      border-left-color: #8b5cf6;
    }
    body.dark-mode .expanded-section--prominent {
      background: #2a2a2a;
      border-color: #404040;
      box-shadow: 0 1px 4px rgba(99, 102, 241, 0.15);
    }
    body.dark-mode .expanded-section-title {
      color: #f5f5f5;
      border-bottom-color: #262626;
    }
    body.dark-mode .table-controls {
      background: #1a1a1a;
      border-color: #262626;
    }
    body.dark-mode .table-search-input {
      background: #262626;
      border-color: #404040;
      color: #f5f5f5;
    }
    body.dark-mode #table-search-btn {
      background: #262626;
      color: #d4d4d4;
    }
    body.dark-mode .expanded-effect-wrapper {
      background: #1a1a1a;
      box-shadow: 0 3px 8px rgba(0, 0, 0, 0.3);
    }
    body.dark-mode .expanded-effect-wrapper.effect-activates {
      background: #064e3b;
      box-shadow: 0 1px 3px rgba(16, 185, 129, 0.2);
      border-color: #065f46;
    }
    body.dark-mode .expanded-effect-wrapper.effect-inhibits {
      background: #7f1d1d;
      box-shadow: 0 1px 3px rgba(220, 38, 38, 0.2);
      border-color: #991b1b;
    }
    body.dark-mode .expanded-effect-wrapper.effect-binds {
      background: #4c1d95;
      box-shadow: 0 1px 3px rgba(124, 58, 237, 0.2);
      border-color: #5b21b6;
    }
    body.dark-mode .expanded-mechanism-wrapper {
      background: #78350f;
      box-shadow: 0 1px 3px rgba(245, 158, 11, 0.2);
      border-color: #92400e;
    }
    body.dark-mode .expanded-effect-type {
      background: #1a1a1a;
      border-color: #262626;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
    }
    body.dark-mode .expanded-effect-type.activates {
      background: #064e3b;
      border-color: #065f46;
      color: #a7f3d0;
    }
    body.dark-mode .expanded-effect-type.inhibits {
      background: #7f1d1d;
      border-color: #991b1b;
      color: #fecaca;
    }
    body.dark-mode .expanded-effect-type.binds {
      background: #4c1d95;
      border-color: #5b21b6;
      color: #ddd6fe;
    }
    body.dark-mode .effect-type-badge.activates {
      background: #065f46;
      border-color: #047857;
      color: #a7f3d0;
      box-shadow: 0 1px 3px rgba(16, 185, 129, 0.4);
    }
    body.dark-mode .effect-type-badge.activates:hover {
      border-color: #059669;
      box-shadow: 0 2px 6px rgba(16, 185, 129, 0.5);
    }
    body.dark-mode .effect-type-badge.inhibits {
      background: #991b1b;
      border-color: #b91c1c;
      color: #fecaca;
      box-shadow: 0 1px 3px rgba(220, 38, 38, 0.4);
    }
    body.dark-mode .effect-type-badge.inhibits:hover {
      border-color: #dc2626;
      box-shadow: 0 2px 6px rgba(220, 38, 38, 0.5);
    }
    body.dark-mode .effect-type-badge.binds {
      background: #5b21b6;
      border-color: #6d28d9;
      color: #ddd6fe;
      box-shadow: 0 1px 3px rgba(124, 58, 237, 0.4);
    }
    body.dark-mode .effect-type-badge.binds:hover {
      border-color: #7c3aed;
      box-shadow: 0 2px 6px rgba(124, 58, 237, 0.5);
    }
    /* Dark mode - Legend & Info Panel */
    body.dark-mode .legend {
      background: #1a1a1a;
      border-color: #262626;
      box-shadow: 0 2px 8px rgba(0,0,0,.3);
    }
    body.dark-mode .legend-title {
      color: #d4d4d4;
    }
    body.dark-mode .legend-item {
      color: #a3a3a3;
    }
    body.dark-mode .legend-item[style*="border-top"] {
      border-top-color: #404040 !important;
    }
    body.dark-mode .info-panel {
      background: #1a1a1a;
      border-color: #262626;
      color: #a3a3a3;
      box-shadow: 0 2px 8px rgba(0,0,0,.3);
    }
    body.dark-mode .info-panel strong {
      color: #d4d4d4;
    }
    /* Dark mode - Expanded Content */
    /* Dark mode - NEW simplified expanded row */
    body.dark-mode .expanded-row {
      background: #171717;
      border-left-color: #6366f1;
    }
    body.dark-mode .expanded-content {
      background: #171717;
    }
    body.dark-mode .detail-section-header {
      color: #9ca3af;
    }
    body.dark-mode .detail-divider {
      background: #404040;
    }
    body.dark-mode .detail-label {
      color: #6b7280;
    }
    body.dark-mode .detail-value {
      color: #d4d4d4;
    }
    body.dark-mode .detail-empty {
      color: #6b7280;
    }
    body.dark-mode .detail-interaction {
      color: #e5e5e5;
    }
    body.dark-mode .detail-arrow {
      color: #9ca3af;
    }
    body.dark-mode .detail-effect-activates {
      color: #10b981;
    }
    body.dark-mode .detail-effect-inhibits {
      color: #ef4444;
    }
    body.dark-mode .detail-effect-binds {
      color: #a78bfa;
    }
    body.dark-mode .detail-effect-regulates {
      color: #fbbf24;
    }
    body.dark-mode .detail-effect-complex {
      color: #818cf8;
    }
    body.dark-mode .function-effect-activates {
      color: #34d399;
    }
    body.dark-mode .function-effect-inhibits {
      color: #fca5a5;
    }
    body.dark-mode .function-effect-binds {
      color: #c4b5fd;
    }
    body.dark-mode .function-effect-regulates {
      color: #fcd34d;
    }
    body.dark-mode .function-effect-complex {
      color: #a5b4fc;
    }
    body.dark-mode .detail-list li {
      color: #d4d4d4;
    }
    body.dark-mode .function-row:hover {
      background: linear-gradient(90deg, #1a1a1a 0%, #262626 100%) !important;
      box-shadow: 0 2px 6px rgba(99, 102, 241, 0.2);
    }
    body.dark-mode .function-row[data-expanded="true"] {
      background: linear-gradient(90deg, #312e81 0%, #3730a3 100%) !important;
      border-left-color: #8b5cf6;
      box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3);
    }
    /* Dark mode - Expanded Effect Type (container only) */
    body.dark-mode .expanded-effect-type.activates {
      /* Container styling */
    }
    body.dark-mode .expanded-effect-type.inhibits {
      /* Container styling */
    }
    body.dark-mode .expanded-effect-type.binds {
      /* Container styling */
    }
    body.dark-mode .expanded-cellular-process {
      background: #4c1d95;
      border-color: #5b21b6;
      color: #e9d5ff;
      box-shadow: 0 1px 3px rgba(168, 85, 247, 0.4);
    }
    body.dark-mode .expanded-section--effect .effect-type-badge {
      background: #4c1d95;
      border-color: #6d28d9;
      color: #e9d5ff;
      box-shadow: 0 1px 3px rgba(124, 58, 237, 0.4);
    }
    body.dark-mode .expanded-section--effect .effect-type-badge:hover {
      border-color: #7c3aed;
      box-shadow: 0 2px 6px rgba(124, 58, 237, 0.5);
    }
    body.dark-mode .expanded-section--effect .effect-type-badge.activates {
      background: #065f46;
      border-color: #047857;
      color: #a7f3d0;
      box-shadow: 0 1px 3px rgba(16, 185, 129, 0.4);
    }
    body.dark-mode .expanded-section--effect .effect-type-badge.activates:hover {
      border-color: #059669;
      box-shadow: 0 2px 6px rgba(16, 185, 129, 0.5);
    }
    body.dark-mode .expanded-section--effect .effect-type-badge.inhibits {
      background: #991b1b;
      border-color: #b91c1c;
      color: #fecaca;
      box-shadow: 0 1px 3px rgba(220, 38, 38, 0.4);
    }
    body.dark-mode .expanded-section--effect .effect-type-badge.inhibits:hover {
      border-color: #dc2626;
      box-shadow: 0 2px 6px rgba(220, 38, 38, 0.5);
    }
    body.dark-mode .expanded-section--effect .effect-type-badge.binds {
      background: #5b21b6;
      border-color: #6d28d9;
      color: #ddd6fe;
      box-shadow: 0 1px 3px rgba(124, 58, 237, 0.4);
    }
    body.dark-mode .expanded-section--effect .effect-type-badge.binds:hover {
      border-color: #7c3aed;
      box-shadow: 0 2px 6px rgba(124, 58, 237, 0.5);
    }
    /* Dark mode - Specific Effects */
    body.dark-mode .expanded-effect-chip {
      background: #164e63;
      border-color: #0e7490;
      color: #cffafe;
      box-shadow: 0 1px 3px rgba(6, 182, 212, 0.4);
    }
    body.dark-mode .expanded-effect-chip:hover {
      border-color: #0891b2;
      box-shadow: 0 2px 6px rgba(6, 182, 212, 0.5);
    }
    /* Dark mode - Biological Cascade: Rich amber gradient with scientific precision */
    body.dark-mode .cascade-flow-container::before {
      background: linear-gradient(180deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%);
      box-shadow: 0 0 8px rgba(251, 191, 36, 0.3);
    }
    body.dark-mode .cascade-flow-item {
      background: linear-gradient(135deg, #1c1410 0%, #2d1f14 100%);
      border: 1px solid #92400e;
      border-left: 3px solid #fbbf24;
      color: #fde68a;
      box-shadow: 0 2px 6px rgba(217, 119, 6, 0.2), inset 0 1px 0 rgba(251, 191, 36, 0.1);
    }
    body.dark-mode .cascade-flow-item::before {
      background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
      border-color: #1c1410;
      box-shadow: 0 0 0 2px #d97706, 0 0 12px rgba(251, 191, 36, 0.4);
    }
    body.dark-mode .cascade-flow-item:hover {
      background: linear-gradient(135deg, #2d1f14 0%, #3d2817 100%);
      border-color: #b45309;
      border-left-color: #fcd34d;
      box-shadow: 0 4px 12px rgba(217, 119, 6, 0.35), inset 0 1px 0 rgba(251, 191, 36, 0.15);
      transform: translateX(3px);
    }
    body.dark-mode .cascade-arrow-inline {
      color: #fcd34d;
      text-shadow: 0 0 8px rgba(251, 191, 36, 0.5);
    }
    /* Dark mode - 3D Wrappers */
    body.dark-mode .expanded-cellular-wrapper {
      background: #2e1065;
      box-shadow: 0 1px 3px rgba(168, 85, 247, 0.25);
      border-color: #4c1d95;
      border-left-color: #a855f7;
    }
    body.dark-mode .expanded-effect-chip-wrapper {
      background: #083344;
      box-shadow: 0 1px 3px rgba(6, 182, 212, 0.25);
      border-color: #0e7490;
      border-left-color: #06b6d4;
    }
    body.dark-mode .cascade-wrapper {
      background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
      box-shadow: 0 2px 8px rgba(217, 119, 6, 0.25);
      border: 1px solid #92400e;
      border-left: 3px solid #f59e0b;
    }
    body.dark-mode .cascade-wrapper .cascade-flow-item {
      background: linear-gradient(135deg, #1c1410 0%, #2d1f14 100%);
      color: #fde68a;
      box-shadow: 0 1px 3px rgba(245, 158, 11, 0.2);
    }
    body.dark-mode .cascade-wrapper .cascade-flow-item:hover {
      background: linear-gradient(135deg, #2d1f14 0%, #3d2817 100%);
      box-shadow: 0 3px 8px rgba(245, 158, 11, 0.3);
    }
    body.dark-mode .cascade-wrapper .cascade-flow-item::before {
      background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
      box-shadow: 0 0 0 2px #d97706, 0 0 12px rgba(251, 191, 36, 0.4);
    }
    body.dark-mode .cascade-wrapper .cascade-arrow-inline {
      color: #fcd34d;
    }
    body.dark-mode .expanded-evidence-wrapper {
      background: #1a1a1a;
      box-shadow: 0 1px 3px rgba(99, 102, 241, 0.2);
      border-color: #262626;
      border-left-color: #6366f1;
    }
    body.dark-mode .expanded-evidence-wrapper .expanded-evidence-card {
      box-shadow: 0 1px 4px rgba(99, 102, 241, 0.2);
    }
    body.dark-mode .expanded-evidence-wrapper .expanded-evidence-card:hover {
      box-shadow: 0 6px 16px rgba(99, 102, 241, 0.35), 0 3px 8px rgba(99, 102, 241, 0.25);
    }
    /* Dark mode - Evidence Cards */
    body.dark-mode .expanded-evidence-card {
      background: linear-gradient(135deg, #1a1a1a 0%, #262626 100%);
      border-color: #404040;
      border-left-color: #6366f1;
      box-shadow: 0 2px 6px rgba(99, 102, 241, 0.2), 0 1px 3px rgba(0,0,0,0.3);
    }
    body.dark-mode .expanded-evidence-card:hover {
      border-left-color: #8b5cf6;
      background: linear-gradient(135deg, #262626 0%, #404040 100%);
      border-color: #525252;
      box-shadow: 0 12px 24px rgba(99, 102, 241, 0.3), 0 6px 12px rgba(99, 102, 241, 0.2);
    }
    body.dark-mode .expanded-evidence-card::after {
      color: #525252;
    }
    body.dark-mode .expanded-evidence-card:hover::after {
      color: #8b5cf6;
    }
    body.dark-mode .expanded-evidence-title {
      color: #f5f5f5;
    }
    body.dark-mode .expanded-evidence-quote {
      background: #262626;
      border-left-color: #6366f1;
      color: #d4d4d4;
    }
    body.dark-mode .expanded-evidence-meta {
      color: #d4d4d4;
    }
    /* Dark mode - Modal Elements */
    body.dark-mode .modal {
      background: rgba(0,0,0,.7);
    }
    body.dark-mode .modal-header {
      border-bottom-color: #262626;
    }
    body.dark-mode .modal-footer {
      border-top-color: #262626;
      box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    body.dark-mode .close-btn {
      color: #a3a3a3;
    }
    body.dark-mode .close-btn:hover {
      background: #262626;
      color: #f5f5f5;
    }
    body.dark-mode .info-row {
      border-bottom-color: #262626;
    }
    body.dark-mode .evidence-item {
      background: #262626;
      border-color: #404040;
      border-left-color: #6366f1;
      color: #e5e5e5;
      box-shadow: 0 0 0 4px #1a1a1a, 0 1px 3px rgba(99, 102, 241, 0.2);
    }
    body.dark-mode .evidence-item strong {
      color: #d4d4d4;
    }
    body.dark-mode .specific-effect {
      background: #164e63;
      border-left-color: #0891b2;
      color: #cffafe;
    }
    body.dark-mode .pmid-link {
      background: #312e81;
      border-color: #4338ca;
      color: #e0e7ff;
      box-shadow: 0 1px 3px rgba(67, 56, 202, 0.4);
    }
    body.dark-mode .pmid-link:hover {
      border-color: #6366f1;
      box-shadow: 0 2px 6px rgba(67, 56, 202, 0.5);
    }
    body.dark-mode .cellular-theme {
      background: #064e3b;
      border-color: #10b981;
      color: #d1fae5;
    }
    body.dark-mode .cellular-theme-title {
      color: #6ee7b7;
    }
    /* Dark mode - Biological cascade variants: Unified rich styling */
    body.dark-mode .biological-cascade {
      background: linear-gradient(135deg, #1c1410 0%, #2d1f14 100%);
      border: 1px solid #92400e;
      border-left: 3px solid #fbbf24;
      color: #fde68a;
      box-shadow: 0 2px 6px rgba(217, 119, 6, 0.2);
    }
    body.dark-mode .biological-cascade-item {
      background: linear-gradient(135deg, #1c1410 0%, #2d1f14 100%);
      border: 1px solid #92400e;
      border-left: 3px solid #fbbf24;
      color: #fde68a;
      box-shadow: 0 1px 3px rgba(245, 158, 11, 0.2);
    }
    body.dark-mode .biological-cascade-item:hover {
      background: linear-gradient(135deg, #2d1f14 0%, #3d2817 100%);
      border-color: #b45309;
      box-shadow: 0 2px 6px rgba(245, 158, 11, 0.3);
    }
    body.dark-mode .biological-cascade-table {
      background: linear-gradient(135deg, #1c1410 0%, #2d1f14 100%);
      border: 1px solid #92400e;
      border-left: 3px solid #fbbf24;
      color: #fde68a;
      box-shadow: 0 2px 6px rgba(217, 119, 6, 0.2);
    }
    body.dark-mode .cascade-arrow {
      color: var(--color-activation);
    }
    /* Dark mode - Table Elements with unified chip styling */
    body.dark-mode .interaction-name-wrapper {
      /* Container styling */
    }
    body.dark-mode .interaction-name {
      background: #1e3a8a;
      border-color: #1e40af;
      color: #dbeafe;
      box-shadow: 0 1px 3px rgba(59, 130, 246, 0.4);
    }
    body.dark-mode .interaction-name:hover {
      border-color: #2563eb;
      box-shadow: 0 2px 6px rgba(59, 130, 246, 0.5);
    }
    body.dark-mode .function-name-wrapper.activates {
      /* Container styling */
    }
    body.dark-mode .function-name-wrapper.inhibits {
      /* Container styling */
    }
    body.dark-mode .function-name-wrapper.binds {
      /* Container styling */
    }
    body.dark-mode .function-name.activates {
      background: #065f46;
      border-color: #047857;
      color: #a7f3d0;
      box-shadow: 0 1px 3px rgba(16, 185, 129, 0.4);
    }
    body.dark-mode .function-name.activates:hover {
      border-color: #059669;
      box-shadow: 0 2px 6px rgba(16, 185, 129, 0.5);
    }
    body.dark-mode .function-name.inhibits {
      background: #991b1b;
      border-color: #b91c1c;
      color: #fecaca;
      box-shadow: 0 1px 3px rgba(220, 38, 38, 0.4);
    }
    body.dark-mode .function-name.inhibits:hover {
      border-color: #dc2626;
      box-shadow: 0 2px 6px rgba(220, 38, 38, 0.5);
    }
    body.dark-mode .function-name.binds {
      background: #5b21b6;
      border-color: #6d28d9;
      color: #ddd6fe;
      box-shadow: 0 1px 3px rgba(124, 58, 237, 0.4);
    }
    body.dark-mode .function-name.binds:hover {
      border-color: #7c3aed;
      box-shadow: 0 2px 6px rgba(124, 58, 237, 0.5);
    }
    body.dark-mode .table-evidence-item {
      background: #262626;
      border-color: #404040;
      border-left-color: #6366f1;
      box-shadow: 0 0 0 4px #1a1a1a, 0 1px 3px rgba(99, 102, 241, 0.2);
    }
    body.dark-mode .table-evidence-title {
      color: #f5f5f5;
    }
    body.dark-mode .table-evidence-meta {
      color: #d4d4d4;
    }
    body.dark-mode .effect-type-tag {
      background: #4c1d95;
      border-color: #6d28d9;
      color: #e9d5ff;
      box-shadow: 0 1px 3px rgba(124, 58, 237, 0.4);
    }
    body.dark-mode .effect-type-tag:hover {
      border-color: #7c3aed;
      box-shadow: 0 2px 6px rgba(124, 58, 237, 0.5);
    }
    body.dark-mode .effect-type-tag.activates {
      background: #065f46;
      color: #a7f3d0;
      border-color: #047857;
      box-shadow: 0 1px 3px rgba(16, 185, 129, 0.4);
    }
    body.dark-mode .effect-type-tag.activates:hover {
      border-color: #059669;
      box-shadow: 0 2px 6px rgba(16, 185, 129, 0.5);
    }
    body.dark-mode .effect-type-tag.inhibits {
      background: #991b1b;
      color: #fecaca;
      border-color: #b91c1c;
      box-shadow: 0 1px 3px rgba(220, 38, 38, 0.4);
    }
    body.dark-mode .effect-type-tag.inhibits:hover {
      border-color: #dc2626;
      box-shadow: 0 2px 6px rgba(220, 38, 38, 0.5);
    }
    body.dark-mode .effect-type-tag.binds {
      background: #5b21b6;
      color: #ddd6fe;
      border-color: #6d28d9;
      box-shadow: 0 1px 3px rgba(124, 58, 237, 0.4);
    }
    body.dark-mode .effect-type-tag.binds:hover {
      border-color: #7c3aed;
      box-shadow: 0 2px 6px rgba(124, 58, 237, 0.5);
    }
    body.dark-mode .effect-badge {
      background: #4338ca;
      border-color: #4f46e5;
      color: #e0e7ff;
      box-shadow: 0 1px 3px rgba(67, 56, 202, 0.4);
    }
    body.dark-mode .effect-badge:hover {
      border-color: #6366f1;
      box-shadow: 0 2px 6px rgba(67, 56, 202, 0.5);
    }
    body.dark-mode .effect-badge.effect-activates {
      background: #065f46;
      border-color: #047857;
      color: #a7f3d0;
      box-shadow: 0 1px 3px rgba(16, 185, 129, 0.4);
    }
    body.dark-mode .effect-badge.effect-activates:hover {
      border-color: #059669;
      box-shadow: 0 2px 6px rgba(16, 185, 129, 0.5);
    }
    body.dark-mode .effect-badge.effect-inhibits {
      background: #991b1b;
      border-color: #b91c1c;
      color: #fecaca;
      box-shadow: 0 1px 3px rgba(220, 38, 38, 0.4);
    }
    body.dark-mode .effect-badge.effect-inhibits:hover {
      border-color: #dc2626;
      box-shadow: 0 2px 6px rgba(220, 38, 38, 0.5);
    }
    body.dark-mode .effect-badge.effect-binds {
      background: #5b21b6;
      border-color: #6d28d9;
      color: #ddd6fe;
      box-shadow: 0 1px 3px rgba(124, 58, 237, 0.4);
    }
    body.dark-mode .effect-badge.effect-binds:hover {
      border-color: #7c3aed;
      box-shadow: 0 2px 6px rgba(124, 58, 237, 0.5);
    }
    /* Dark mode - Mechanism badge: Warm gradient matching cascade aesthetics */
    body.dark-mode .mechanism-badge {
      background: linear-gradient(135deg, #78350f 0%, #92400e 100%);
      color: #fde68a;
      border: 1px solid #b45309;
      box-shadow: 0 2px 4px rgba(245, 158, 11, 0.3), inset 0 1px 0 rgba(251, 191, 36, 0.15);
      text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    }
    body.dark-mode .mechanism-badge:hover {
      background: linear-gradient(135deg, #92400e 0%, #b45309 100%);
      border-color: #d97706;
      box-shadow: 0 3px 8px rgba(245, 158, 11, 0.4), inset 0 1px 0 rgba(251, 191, 36, 0.2);
    }
    /* Dark mode - Modal Evidence Cards (fixes hardcoded light mode overrides) */
    body.dark-mode .evidence-title {
      color: #f5f5f5;
    }
    body.dark-mode .evidence-meta {
      color: #a3a3a3;
    }
    body.dark-mode .evidence-quote {
      color: #d4d4d4;
      background: #262626;
      border-left-color: #6366f1;
    }
    body.dark-mode .expanded-pmid-badge {
      background: #1e40af;
      border-color: #3b82f6;
      color: #dbeafe;
      box-shadow: 0 1px 3px rgba(59, 130, 246, 0.4);
    }
    body.dark-mode .expanded-pmid-badge:hover {
      background: #2563eb;
      border-color: #60a5fa;
      box-shadow: 0 2px 6px rgba(59, 130, 246, 0.6);
    }
    /* Fix .pmid-badge to be blue in dark mode (not gray from CSS var) */
    body.dark-mode .pmid-badge {
      background: #1e40af;
      border: 1px solid #3b82f6;
      color: #dbeafe;
      box-shadow: 0 1px 3px rgba(59, 130, 246, 0.4);
    }
    body.dark-mode .pmid-badge:hover {
      background: #2563eb;
      border-color: #60a5fa;
      box-shadow: 0 2px 6px rgba(59, 130, 246, 0.6);
    }
    /* Dark mode - Buttons & Controls */
    body.dark-mode .header-btn {
      background: #262626;
      border-color: #404040;
      color: #d4d4d4;
    }
    body.dark-mode .header-btn:hover {
      background: #404040;
      border-color: #525252;
    }
    body.dark-mode #query-button {
      background: #4338ca;
      color: #f5f5f5;
    }
    body.dark-mode #query-button:hover {
      background: #4f46e5;
    }
    body.dark-mode .cancel-btn {
      border-color: #dc2626;
      background: #1a1a1a;
      color: #fca5a5;
    }
    body.dark-mode .cancel-btn:hover {
      background: #dc2626;
      color: #fff;
    }
    /* Dark mode - Progress Bars */
    body.dark-mode .progress-bar-outer {
      background: #262626;
    }
    body.dark-mode #notification-message {
      color: #d4d4d4;
    }
    /* Dark mode - Expand Icon */
    body.dark-mode .expand-icon {
      color: #a3a3a3;
    }
    body.dark-mode .expand-icon:hover {
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.25) 100%);
    }
    body.dark-mode .function-row:hover .expand-icon {
      color: #818cf8;
    }
    body.dark-mode .function-row[data-expanded="true"] .expand-icon {
      color: #a78bfa;
      background: linear-gradient(135deg, rgba(124, 58, 237, 0.25) 0%, rgba(139, 92, 246, 0.35) 100%);
    }
    /* Dark mode - Chat Panel */
    /* Dark mode - Chat View */
    body.dark-mode .chat-container {
      background: #0a0a0a;
    }
    body.dark-mode .chat-header {
      border-bottom-color: #404040;
    }
    body.dark-mode .chat-title {
      color: #f5f5f5;
    }
    body.dark-mode .chat-subtitle {
      color: #9ca3af;
    }
    body.dark-mode .message-label {
      color: #6b7280;
    }
    body.dark-mode .user-message .message-content {
      background: linear-gradient(135deg, #4338ca 0%, #3730a3 100%);
      box-shadow: 0 2px 8px rgba(67, 56, 202, 0.25);
    }
    body.dark-mode .assistant-message .message-content {
      background: #171717;
      color: #e5e5e5;
      border-color: #404040;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    }
    body.dark-mode .system-message .message-content {
      background: #0c4a6e;
      color: #bae6fd;
      border-color: #075985;
      box-shadow: 0 1px 3px rgba(14, 165, 233, 0.2);
    }
    body.dark-mode .error-message .message-content {
      background: #7f1d1d;
      color: #fecaca;
      border-color: #991b1b;
      box-shadow: 0 1px 3px rgba(220, 38, 38, 0.2);
    }
    body.dark-mode .chat-input-wrapper {
      border-top-color: #404040;
    }
    body.dark-mode .chat-input {
      background: #171717;
      border-color: #404040;
      color: #e5e5e5;
    }
    body.dark-mode .chat-input:focus {
      background: #1a1a1a;
      border-color: #6366f1;
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15), 0 1px 2px rgba(0, 0, 0, 0.3);
    }
    body.dark-mode .chat-input::placeholder {
      color: #6b7280;
    }
    body.dark-mode .chat-send-btn {
      background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
    }
    body.dark-mode .chat-send-btn:hover:not(:disabled) {
      background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
      box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
    }
    body.dark-mode .chat-send-btn:active:not(:disabled) {
      box-shadow: 0 2px 6px rgba(99, 102, 241, 0.3);
    }
    body.dark-mode .chat-send-btn:disabled {
      background: #404040;
      color: #6b7280;
    }
    body.dark-mode .chat-messages::-webkit-scrollbar-thumb {
      background: #404040;
      border-color: #0a0a0a;
    }
    body.dark-mode .chat-messages::-webkit-scrollbar-thumb:hover {
      background: #525252;
    }
    /* Dark mode - Misc */
    body.dark-mode .muted-text {
      color: #a3a3a3;
    }
    body.dark-mode .resize-handle:hover {
      background: rgba(99, 102, 241, 0.4);
    }
    body.dark-mode .resize-handle:active {
      background: rgba(99, 102, 241, 0.6);
    }
    body.dark-mode .expanded-empty {
      color: #525252;
      background: linear-gradient(135deg, #1a1a1a 0%, #262626 100%);
      border-color: #404040;
    }
    body.dark-mode .expanded-empty:hover {
      border-color: #525252;
      background: linear-gradient(135deg, #262626 0%, #404040 100%);
    }
    .container{position:relative;width:100%;min-height:100vh;display:flex;flex-direction:column}
    .container.graph-active{height:100vh}

    /* Header uses same classes/ids as index to pick up site styles */

    /* Auto-hiding header */
    .header-trigger{
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 80px;
      z-index: 59;
      pointer-events: all;
    }
    .header{
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      background: #fff;
      padding: 8px 16px;
      box-shadow: 0 1px 3px rgba(0,0,0,.06);
      border-bottom: 1px solid #e1e4e8;
      z-index: 60;
      transform: translateY(-100%);
      transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .header.header-visible{
      transform: translateY(0);
    }
    .header.header-static{
      position: relative;
      transform: translateY(0);
    }
    /* Header visibility controlled by JavaScript (see headerAutoHide logic below) */

    .title{font-size:24px;font-weight:600;color:#1a202c;text-align:center;margin-bottom:4px;letter-spacing:-.5px}
    .subtitle{text-align:center;color:#6b7280;font-size:12px}
    .header-search-container{display:flex;flex-direction:column;align-items:center;justify-content:center;margin-top:6px;gap:0}
    .input-container{display:inline-flex;align-items:center;gap:6px}
    #protein-input{height:34px;border-radius:999px;padding:0 12px;border:1px solid #e5e7eb;width:240px;font-size:14px}
    #query-button{height:34px;border-radius:999px;border:0;background:#4f46e5;color:#fff;padding:0 14px;cursor:pointer;font-size:14px}

    /* Results mini-progress (IDs consistent with your script.css/script.js) */
    .job-notification{margin-top:4px;text-align:center}
    .mini-progress-wrapper{display:none;grid-template-columns:1fr auto auto;gap:8px;align-items:center;justify-content:center}
    .progress-bar-outer{width:240px;height:8px;border-radius:999px;background:#e5e7eb;overflow:hidden;margin:0 auto}
    .progress-bar-inner{width:0%;height:100%;background:linear-gradient(90deg,#6366f1,#22d3ee)}
    #notification-message{color:#4b5563;font-size:12px;margin-top:6px}
    .cancel-btn{
      height:32px;padding:0 12px;border-radius:6px;border:1px solid #dc2626;
      background:#fff;color:#dc2626;font-size:13px;font-weight:500;cursor:pointer;
      transition:all .2s;white-space:nowrap;
    }
    .cancel-btn:hover{background:#dc2626;color:#fff;}

    #network{flex:1;position:relative;background:#fff;overflow:hidden;border:2px solid #e5e7eb}
    #svg{display:block;width:100%;height:100%}

    .controls{position:absolute;top:20px;left:20px;background:#fff;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.1);
      padding:10px;display:flex;gap:8px;align-items:center;z-index:50;border:1px solid #e1e4e8;user-select:none;
      transition: top 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    /* Shift controls down when header is visible (JS-controlled) */
    .header.header-visible ~ #network .controls {
      top: 210px;
    }
    .control-btn{width:32px;height:32px;border:1px solid #d1d5db;background:#fff;border-radius:6px;cursor:pointer;
      display:flex;align-items:center;justify-content:center;font-size:18px;color:#4b5563;transition:all .2s}
    .control-btn:hover{background:#f3f4f6;border-color:#9ca3af}
    .control-divider{width:1px;height:24px;background:#d1d5db;margin:0 4px}

    .filter-label{font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.5px}
    .graph-filter-btn{border:2px solid;padding:4px 10px;border-radius:16px;font-size:11px;font-weight:600;
      cursor:pointer;background:#fff;transition:all .2s;display:inline-flex;align-items:center;gap:6px}
    .graph-filter-btn.activates{border-color:#059669;color:#059669}
    .graph-filter-btn.inhibits{border-color:#dc2626;color:#dc2626}
    .graph-filter-btn.binds{border-color:#7c3aed;color:#7c3aed}
    .graph-filter-btn.active.activates{background:#059669;color:#fff}
    .graph-filter-btn.active.inhibits{background:#dc2626;color:#fff}
    .graph-filter-btn.active.binds{background:#7c3aed;color:#fff}
    .graph-filter-btn:hover{opacity:0.85;transform:translateY(-1px)}
    .filter-dot{width:8px;height:8px;border-radius:50%;display:inline-block}
    .filter-dot.activates{background:#059669}
    .filter-dot.inhibits{background:#dc2626}
    .filter-dot.binds{background:#7c3aed}

    /* ===============================================================
       GRAPH STYLING - Improved Nodes & Arrows
       =============================================================== */

    /* Node Base Styles */
    .node{
      cursor: pointer;
      transition: filter var(--transition-base), transform var(--transition-fast);
    }
    .node:hover{
      filter: brightness(1.1) drop-shadow(0 2px 4px rgba(0,0,0,0.2));
      transform: scale(1.03);
    }

    /* Main Node - Visually Distinct with Glow */
    .main-node{
      fill: url(#mainGradient);
      stroke: #4f46e5;
      stroke-width: 3;
      filter: drop-shadow(0 0 8px rgba(79, 70, 229, 0.5));
    }

    /* Interactor Nodes - Subtle Gradient */
    .interactor-node{
      fill: url(#interactorGradient);
      stroke: #404040;
      stroke-width: 2;
    }

    /* Expanded nodes look like normal interactor nodes */
    .expanded-node{
      fill: url(#interactorGradient);
      stroke: #404040;
      stroke-width: 2.5;
    }

    /* Indirect interactor nodes - dotted border, lower opacity */
    .interactor-node-indirect {
      fill: url(#interactorGradient);
      stroke: #404040;
      stroke-width: 2;
      stroke-dasharray: 4, 3;
      opacity: 0.85;
    }

    /* Node Labels */
    .node-label{
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      fill: #ffffff;
      text-anchor: middle;
      pointer-events: none;
      letter-spacing: 0.3px;
    }
    .node-label.main-label{
      font-size: 21px;
      letter-spacing: 1px;
    }

    /* Link Styles - Thicker & Smoother */
    .link{
      fill: none;
      stroke-width: 3;
      opacity: 0.75;
      cursor: pointer;
      transition: stroke-width var(--transition-base), opacity var(--transition-base);
    }
    .link:hover{
      stroke-width: 4.5;
      opacity: 0.95;
    }

    /* Link Colors - Light Mode */
    .link-activate{stroke: var(--color-activation);}
    .link-inhibit{stroke: var(--color-inhibition);}
    .link-binding{stroke: var(--color-binding);}

    /* Shared Links */
    .link-shared{
      stroke-dasharray: 5,3;
      opacity: 0.8;
      filter: drop-shadow(0 0 4px rgba(245, 158, 11, 0.9)) drop-shadow(0 0 8px rgba(245, 158, 11, 0.6)) drop-shadow(0 0 12px rgba(245, 158, 11, 0.3));
    }
    .link-shared:hover{
      opacity: 0.95;
      stroke-width: 3.5;
      filter: drop-shadow(0 0 5px rgba(245, 158, 11, 1)) drop-shadow(0 0 10px rgba(245, 158, 11, 0.8)) drop-shadow(0 0 16px rgba(245, 158, 11, 0.5));
    }

    /* Dark Mode - Shared Links (brighter gold glow) */
    body.dark-mode .link-shared{
      filter: drop-shadow(0 0 5px rgba(251, 191, 36, 0.95)) drop-shadow(0 0 9px rgba(251, 191, 36, 0.7)) drop-shadow(0 0 14px rgba(251, 191, 36, 0.4));
    }
    body.dark-mode .link-shared:hover{
      filter: drop-shadow(0 0 6px rgba(251, 191, 36, 1)) drop-shadow(0 0 12px rgba(251, 191, 36, 0.85)) drop-shadow(0 0 18px rgba(251, 191, 36, 0.6));
    }

    /* Indirect Links (cascade/pathway, not physical) */
    .link-indirect{
      stroke-dasharray: 8,4;
      opacity: 0.7;
    }
    .link-indirect:hover{
      opacity: 0.9;
    }

    /* Incomplete Pathway Links (fallback when mediator missing) */
    .link-incomplete{
      stroke: #ff8c00;  /* Orange warning color */
      stroke-dasharray: 5,5;
      opacity: 0.7;
    }
    .link-incomplete:hover{
      opacity: 0.95;
      stroke-width: 3.5;
    }

    /* Dark Mode - Incomplete Links (brighter orange) */
    body.dark-mode .link-incomplete{
      stroke: #ffa500;
      opacity: 0.75;
    }
    body.dark-mode .link-incomplete:hover{
      opacity: 1;
    }

    /* Dark Mode - Node Overrides */
    body.dark-mode .main-node{
      fill: url(#mainGradientDark);
      stroke: #64b5f6;
      filter: drop-shadow(0 0 10px rgba(100, 181, 246, 0.6));
    }

    body.dark-mode .interactor-node{
      fill: url(#interactorGradientDark);
      stroke: #525252;
    }

    /* Expanded nodes look like normal interactor nodes (no blue glow) */
    body.dark-mode .expanded-node{
      fill: url(#interactorGradientDark);
      stroke: #525252;
      stroke-width: 2.5;
    }

    /* Indirect interactor nodes - dotted border, lower opacity (dark mode) */
    body.dark-mode .interactor-node-indirect {
      fill: url(#interactorGradientDark);
      stroke: #525252;
      stroke-width: 2;
      stroke-dasharray: 4, 3;
      opacity: 0.85;
    }

    body.dark-mode .node-label{
      fill: #e0e0e0;
    }

    /* Legend restored */
    .legend{position:absolute;bottom:20px;right:20px;background:#fff;padding:12px 16px;border-radius:8px;
      box-shadow:0 2px 8px rgba(0,0,0,.1);border:1px solid #e1e4e8;z-index:20}
    .legend-title{font-weight:600;margin-bottom:8px;color:#374151;font-size:12px;text-transform:uppercase;letter-spacing:.5px}
    .legend-item{display:flex;align-items:center;margin:4px 0;font-size:12px;color:#6b7280}
    .legend-arrow{width:30px;height:20px;margin-right:8px;display:flex;align-items:center}

    /* ===============================================================
       MODAL SYSTEM - Typography-Focused & Expandable
       =============================================================== */
    .modal{
      display:none;
      position:fixed;
      inset:0;
      background:rgba(0,0,0,.7);
      backdrop-filter: blur(4px);
      z-index:1000;
      animation: modalFadeIn var(--transition-slow) ease;
    }
    .modal.active{
      display:flex;
      align-items:center;
      justify-content:center;
    }
    .modal-content{
      background: var(--color-bg-elevated);
      border-radius: var(--radius-xl);
      padding: 0;
      max-width: 900px;
      width: 90%;
      max-height: 85vh;
      display: flex;
      flex-direction: column;
      box-shadow: var(--shadow-lg);
      animation: modalSlideIn var(--transition-slow) cubic-bezier(0.34, 1.56, 0.64, 1);
    }

    @keyframes modalFadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    @keyframes modalSlideIn {
      from { transform: translateY(20px) scale(0.95); opacity: 0; }
      to { transform: translateY(0) scale(1); opacity: 1; }
    }

    /* Modal Header - Sticky */
    .modal-header{
      position: sticky;
      top: 0;
      background: var(--color-bg-elevated);
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--space-6);
      border-bottom: 1px solid var(--color-border-medium);
      border-radius: var(--radius-xl) var(--radius-xl) 0 0;
      z-index: 10;
    }

    .modal-title{
      font-family: var(--font-serif);
      font-size: var(--text-2xl);
      font-weight: 600;
      color: var(--color-text-primary);
      line-height: var(--leading-tight);
    }

    .close-btn{
      background: none;
      border: none;
      font-size: 24px;
      cursor: pointer;
      color: var(--color-text-secondary);
      width: 32px;
      height: 32px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all var(--transition-fast);
    }
    .close-btn:hover{
      background: var(--color-bg-tertiary);
      color: var(--color-text-primary);
      transform: scale(1.1);
    }

    /* Modal Body - Scrollable */
    .modal-body{
      padding: var(--space-6) var(--space-6) 0 var(--space-6);
      overflow-y: auto;
      flex: 1;
      display: flex;
      flex-direction: column;
      font-family: var(--font-sans);
    }

    /* Modal Footer - Sticky at bottom */
    .modal-footer{
      position: sticky;
      bottom: 0;
      background: var(--color-bg-elevated);
      margin: 0 calc(var(--space-6) * -1);
      padding: var(--space-4) var(--space-6);
      border-top: 2px solid var(--color-border-light);
      border-bottom-left-radius: var(--radius-xl);
      border-bottom-right-radius: var(--radius-xl);
      margin-top: auto;
      box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.05);
      z-index: 10;
    }

    /* Modal Footer Buttons */
    .modal-footer .btn-primary:hover {
      background: #2563eb !important;
    }
    .modal-footer .btn-secondary:hover {
      background: #dc2626 !important;
    }

    /* Interaction Summary Section */
    .modal-summary{
      margin-bottom: var(--space-8);
    }

    .modal-interaction-header{
      display: flex;
      align-items: center;
      gap: var(--space-4);
      padding: var(--space-6);
      background: var(--color-bg-tertiary);
      border-radius: var(--radius-lg);
      margin-bottom: var(--space-6);
    }

    .modal-protein-name{
      font-family: var(--font-mono);
      font-size: var(--text-lg);
      font-weight: 600;
      color: var(--color-text-primary);
    }

    .modal-arrow{
      font-size: var(--text-xl);
      color: var(--color-text-secondary);
    }

    .modal-detail-grid{
      display: grid;
      grid-template-columns: auto 1fr;
      gap: var(--space-4) var(--space-6);
      margin-bottom: var(--space-6);
      align-items: start;
    }

    .modal-detail-label{
      font-family: var(--font-sans);
      font-size: var(--text-xs);
      font-weight: 600;
      color: var(--color-text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding-top: 2px; /* Align with value text baseline */
    }

    .modal-detail-value{
      font-family: var(--font-sans);
      font-size: var(--text-sm);
      color: var(--color-text-primary);
      line-height: var(--leading-relaxed);
    }

    /* Functions Section Header */
    .modal-functions-header{
      font-family: var(--font-serif);
      font-size: var(--text-xl);
      font-weight: 600;
      color: var(--color-text-primary);
      margin-bottom: var(--space-4);
      padding-bottom: var(--space-3);
      border-bottom: 2px solid var(--color-border-medium);
    }

    /* Interaction Summary (Node Modal) */
    .interaction-summary{
      margin-bottom: 12px;
      padding: 10px;
      border: 1px solid var(--color-border-medium);
      border-radius: 6px;
      background: var(--color-bg-elevated);
    }
    .partner-group h4{
      margin-bottom: 10px;
      padding-bottom: 6px;
      border-bottom: 2px solid var(--color-border-medium);
      font-size: 15px;
      color: var(--color-text-primary);
    }

    /* Expandable Function Rows */
    .function-expandable-row{
      border: 1px solid var(--color-border-medium);
      border-radius: var(--radius-lg);
      margin-bottom: var(--space-3);
      overflow: hidden;
      transition: all var(--transition-base);
    }

    .function-expandable-row:hover{
      border-color: var(--color-border-strong);
      box-shadow: var(--shadow-sm);
    }

    .function-row-header{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--space-4);
      cursor: pointer;
      background: var(--color-bg-secondary);
      transition: background var(--transition-fast);
    }

    .function-row-header:hover{
      background: var(--color-bg-tertiary);
    }

    .function-row-left{
      display: flex;
      align-items: center;
      gap: var(--space-3);
      flex: 1;
    }

    .function-expand-icon{
      font-size: 12px;
      color: var(--color-text-secondary);
      transition: transform var(--transition-base);
      width: 16px;
      text-align: center;
    }

    .function-expandable-row.expanded .function-expand-icon{
      transform: rotate(180deg);
    }

    .function-name-display{
      font-family: var(--font-serif);
      font-size: var(--text-base);
      font-weight: 600;
      color: var(--color-text-primary);
    }

    .function-row-right{
      display: flex;
      align-items: center;
      gap: var(--space-3);
    }


    /* Function Expanded Content */
    .function-expanded-content{
      max-height: 0;
      opacity: 0;
      overflow: hidden;
      transition: max-height var(--transition-slow) ease, opacity var(--transition-base) ease;
    }

    .function-expandable-row.expanded .function-expanded-content{
      max-height: 2000px;
      opacity: 1;
      padding: var(--space-6);
      background: var(--color-bg-primary);
      border-top: 1px solid var(--color-border-subtle);
    }

    .function-detail-section{
      margin-bottom: var(--space-6);
    }

    .function-detail-section:last-child{
      margin-bottom: 0;
    }

    .function-section-title{
      font-family: var(--font-sans);
      font-size: var(--text-sm);
      font-weight: 600;
      color: var(--color-text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: var(--space-2);
    }

    .function-section-content{
      font-family: var(--font-sans);
      font-size: var(--text-sm);
      color: var(--color-text-primary);
      line-height: var(--leading-relaxed);
    }

    /* Enhanced function sections with color coding */
    .function-detail-section.section-highlighted {
      padding: var(--space-3) var(--space-4);
      background: var(--color-bg-secondary);
      border-radius: var(--radius-md);
      border-left: 3px solid var(--color-accent-primary);
    }

    .function-detail-section.section-cellular-process {
      border-left-color: #3b82f6;
    }

    .function-detail-section.section-effect {
      border-left-color: var(--color-accent-primary);
    }

    .function-detail-section.section-effect.effect-activates {
      border-left-color: #10b981;
      background: rgba(16, 185, 129, 0.05);
    }

    .function-detail-section.section-effect.effect-inhibits {
      border-left-color: #ef4444;
      background: rgba(239, 68, 68, 0.05);
    }

    .function-detail-section.section-effect.effect-binds {
      border-left-color: #8b5cf6;
      background: rgba(139, 92, 246, 0.05);
    }

    .function-detail-section.section-specific-effects {
      border-left-color: #f59e0b;
    }

    .function-detail-section.section-mechanism {
      padding: var(--space-3) var(--space-4);
      background: rgba(245, 158, 11, 0.05);
      border-radius: var(--radius-md);
      border-left: 3px solid #f59e0b;
      margin-bottom: var(--space-4);
    }

    /* Dark mode adjustments */
    body.dark-mode .function-detail-section.section-highlighted {
      background: rgba(255, 255, 255, 0.05);
    }

    body.dark-mode .function-detail-section.section-effect.effect-activates {
      background: rgba(16, 185, 129, 0.1);
      border-left-color: #34d399;
    }

    body.dark-mode .function-detail-section.section-effect.effect-inhibits {
      background: rgba(239, 68, 68, 0.1);
      border-left-color: #f87171;
    }

    body.dark-mode .function-detail-section.section-effect.effect-binds {
      background: rgba(139, 92, 246, 0.1);
      border-left-color: #a78bfa;
    }

    body.dark-mode .function-detail-section.section-mechanism {
      background: rgba(245, 158, 11, 0.1);
      border-left-color: #fbbf24;
    }

    /* Cascade Display */
    .cascade-flow{
      display: flex;
      flex-direction: column;
      gap: var(--space-2);
    }

    .cascade-step{
      display: flex;
      align-items: center;
      gap: var(--space-2);
      font-size: var(--text-sm);
      padding: var(--space-2) var(--space-3);
      background: var(--color-bg-secondary);
      border-radius: var(--radius-md);
    }

    .cascade-step-arrow{
      color: var(--color-activation);
      font-weight: bold;
    }

    /* Cascade Scenario Separation */
    .cascade-scenario {
      margin-bottom: var(--space-6);
    }

    .cascade-scenario:last-child {
      margin-bottom: 0;
    }

    .cascade-scenario-label {
      font-family: var(--font-sans);
      font-size: var(--text-xs);
      font-weight: 700;
      color: var(--color-accent-primary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: var(--space-3);
      padding-bottom: var(--space-2);
      border-bottom: 1px solid var(--color-border-subtle);
    }

    .cascade-scenario + .cascade-scenario {
      padding-top: var(--space-5);
      border-top: 2px dashed var(--color-border-subtle);
    }

    body.dark-mode .cascade-scenario-label {
      color: #a78bfa;
    }

    body.dark-mode .cascade-scenario + .cascade-scenario {
      border-top-color: rgba(255, 255, 255, 0.1);
    }

    /* Evidence Cards in Expanded Function */
    .evidence-card{
      background: var(--color-bg-secondary);
      border: 1px solid var(--color-border-subtle);
      border-left: 3px solid var(--color-accent-primary);
      border-radius: var(--radius-md);
      padding: var(--space-4);
      margin-bottom: var(--space-3);
    }

    .evidence-title{
      font-family: var(--font-sans);
      font-size: var(--text-sm);
      font-weight: 600;
      color: var(--color-text-primary);
      margin-bottom: var(--space-2);
    }

    .evidence-meta{
      font-family: var(--font-sans);
      font-size: var(--text-xs);
      color: var(--color-text-secondary);
      margin-bottom: var(--space-2);
    }

    .evidence-quote{
      font-family: var(--font-sans);
      font-size: var(--text-sm);
      font-style: italic;
      color: var(--color-text-secondary);
      padding: var(--space-3);
      background: var(--color-bg-tertiary);
      border-left: 2px solid var(--color-border-medium);
      border-radius: var(--radius-sm);
      margin-top: var(--space-2);
    }

    .pmid-badge{
      display: inline-block;
      font-family: var(--font-mono);
      font-size: var(--text-xs);
      padding: var(--space-1) var(--space-2);
      background: var(--color-accent-primary);
      color: white;
      border-radius: var(--radius-sm);
      text-decoration: none;
      margin-right: var(--space-2);
      transition: background var(--transition-fast);
    }

    .pmid-badge:hover{
      background: var(--color-accent-info);
    }

    /* OLD STYLES - Keep for backward compatibility */
    .info-table{width:100%;border-collapse:collapse}
    .info-row{border-bottom:1px solid #f3f4f6}
    .info-row:last-child{border-bottom:none}
    .info-label{font-weight:600;color:#6b7280;padding:10px 0;vertical-align:top;width:25%;text-transform:uppercase;font-size:11px;letter-spacing:.5px}
    .info-value{padding:10px 0 10px 16px;color:#1f2937;line-height:1.6;font-size:14px}
    .evidence-item{
      background:#fff;
      padding:10px;
      border-radius:6px;
      margin:6px 0;
      border:1px solid #e5e7eb;
      border-left:3px solid #6366f1;
      font-size:13px;
      box-shadow:0 0 0 4px #f8fafc, 0 1px 3px rgba(99,102,241,0.08);
    }
    .evidence-item strong{color:#4b5563}
    .pmid-link{color:#4f46e5;text-decoration:none;font-weight:600}
    .pmid-link:hover{text-decoration:underline}
    .specific-effect{background:#f0f9ff;padding:8px 12px;margin:6px 0;border-radius:6px;border-left:3px solid #0891b2;font-size:13px}

    .info-panel{position:absolute;top:20px;right:20px;background:#fff;padding:12px 16px;border-radius:8px;
      box-shadow:0 2px 8px rgba(0,0,0,.1);border:1px solid #e1e4e8;font-size:12px;color:#6b7280;z-index:20;
      transition: top 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    /* Shift info-panel down when header is visible (JS-controlled) */
    .header.header-visible ~ #network .info-panel {
      top: 190px;
    }
    .info-panel strong{color:#374151}

    /* Modal content boxes for Cellular Process and Biological Cascade */
    .cellular-theme {
      background: #ecfdf5;
      padding: 12px;
      border-radius: 8px;
      margin: 10px 0;
      border: 1px solid #10b981;
    }
    .cellular-theme-title {
      font-weight: 600;
      color: #059669;
      margin-bottom: 8px;
      text-transform: uppercase;
      font-size: 12px;
    }
    .biological-cascade {
      background: #fffbeb;
      padding: 7px 10px;
      border-radius: 5px;
      margin: 6px 0;
      border: 1px solid #fde68a;
      border-left: 3px solid #f59e0b;
    }
    .cascade-arrow {
      color: #10b981;
      font-weight: bold;
      margin: 0 4px;
    }
    .cascade-line {
      margin-bottom: 6px;
      line-height: 1.6;
    }

    /* === Header Controls Row === */
    .header-controls-row {
      display: flex;
      gap: 12px;
      align-items: center;
      justify-content: center;
      margin-top: 26px;
      padding: 0 20px;
      flex-wrap: wrap;
    }

    /* Unified header button styling */
    .header-btn {
      height: 36px;
      padding: 0 18px;
      border: 1px solid #d1d5db;
      background: white;
      color: #4b5563;
      border-radius: 999px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    .header-btn:hover {
      background: #f3f4f6;
      border-color: #9ca3af;
    }

    /* View Tabs */
    .view-tabs {
      display: flex;
      gap: 8px;
    }
    .tab-btn.active {
      background: #4f46e5;
      color: white;
      border-color: #4f46e5;
    }

    /* Research Settings Inline */
    .config-details-inline {
      position: relative;
    }
    .config-summary-inline {
      list-style: none;
    }
    .config-summary-inline::-webkit-details-marker {
      display: none;
    }
    .config-content-inline {
      position: absolute;
      top: calc(100% + 12px);
      left: 50%;
      transform: translateX(-50%);
      min-width: 400px;
      background: white;
      border: 2px solid #e5e7eb;
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      z-index: 100;
    }
    .view-container {
      flex: 1;
      position: relative;
      background: #fff;
    }
    #network {
      overflow: hidden;
    }
    #table-view {
      display: flex;
      flex-direction: column;
      padding: 0;
      overflow-y: visible;
    }
    .table-controls {
      padding: 16px 20px;
      background: white;
      border-bottom: 1px solid #e5e7eb;
      box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    }
    .table-controls-main {
      display: flex;
      gap: 10px;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }
    .table-controls-left {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
      flex: 1;
    }
    .search-container {
      position: relative;
      flex: 1;
      min-width: 250px;
      max-width: 450px;
    }
    .table-search-input {
      width: 100%;
      height: 38px;
      padding: 0 40px 0 20px;
      border: 2px solid #e5e7eb;
      border-radius: 999px;
      font-size: 14px;
      font-weight: 500;
      transition: border-color 0.2s;
    }
    .table-search-input:focus {
      outline: none;
      border-color: #4f46e5;
      box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
    }
    .search-clear-btn {
      position: absolute;
      right: 10px;
      top: 50%;
      transform: translateY(-50%);
      width: 22px;
      height: 22px;
      border: none;
      background: #9ca3af;
      color: white;
      border-radius: 50%;
      font-size: 18px;
      line-height: 1;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s;
    }
    .search-clear-btn:hover {
      background: #6b7280;
    }
    .filter-chips {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      align-items: center;
    }
    .filter-chip {
      height: 34px;
      padding: 0 16px;
      border: 2px solid;
      border-radius: 999px;
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      background: white;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    .filter-chip.activates {
      border-color: #059669;
      color: #059669;
    }
    .filter-chip.inhibits {
      border-color: #dc2626;
      color: #dc2626;
    }
    .filter-chip.binds {
      border-color: #7c3aed;
      color: #7c3aed;
    }
    .filter-chip.filter-active.activates {
      background: #059669;
      color: white;
    }
    .filter-chip.filter-active.inhibits {
      background: #dc2626;
      color: white;
    }
    .filter-chip.filter-active.binds {
      background: #7c3aed;
      color: white;
    }
    .filter-chip:hover {
      opacity: 0.8;
    }
    .filter-results {
      font-size: 12.5px;
      color: #6b7280;
      font-weight: 500;
    }
    .export-dropdown {
      position: relative;
    }
    .export-btn {
      height: 36px;
      padding: 0 20px;
      border: 2px solid #4f46e5;
      background: white;
      color: #4f46e5;
      border-radius: 999px;
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    .export-btn:hover {
      background: #4f46e5;
      color: white;
    }
    .export-dropdown-menu {
      display: none;
      position: absolute;
      right: 0;
      top: calc(100% + 4px);
      background: white;
      border: 2px solid #e5e7eb;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      min-width: 200px;
      z-index: 100;
      overflow: hidden;
    }
    .export-dropdown-menu.show {
      display: block;
    }
    .export-option {
      width: 100%;
      padding: 10px 16px;
      border: none;
      background: white;
      color: #1f2937;
      font-size: 13.5px;
      font-weight: 500;
      text-align: left;
      cursor: pointer;
      transition: background 0.2s;
    }
    .export-option:hover {
      background: #f3f4f6;
    }
    .export-option:not(:last-child) {
      border-bottom: 1px solid #e5e7eb;
    }
    .table-wrapper {
      border: 1px solid #d1d5db;
      border-radius: 12px;
      background: white;
      margin: 12px 20px 28px 20px;
      box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
      overflow: hidden;
    }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      font-family: var(--font-sans);
      font-size: var(--text-sm);
    }
    .data-table thead {
      background: var(--color-bg-tertiary);
      border-bottom: 2px solid var(--color-border-medium);
      position: sticky;
      top: 0;
      z-index: 10;
    }
    .data-table th {
      padding: var(--space-3) var(--space-4);
      text-align: left;
      font-family: var(--font-sans);
      font-weight: 600;
      color: var(--color-text-primary);
      text-transform: uppercase;
      font-size: var(--text-xs);
      letter-spacing: 0.05em;
    }
    .data-table th.sortable {
      cursor: pointer;
      user-select: none;
      position: relative;
    }
    .data-table th.sortable:hover {
      background: #e5e7eb;
    }
    .sort-indicator {
      margin-left: 4px;
      font-size: 9px;
      color: #9ca3af;
      display: inline-block;
      width: 10px;
    }
    .data-table th.sort-asc .sort-indicator::after {
      content: '▲';
      color: #4f46e5;
    }
    .data-table th.sort-desc .sort-indicator::after {
      content: '▼';
      color: #4f46e5;
    }
    .data-table .col-expand { width: 40px; min-width: 40px; max-width: 40px; text-align: center; }
    .data-table .col-interaction { min-width: 150px; }
    .data-table .col-effect { min-width: 100px; }
    .data-table .col-effect-type { min-width: 120px; }
    .data-table .col-mechanism { min-width: 140px; }
    .data-table .col-function { min-width: 150px; }
    .data-table tbody tr {
      background: #ffffff;
      border-bottom: 1px solid #e5e7eb;
      transition: background 0.15s;
    }
    .data-table tbody tr:hover {
      background: #eef2ff;
    }
    .data-table tbody tr.function-row {
      background: white;
    }
    .data-table tbody tr.function-row:nth-child(even) {
      background: #f9fafb;
    }
    .data-table tbody tr.function-row:hover {
      background: #e0e7ff;
    }
    .data-table td {
      padding: 8px 12px;
      color: var(--color-text-primary);
      vertical-align: middle;
      font-size: 13px;
      line-height: 1.5;
    }

    /* === NEW: Clean Text-Based Table Cell Styles === */

    /* Interaction cell - clean text with colored arrow */
    .interaction-cell {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .interaction-text {
      font-family: var(--font-mono);
      font-size: 13px;
      font-weight: 500;
      color: #1f2937;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .interaction-arrow {
      font-size: 14px;
      font-weight: 700;
      margin: 0 2px;
    }
    .interaction-arrow-activates {
      color: #059669;
    }
    .interaction-arrow-inhibits {
      color: #dc2626;
    }
    .interaction-arrow-binds {
      color: #7c3aed;
    }
    .interaction-subtitle {
      font-size: 11px;
      color: #6b7280;
      font-weight: 500;
    }

    /* Function cell - clean text only */
    .function-text {
      font-size: 13px;
      font-weight: 500;
      color: #1f2937;
    }

    /* Effect cell - uppercase colored text */
    .effect-text {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .effect-text-activates {
      color: #059669;
    }
    .effect-text-inhibits {
      color: #dc2626;
    }
    .effect-text-binds {
      color: #7c3aed;
    }

    /* Effect type cell - plain text */
    .effect-type-text {
      font-size: 13px;
      color: #374151;
      line-height: 1.4;
    }

    /* Mechanism cell - amber uppercase text */
    .mechanism-text {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #d97706;
    }

    /* === END NEW STYLES === */

    /* OLD: Interaction name with unified chip styling (kept for backward compatibility in expanded content) */
    .interaction-name-wrapper {
      display: flex;
      flex-wrap: wrap;
      gap: var(--space-2);
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    .interaction-name {
      font-family: var(--font-mono);
      background: var(--color-bg-tertiary);
      color: var(--color-text-primary);
      padding: var(--space-2) var(--space-3);
      border-radius: var(--radius-md);
      font-size: var(--text-xs);
      font-weight: 600;
      line-height: 1.4;
      border: 1px solid var(--color-border-medium);
      box-shadow: var(--shadow-sm);
      transition: box-shadow var(--transition-fast), border-color var(--transition-fast);
      display: inline-flex;
      align-items: center;
      gap: var(--space-2);
    }
    .interaction-name:hover {
      box-shadow: 0 2px 6px rgba(59, 130, 246, 0.15);
      border-color: #60a5fa;
    }
    .interaction-arrow {
      color: #404040;
      font-weight: 400;
      margin: 0 4px;
    }
    /* Effect badge with unified chip styling */
    .effect-badge {
      font-family: var(--font-sans);
      background: var(--color-bg-tertiary);
      color: var(--color-text-primary);
      padding: var(--space-1) var(--space-3);
      border-radius: var(--radius-sm);
      font-size: var(--text-xs);
      font-weight: 600;
      line-height: 1.4;
      border: 1px solid var(--color-border-medium);
      box-shadow: var(--shadow-sm);
      transition: box-shadow var(--transition-fast), border-color var(--transition-fast);
      display: inline-block;
    }
    .effect-badge:hover {
      box-shadow: var(--shadow-md);
      border-color: var(--color-border-strong);
    }
    .effect-badge.effect-activates {
      background: var(--color-activation-light);
      color: var(--color-activation-dark);
      border-color: var(--color-activation);
    }
    .effect-badge.effect-activates:hover {
      box-shadow: 0 2px 6px rgba(16, 185, 129, 0.2);
    }
    .effect-badge.effect-inhibits {
      background: var(--color-inhibition-light);
      color: var(--color-inhibition-dark);
      border-color: var(--color-inhibition);
    }
    .effect-badge.effect-inhibits:hover {
      box-shadow: 0 2px 6px rgba(220, 38, 38, 0.2);
    }
    .effect-badge.effect-binds {
      background: var(--color-binding-light);
      color: var(--color-binding-dark);
      border-color: var(--color-binding);
    }
    .effect-badge.effect-binds:hover {
      box-shadow: 0 2px 6px rgba(124, 58, 237, 0.2);
    }

    /* NEW: Interaction Effect Badge (effect on downstream protein) */
    .interaction-effect-badge {
      font-family: var(--font-sans);
      background: var(--color-bg-tertiary);
      color: var(--color-text-primary);
      padding: 4px 10px;
      border-radius: var(--radius-sm);
      font-size: 11px;
      font-weight: 700;
      line-height: 1.4;
      border: 1px solid var(--color-border-medium);
      box-shadow: var(--shadow-sm);
      transition: all var(--transition-fast);
      display: inline-block;
      margin-right: 6px;
    }
    .interaction-effect-badge.interaction-effect-activates {
      background: var(--color-activation-light);
      color: var(--color-activation-dark);
      border-color: var(--color-activation);
    }
    .interaction-effect-badge.interaction-effect-inhibits {
      background: var(--color-inhibition-light);
      color: var(--color-inhibition-dark);
      border-color: var(--color-inhibition);
    }
    .interaction-effect-badge.interaction-effect-binds,
    .interaction-effect-badge.interaction-effect-regulates {
      background: var(--color-binding-light);
      color: var(--color-binding-dark);
      border-color: var(--color-binding);
    }

    /* NEW: Function Effect Badge (effect on function) */
    .function-effect-badge {
      font-family: var(--font-sans);
      background: var(--color-bg-tertiary);
      color: var(--color-text-primary);
      padding: 4px 10px;
      border-radius: var(--radius-sm);
      font-size: 11px;
      font-weight: 700;
      line-height: 1.4;
      border: 1px solid var(--color-border-medium);
      box-shadow: var(--shadow-sm);
      transition: all var(--transition-fast);
      display: inline-block;
      margin-left: 6px;
    }
    .function-effect-badge.function-effect-activates {
      background: var(--color-activation-light);
      color: var(--color-activation-dark);
      border-color: var(--color-activation);
    }
    .function-effect-badge.function-effect-inhibits {
      background: var(--color-inhibition-light);
      color: var(--color-inhibition-dark);
      border-color: var(--color-inhibition);
    }
    .function-effect-badge.function-effect-binds,
    .function-effect-badge.function-effect-regulates {
      background: var(--color-binding-light);
      color: var(--color-binding-dark);
      border-color: var(--color-binding);
    }

    /* NEW: Container for function name + effect badge */
    .function-name-with-effect {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    /* NEW: Container for interaction display + effect badge */
    .detail-interaction-with-effect {
      display: inline-flex;
      align-items: center;
      gap: 0;
    }

    .biological-cascade-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .biological-cascade-item {
      background: #fffbeb;
      color: #92400e;
      padding: 7px 10px;
      border-radius: 5px;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.5;
      border: 1px solid #fde68a;
      border-left: 3px solid #f59e0b;
      box-shadow: 0 1px 3px rgba(245, 158, 11, 0.1);
    }
    .specific-effects-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .specific-effect-chip {
      background: linear-gradient(135deg, #cffafe 0%, #a5f3fc 100%);
      color: #164e63;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 700;
      line-height: 1.5;
      border: none;
      box-shadow: 0 2px 6px rgba(6, 182, 212, 0.25);
    }
    /* Effect Type Tag with unified chip styling */
    .effect-type-tag {
      background: #e0e7ff;
      color: #3730a3;
      padding: 7px 10px;
      border-radius: 5px;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.4;
      border: 1px solid #c7d2fe;
      box-shadow: 0 1px 3px rgba(67, 56, 202, 0.1);
      transition: box-shadow 0.2s ease, border-color 0.2s ease;
      display: inline-block;
    }
    .effect-type-tag:hover {
      box-shadow: 0 2px 6px rgba(67, 56, 202, 0.15);
      border-color: #a5b4fc;
    }
    .effect-type-tag.activates {
      background: #d1fae5;
      color: #065f46;
      border-color: #a7f3d0;
      box-shadow: 0 1px 3px rgba(16, 185, 129, 0.1);
    }
    .effect-type-tag.activates:hover {
      box-shadow: 0 2px 6px rgba(16, 185, 129, 0.15);
      border-color: #6ee7b7;
    }
    .effect-type-tag.inhibits {
      background: #fecaca;
      color: #991b1b;
      border-color: #fca5a5;
      box-shadow: 0 1px 3px rgba(220, 38, 38, 0.1);
    }
    .effect-type-tag.inhibits:hover {
      box-shadow: 0 2px 6px rgba(220, 38, 38, 0.15);
      border-color: #f87171;
    }
    .effect-type-tag.binds {
      background: #e9d5ff;
      color: #6d28d9;
      border-color: #c4b5fd;
      box-shadow: 0 1px 3px rgba(124, 58, 237, 0.1);
    }
    .effect-type-tag.binds:hover {
      box-shadow: 0 2px 6px rgba(124, 58, 237, 0.15);
      border-color: #a78bfa;
    }
    /* Effect Type Badge with unified chip styling (for expanded rows) */
    .effect-type-badge {
      background: #e0e7ff;
      color: #3730a3;
      padding: 7px 10px;
      border-radius: 5px;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.4;
      border: 1px solid #c7d2fe;
      box-shadow: 0 1px 3px rgba(67, 56, 202, 0.1);
      transition: box-shadow 0.2s ease, border-color 0.2s ease;
      display: inline-block;
    }
    .effect-type-badge:hover {
      box-shadow: 0 2px 6px rgba(67, 56, 202, 0.15);
      border-color: #a5b4fc;
    }
    .effect-type-badge.activates {
      background: #d1fae5;
      color: #065f46;
      border-color: #a7f3d0;
      box-shadow: 0 1px 3px rgba(16, 185, 129, 0.1);
    }
    .effect-type-badge.activates:hover {
      box-shadow: 0 2px 6px rgba(16, 185, 129, 0.15);
      border-color: #6ee7b7;
    }
    .effect-type-badge.inhibits {
      background: #fecaca;
      color: #991b1b;
      border-color: #fca5a5;
      box-shadow: 0 1px 3px rgba(220, 38, 38, 0.1);
    }
    .effect-type-badge.inhibits:hover {
      box-shadow: 0 2px 6px rgba(220, 38, 38, 0.15);
      border-color: #f87171;
    }
    .effect-type-badge.binds {
      background: #e9d5ff;
      color: #6d28d9;
      border-color: #c4b5fd;
      box-shadow: 0 1px 3px rgba(124, 58, 237, 0.1);
    }
    .effect-type-badge.binds:hover {
      box-shadow: 0 2px 6px rgba(124, 58, 237, 0.15);
      border-color: #a78bfa;
    }
    /* Mechanism Badge - compact size matching interaction type badge */
    .mechanism-badge {
      background: #fde68a;
      color: #92400e;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 10px;
      font-weight: 600;
      line-height: 1.2;
      text-transform: uppercase;
      letter-spacing: 0.3px;
      border: 1px solid #fbbf24;
      box-shadow: 0 1px 3px rgba(245, 158, 11, 0.1);
      transition: box-shadow 0.2s ease, border-color 0.2s ease;
      display: inline-block;
    }
    .mechanism-badge:hover {
      box-shadow: 0 2px 6px rgba(245, 158, 11, 0.15);
      border-color: #fbbf24;
    }
    /* Unified Wrapper for Effect Badge */
    .expanded-effect-wrapper {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    .expanded-effect-wrapper.effect-activates {
      /* Container styling */
    }
    .expanded-effect-wrapper.effect-inhibits {
      /* Container styling */
    }
    .expanded-effect-wrapper.effect-binds {
      /* Container styling */
    }
    /* Unified Wrapper for Mechanism Badge */
    .expanded-mechanism-wrapper {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    /* 3D Wrapper for Cellular Process */
    .expanded-cellular-wrapper {
      padding: 8px 10px;
      border-radius: 6px;
      background: #faf5ff;
      box-shadow: 0 1px 3px rgba(168, 85, 247, 0.12);
      border: 1px solid #e9d5ff;
      border-left: 2px solid #a855f7;
      display: inline-block;
      width: 100%;
    }
    .expanded-cellular-wrapper .expanded-cellular-process {
      box-shadow: none;
      background: none;
      padding: 0;
      border: none;
    }
    /* 3D Wrapper for Effect Chips */
    .expanded-effect-chip-wrapper {
      padding: 6px 8px;
      border-radius: 6px;
      background: #ecfeff;
      box-shadow: 0 1px 3px rgba(6, 182, 212, 0.12);
      border: 1px solid #cffafe;
      border-left: 2px solid #06b6d4;
      display: inline-block;
    }
    .expanded-effect-chip-wrapper .expanded-effect-chip {
      box-shadow: 0 1px 2px rgba(6, 182, 212, 0.1);
      background: #cffafe;
    }
    /* 3D Wrapper for Cascade Items */
    .cascade-wrapper {
      padding: 8px 10px;
      border-radius: 6px;
      background: #fefce8;
      box-shadow: 0 2px 6px rgba(245, 158, 11, 0.15);
      border: 1px solid #fde68a;
      border-left: 3px solid #f59e0b;
      display: inline-block;
      width: 100%;
      position: relative;
    }
    .cascade-wrapper .cascade-flow-item {
      background: #fffbeb;
      color: #92400e;
      box-shadow: 0 1px 3px rgba(245, 158, 11, 0.12);
    }
    .cascade-wrapper .cascade-flow-item:hover {
      background: #fef3c7;
      box-shadow: 0 2px 6px rgba(245, 158, 11, 0.18);
    }
    .cascade-wrapper .cascade-flow-item::before {
      color: #d97706;
    }
    .cascade-wrapper .cascade-arrow-inline {
      color: #f59e0b;
    }
    /* 3D Wrapper for Evidence Cards */
    .expanded-evidence-wrapper {
      padding: 6px 8px;
      border-radius: 6px;
      background: #f8fafc;
      box-shadow: 0 1px 3px rgba(99, 102, 241, 0.1);
      border: 1px solid #e5e5e5;
      border-left: 2px solid #6366f1;
      display: inline-block;
      width: 100%;
      margin-bottom: 8px;
    }
    .expanded-evidence-wrapper .expanded-evidence-card {
      box-shadow: 0 1px 4px rgba(99, 102, 241, 0.12);
      margin: 0;
    }
    .expanded-evidence-wrapper .expanded-evidence-card:hover {
      box-shadow: 0 6px 16px rgba(99, 102, 241, 0.25), 0 3px 8px rgba(99, 102, 241, 0.15);
    }
    .muted-text {
      color: #6b7280;
      font-size: 13px;
    }
    .table-evidence-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .table-evidence-item {
      padding: 6px 10px;
      border-radius: 6px;
      background: #fff;
      border: 1px solid #e5e7eb;
      border-left: 3px solid #6366f1;
      box-shadow: 0 0 0 4px #f8fafc, 0 1px 3px rgba(99, 102, 241, 0.08);
    }
    .table-evidence-title {
      font-weight: 700;
      font-size: 13.5px;
      color: #0a0a0a;
    }
    .table-evidence-meta {
      font-size: 12.5px;
      font-weight: 500;
      color: #374151;
      margin-top: 2px;
    }
    .table-evidence-pmids {
      margin-top: 4px;
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .table-evidence-more {
      font-size: 12px;
      color: #6b7280;
    }
    .pmid-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .pmid-link {
      display: inline-block;
      background: #eef2ff;
      color: #3730a3;
      padding: 7px 10px;
      border-radius: 5px;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.4;
      text-decoration: none;
      border: 1px solid #c7d2fe;
      box-shadow: 0 1px 3px rgba(67, 56, 202, 0.1);
      transition: box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .pmid-link:hover {
      box-shadow: 0 2px 6px rgba(67, 56, 202, 0.15);
      border-color: #a5b4fc;
    }
    /* Function name with unified chip styling */
    .function-name-wrapper {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    .function-name-wrapper.activates {
      /* Container styling */
    }
    .function-name-wrapper.inhibits {
      /* Container styling */
    }
    .function-name-wrapper.binds {
      /* Container styling */
    }
    .function-name {
      padding: 7px 10px;
      border-radius: 5px;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.4;
      border: 1px solid;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      transition: box-shadow 0.2s ease, border-color 0.2s ease;
      display: inline-block;
    }
    .function-name.activates {
      background: #d1fae5;
      color: #065f46;
      border-color: #a7f3d0;
      box-shadow: 0 1px 3px rgba(16, 185, 129, 0.1);
    }
    .function-name.activates:hover {
      box-shadow: 0 2px 6px rgba(16, 185, 129, 0.15);
      border-color: #6ee7b7;
    }
    .function-name.inhibits {
      background: #fecaca;
      color: #991b1b;
      border-color: #fca5a5;
      box-shadow: 0 1px 3px rgba(220, 38, 38, 0.1);
    }
    .function-name.inhibits:hover {
      box-shadow: 0 2px 6px rgba(220, 38, 38, 0.15);
      border-color: #f87171;
    }
    .function-name.binds {
      background: #e9d5ff;
      color: #6d28d9;
      border-color: #c4b5fd;
      box-shadow: 0 1px 3px rgba(124, 58, 237, 0.1);
    }
    .function-name.binds:hover {
      box-shadow: 0 2px 6px rgba(124, 58, 237, 0.15);
      border-color: #a78bfa;
    }

    /* === Resizable columns === */
    .data-table th.resizable {
      position: relative;
      user-select: none;
    }
    .resize-handle {
      position: absolute;
      top: 0;
      right: 0;
      width: 8px;
      height: 100%;
      cursor: col-resize;
      background: transparent;
      transition: background 0.2s;
      z-index: 1;
    }
    .resize-handle:hover {
      background: rgba(79, 70, 229, 0.3);
    }
    .resize-handle:active {
      background: rgba(79, 70, 229, 0.5);
    }

    /* === Expand column === */
    .col-expand {
      cursor: default;
      padding: 12px 8px !important;
    }
    .expand-header-icon {
      font-size: 10px;
      color: #9ca3af;
      opacity: 0.5;
    }
    .expand-icon {
      display: inline-block;
      font-size: 12px;
      color: #6b7280;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      cursor: pointer;
      user-select: none;
      padding: 4px;
      border-radius: 4px;
    }
    .expand-icon:hover {
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.15) 100%);
      transform: scale(1.1);
    }
    .function-row:hover .expand-icon {
      color: #6366f1;
    }
    .function-row[data-expanded="true"] .expand-icon {
      transform: rotate(180deg);
      color: #8b5cf6;
      background: linear-gradient(135deg, rgba(124, 58, 237, 0.12) 0%, rgba(139, 92, 246, 0.18) 100%);
    }

    /* === Expandable rows === */
    .function-row {
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .function-row:hover {
      background: linear-gradient(90deg, #f8fafc 0%, #f5f5f5 100%) !important;
      box-shadow: 0 2px 6px rgba(79, 70, 229, 0.06);
      transform: translateX(2px);
    }
    .function-row[data-expanded="true"] {
      background: linear-gradient(90deg, #faf5ff 0%, #f5f3ff 100%) !important;
      border-left: 4px solid #8b5cf6;
      box-shadow: 0 2px 8px rgba(124, 58, 237, 0.1);
    }

    /* Expanded row - simplified with only left border */
    .expanded-row {
      display: none;
      background: #fafbfc;
      border-left: 4px solid #6366f1;
    }
    .expanded-row.show {
      display: table-row;
    }
    .expanded-row td {
      padding: 0 !important;
    }
    .expanded-content {
      padding: 36px 48px;
      animation: expandIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      background: #fafbfc;
    }
    @keyframes expandIn {
      from {
        opacity: 0;
        transform: translateY(-12px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    /* === NEW: Clean Two-Column Detail Layout === */

    /* Section containers */
    .detail-section {
      margin-bottom: 32px;
    }
    .detail-section:last-child {
      margin-bottom: 0;
    }

    /* Section headers */
    .detail-section-header {
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #6b7280;
      margin: 0 0 14px 0;
      padding-left: 0;
    }

    /* Subtle divider */
    .detail-divider {
      height: 1px;
      background: #e5e7eb;
      margin-bottom: 18px;
    }

    /* Two-column grid using definition list */
    .detail-grid {
      display: grid;
      grid-template-columns: 140px 1fr;
      gap: 14px 20px;
      align-items: baseline;
      margin: 0;
    }

    /* Labels (left column) */
    .detail-label {
      font-size: 13px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #9ca3af;
      text-align: right;
      margin: 0;
    }

    /* Values (right column) */
    .detail-value {
      font-size: 14px;
      line-height: 1.6;
      color: #374151;
      margin: 0;
    }

    /* Empty state */
    .detail-empty {
      color: #9ca3af;
      font-style: italic;
    }

    /* Special styling for interaction text */
    .detail-interaction {
      font-family: var(--font-mono);
      font-weight: 500;
    }
    .detail-arrow {
      color: #6b7280;
      margin: 0 6px;
    }

    /* Interaction Effect badge (colored, bold) - Effect on the downstream protein */
    .detail-effect {
      font-weight: 600;
      text-transform: uppercase;
      font-size: 12px;
      letter-spacing: 0.5px;
    }
    .detail-effect-activates {
      color: #059669;
    }
    .detail-effect-inhibits {
      color: #dc2626;
    }
    .detail-effect-binds {
      color: #7c3aed;
    }
    .detail-effect-regulates {
      color: #d97706;
    }
    .detail-effect-complex {
      color: #6366f1;
    }

    /* Function Effect badge (colored, slightly lighter) - Effect on specific function */
    .function-effect {
      font-weight: 600;
      text-transform: uppercase;
      font-size: 12px;
      letter-spacing: 0.5px;
      opacity: 0.9;
    }
    .function-effect-activates {
      color: #10b981;
    }
    .function-effect-inhibits {
      color: #f87171;
    }
    .function-effect-binds {
      color: #a78bfa;
    }
    .function-effect-regulates {
      color: #fbbf24;
    }
    .function-effect-complex {
      color: #818cf8;
    }

    /* Simple lists (no backgrounds, just bullets) */
    .detail-list {
      margin: 0;
      padding-left: 20px;
      list-style-position: outside;
    }
    .detail-list li {
      margin-bottom: 8px;
      line-height: 1.6;
      color: #374151;
    }
    .detail-list li:last-child {
      margin-bottom: 0;
    }
    .detail-list-ordered {
      list-style-type: decimal;
    }

    /* === NEW: Clean Expanded Content Text Styles === */

    /* Clean description text (no wrappers) */
    .effect-type-description,
    .mechanism-description,
    .cellular-process-text {
      font-size: 14px;
      line-height: 1.6;
      color: #374151;
      margin: 0;
    }

    /* Clean bullet lists for cascade and effects */
    .cascade-list,
    .effects-list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .cascade-list-item,
    .effects-list-item {
      padding: 8px 12px;
      background: #f9fafb;
      border-left: 3px solid #d97706;
      border-radius: 4px;
      font-size: 13px;
      line-height: 1.5;
      color: #374151;
      position: relative;
    }

    .cascade-list-item::before {
      content: '→';
      position: absolute;
      left: -18px;
      color: #d97706;
      font-weight: 700;
      font-size: 16px;
    }

    .effects-list-item {
      border-left-color: #0891b2;
    }

    .effects-list-item::before {
      content: '•';
      position: absolute;
      left: -16px;
      color: #0891b2;
      font-weight: 700;
      font-size: 18px;
    }

    /* === END NEW STYLES === */

    /* OLD: Expanded effect type with unified chip styling (kept for modal compatibility) === */
    .expanded-effect-type {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      width: 100%;
    }
    .expanded-effect-type.activates {
      /* Container styling */
    }
    .expanded-effect-type.inhibits {
      /* Container styling */
    }
    .expanded-effect-type.binds {
      /* Container styling */
    }
    .expanded-section--effect .effect-type-badge.activates {
      background: #d1fae5;
      border: 1px solid #a7f3d0;
      color: #065f46;
      box-shadow: 0 1px 3px rgba(16, 185, 129, 0.1);
      padding: 7px 10px;
      border-radius: 5px;
      font-weight: 700;
      font-size: 12px;
      line-height: 1.4;
      transition: box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .expanded-section--effect .effect-type-badge.activates:hover {
      box-shadow: 0 2px 6px rgba(16, 185, 129, 0.15);
      border-color: #6ee7b7;
    }
    .expanded-section--effect .effect-type-badge.inhibits {
      background: #fecaca;
      border: 1px solid #fca5a5;
      color: #991b1b;
      box-shadow: 0 1px 3px rgba(220, 38, 38, 0.1);
      padding: 7px 10px;
      border-radius: 5px;
      font-weight: 700;
      font-size: 12px;
      line-height: 1.4;
      transition: box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .expanded-section--effect .effect-type-badge.inhibits:hover {
      box-shadow: 0 2px 6px rgba(220, 38, 38, 0.15);
      border-color: #f87171;
    }
    .expanded-section--effect .effect-type-badge.binds {
      background: #e9d5ff;
      border: 1px solid #c4b5fd;
      color: #6d28d9;
      box-shadow: 0 1px 3px rgba(124, 58, 237, 0.1);
      padding: 7px 10px;
      border-radius: 5px;
      font-weight: 700;
      font-size: 12px;
      line-height: 1.4;
      transition: box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .expanded-section--effect .effect-type-badge.binds:hover {
      box-shadow: 0 2px 6px rgba(124, 58, 237, 0.15);
      border-color: #a78bfa;
    }
    .expanded-cellular-process {
      background: #faf5ff;
      color: #6d28d9;
      padding: 8px 10px;
      border-radius: 5px;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.5;
      border: 1px solid #e9d5ff;
      box-shadow: 0 1px 3px rgba(168, 85, 247, 0.1);
    }
    .expanded-cellular-process-text {
      display: block;
    }

    /* === Expanded specific effects === */
    .expanded-effects-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .expanded-effect-chip {
      background: #ecfeff;
      color: #155e75;
      padding: 7px 10px;
      border-radius: 5px;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.4;
      border: 1px solid #a5f3fc;
      box-shadow: 0 1px 3px rgba(6, 182, 212, 0.1);
      transition: box-shadow 0.2s ease, border-color 0.2s ease;
      flex: 1 1 200px;
      max-width: 100%;
    }
    .expanded-effect-chip:hover {
      box-shadow: 0 2px 6px rgba(6, 182, 212, 0.15);
      border-color: #67e8f9;
    }

    /* === Expanded biological cascade - VERTICAL FLOWCHART === */
    .cascade-flow-container {
      position: relative;
      padding-left: 20px;
      margin-top: 8px;
    }
    /* Vertical connecting line on the left */
    .cascade-flow-container::before {
      content: '';
      position: absolute;
      left: 8px;
      top: 12px;
      bottom: 12px;
      width: 3px;
      background: linear-gradient(180deg, #fbbf24 0%, #f59e0b 100%);
      border-radius: 2px;
    }
    .cascade-flow-item {
      position: relative;
      background: #fffbeb;
      color: #92400e;
      padding: 10px 14px;
      margin-bottom: 12px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 500;
      line-height: 1.6;
      border: 1px solid #fde68a;
      box-shadow: 0 1px 3px rgba(245, 158, 11, 0.1);
      transition: all 0.2s ease;
    }
    /* Connection dot for each step */
    .cascade-flow-item::before {
      content: '';
      position: absolute;
      left: -16px;
      top: 50%;
      transform: translateY(-50%);
      width: 8px;
      height: 8px;
      background: #f59e0b;
      border: 2px solid #fffbeb;
      border-radius: 50%;
      box-shadow: 0 0 0 2px #f59e0b;
      z-index: 1;
    }
    .cascade-flow-item:hover {
      background: #fef3c7;
      border-color: #fbbf24;
      box-shadow: 0 3px 8px rgba(245, 158, 11, 0.2);
      transform: translateX(2px);
    }
    /* Last item has no bottom margin */
    .cascade-flow-item:last-child {
      margin-bottom: 0;
    }

    /* === Expanded evidence - SIMPLIFIED === */
    .expanded-evidence-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .expanded-evidence-card {
      background: #ffffff;
      border: 1px solid #e5e7eb;
      border-left: 3px solid #6366f1;
      border-radius: 6px;
      padding: 12px 14px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.06);
      transition: box-shadow 0.2s ease, border-color 0.2s ease;
      cursor: pointer;
      position: relative;
    }
    .expanded-evidence-card::after {
      content: '↗';
      position: absolute;
      top: 12px;
      right: 12px;
      font-size: 14px;
      color: #9ca3af;
      opacity: 0;
      transition: opacity 0.2s ease;
    }
    .expanded-evidence-card:hover {
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
      border-left-color: #8b5cf6;
    }
    .expanded-evidence-card:hover::after {
      opacity: 1;
      color: #8b5cf6;
    }
    .expanded-evidence-title {
      font-weight: 700;
      font-size: 12px;
      color: #0a0a0a;
      margin-bottom: 4px;
      line-height: 1.4;
      padding-right: 20px;
    }
    .expanded-evidence-meta {
      font-size: 10px;
      font-weight: 600;
      color: #4b5563;
      margin-bottom: 6px;
      display: flex;
      flex-wrap: wrap;
      gap: 6px 8px;
      line-height: 1.4;
    }
    .expanded-evidence-meta-item {
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .expanded-evidence-quote {
      background: #f8fafc;
      border-left: 2px solid #c7d2fe;
      padding: 7px 10px 7px 12px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
      color: #1f2937;
      line-height: 1.5;
      font-style: italic;
      margin: 6px 0;
      box-shadow: inset 0 1px 2px rgba(0,0,0,0.04);
      position: relative;
    }
    .expanded-evidence-quote::before {
      color: #9ca3af;
      opacity: 0.4;
    }
    .expanded-evidence-quote::before {
      content: '"';
      font-size: 24px;
      color: #9ca3af;
      font-weight: bold;
      margin-right: 4px;
      line-height: 0;
    }
    .expanded-evidence-pmids {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 8px;
    }
    .expanded-pmid-badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: #eef2ff;
      color: #3730a3;
      padding: 7px 10px;
      border-radius: 5px;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.4;
      text-decoration: none;
      border: 1px solid #c7d2fe;
      box-shadow: 0 1px 3px rgba(67, 56, 202, 0.1);
      transition: box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .expanded-pmid-badge:hover {
      box-shadow: 0 2px 6px rgba(67, 56, 202, 0.15);
      border-color: #a5b4fc;
    }

    /* === Empty state === */
    .expanded-empty {
      color: #9ca3af;
      font-size: 14px;
      font-style: italic;
      padding: 16px 20px;
      text-align: center;
      background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
      border-radius: 8px;
      border: 2px dashed #d1d5db;
      transition: all 0.3s ease;
    }
    .expanded-empty:hover {
      border-color: #9ca3af;
      background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
    }
    .function-effect {
      font-size: 12px;
      padding: 4px 10px;
      border-radius: 4px;
      font-weight: 600;
    }
    .function-effect.activates {
      background: #d1fae5;
      color: #059669;
    }
    .function-effect.inhibits {
      background: #fee2e2;
      color: #dc2626;
    }
    .function-effect.binds {
      background: #f3e8ff;
      color: #7c3aed;
    }
    .function-description {
      margin: 10px 0;
      color: #374151;
      line-height: 1.7;
      font-size: 15px;
    }
    .biological-cascade-table {
      background: #fffbeb;
      padding: 7px 10px;
      border-radius: 5px;
      margin: 6px 0;
      border: 1px solid #fde68a;
      border-left: 3px solid #f59e0b;
      box-shadow: 0 1px 3px rgba(245, 158, 11, 0.1);
    }
    .cascade-title {
      font-weight: 600;
      font-size: 11px;
      text-transform: uppercase;
      color: #92400e;
      margin-bottom: 6px;
    }
    .cascade-step {
      color: #78350f;
      font-size: 12px;
      line-height: 1.5;
      margin: 4px 0;
    }
    .cascade-arrow-table {
      color: #f59e0b;
      font-weight: bold;
      margin: 0 4px;
    }
    .evidence-section {
      margin-top: 20px;
    }
    .evidence-divider {
      border: none;
      border-top: 2px solid #e5e7eb;
      margin: 16px 0;
    }
    .evidence-section-title {
      font-weight: 700;
      font-size: 15px;
      color: #6b7280;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 16px;
    }
    .evidence-paper {
      margin: 12px 0;
      padding: 14px;
      background: #f9fafb;
      border-left: 3px solid #4f46e5;
      border-radius: 6px;
    }
    .evidence-paper-divider {
      border: none;
      border-top: 1px dashed #d1d5db;
      margin: 16px 0;
    }
    .evidence-title {
      font-weight: 600;
      color: #1f2937;
      margin-bottom: 6px;
      font-size: 14px;
      line-height: 1.5;
    }
    .evidence-meta {
      color: #6b7280;
      font-size: 13px;
      margin-bottom: 6px;
    }
    .evidence-quote {
      color: #4b5563;
      font-style: italic;
      font-size: 13px;
      margin-top: 8px;
      padding: 8px 12px;
      background: white;
      border-radius: 4px;
      line-height: 1.6;
    }

    /* === Chat View Styles === */
    .chat-container {
      display: flex;
      flex-direction: column;
      height: 100%;
      max-width: 1000px;  /* Increased from 900px to accommodate padding */
      margin: 0 auto;
      padding: 24px;
      background: white;
      transition: padding-top 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* Shift chat container down when header is visible */
    .header.header-visible ~ #chat-view .chat-container {
      padding-top: 204px;
    }

    .chat-header {
      text-align: center;
      padding-bottom: 24px;
      border-bottom: 1px solid #e5e7eb;
      margin-bottom: 28px;
    }

    .chat-title {
      font-size: 28px;
      font-weight: 700;
      color: #1f2937;
      margin-bottom: 8px;
      letter-spacing: -0.02em;
    }

    .chat-subtitle {
      font-size: 15px;
      color: #6b7280;
      font-weight: 400;
      line-height: 1.5;
    }

    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 4px 20px 20px 4px;  /* Add right padding for scrollbar gutter, minimal left */
      display: flex;
      flex-direction: column;
      gap: 20px;
      min-height: 200px;
      max-height: calc(100vh - 400px);
    }

    .chat-message {
      display: flex;
      flex-direction: column;
      max-width: 80%;  /* Reduced from 85% for better scrollbar clearance */
      animation: fadeIn 0.3s ease-in;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .chat-message.user-message {
      align-self: flex-end;
    }

    .chat-message.assistant-message {
      align-self: flex-start;
    }

    .chat-message.system-message {
      align-self: center;
      max-width: 100%;
    }

    .chat-message.error-message {
      align-self: center;
      max-width: 100%;
    }

    .message-content {
      padding: 16px 20px;
      border-radius: 12px;
      font-size: 15px;
      line-height: 1.65;
      word-wrap: break-word;
    }

    .user-message .message-content {
      background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
      color: white;
      border-bottom-right-radius: 4px;
      box-shadow: 0 2px 8px rgba(79, 70, 229, 0.15);
    }

    .assistant-message .message-content {
      background: #fafbfc;
      color: #1f2937;
      border: 1px solid #e5e7eb;
      border-bottom-left-radius: 4px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }

    .system-message .message-content {
      background: #f0f9ff;
      color: #075985;
      border: 1px solid #bae6fd;
      text-align: center;
      font-size: 14px;
      padding: 14px 18px;
      border-radius: 10px;
      box-shadow: 0 1px 3px rgba(14, 165, 233, 0.08);
    }

    .error-message .message-content {
      background: #fef2f2;
      color: #991b1b;
      border: 1px solid #fecaca;
      text-align: center;
      font-size: 14px;
      padding: 14px 18px;
      border-radius: 10px;
      box-shadow: 0 1px 3px rgba(220, 38, 38, 0.08);
    }

    .message-label {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      margin-bottom: 8px;
      padding: 0 4px;
    }

    .user-message .message-label {
      color: #9ca3af;
      text-align: right;
    }

    .assistant-message .message-label {
      color: #9ca3af;
      text-align: left;
    }

    .chat-input-wrapper {
      display: flex;
      flex-direction: column;
      gap: 14px;
      padding-top: 24px;
      border-top: 1px solid #e5e7eb;
      margin-top: auto;
    }

    .chat-input {
      width: 100%;
      padding: 16px 18px;
      border: 1px solid #d1d5db;
      border-radius: 12px;
      font-size: 15px;
      font-family: inherit;
      resize: vertical;
      min-height: 80px;
      max-height: 200px;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      line-height: 1.6;
      background: #fafbfc;
    }

    .chat-input:focus {
      outline: none;
      border-color: #6366f1;
      background: #ffffff;
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.08), 0 1px 2px rgba(0, 0, 0, 0.05);
    }

    .chat-input::placeholder {
      color: #9ca3af;
    }

    .chat-send-btn {
      align-self: flex-end;
      padding: 13px 36px;
      background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
      color: white;
      border: none;
      border-radius: 999px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      min-width: 130px;
      box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
    }

    .chat-send-btn:hover:not(:disabled) {
      background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
      transform: translateY(-1px);
      box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);
    }

    .chat-send-btn:active:not(:disabled) {
      transform: translateY(0);
      box-shadow: 0 2px 6px rgba(79, 70, 229, 0.25);
    }

    .chat-send-btn:disabled {
      background: #d1d5db;
      cursor: not-allowed;
      transform: none;
      box-shadow: none;
    }

    /* Scrollbar styling for chat messages */
    .chat-messages::-webkit-scrollbar {
      width: 10px;  /* Slightly wider for better usability */
    }

    .chat-messages::-webkit-scrollbar-track {
      background: transparent;  /* Invisible track for cleaner look */
      margin: 8px 0;  /* Add margin to track for spacing */
    }

    .chat-messages::-webkit-scrollbar-thumb {
      background: #d4d4d4;  /* Slate-300 */
      border-radius: 999px;  /* Fully rounded for modern look */
      border: 2px solid white;  /* White border creates visual separation */
    }

    .chat-messages::-webkit-scrollbar-thumb:hover {
      background: #a3a3a3;  /* Slate-400 on hover */
    }
  </style>
</head>
<body class="dark-mode">
<div class="container">
  <!-- Invisible hover trigger -->
  <div class="header-trigger"></div>

  <!-- Header (classes/IDs aligned with index page) -->
  <div class="header">
    <h1 class="title" id="networkTitle">PLACEHOLDER_MAIN Interaction Network</h1>

    <div class="header-search-container">
      <div class="input-container">
        <input type="text" id="protein-input" placeholder="Search another protein..."/>
        <button id="query-button">Generate</button>
      </div>
    </div>

    <!-- Inline Controls Row: View Tabs + Research Settings -->
    <div class="header-controls-row">
      <div class="view-tabs">
        <button class="header-btn tab-btn active" onclick="switchView('graph')">Graph View</button>
        <button class="header-btn tab-btn" onclick="switchView('table')">Table View</button>
        <button class="header-btn tab-btn" onclick="switchView('chat')">Chat</button>
      </div>

      <details class="config-details-inline">
        <summary class="header-btn config-summary-inline">Research Settings</summary>
        <div class="config-content-inline">
          <div class="config-presets">
            <button class="preset-btn" onclick="setPreset(3,3)">Quick</button>
            <button class="preset-btn" onclick="setPreset(5,5)">Standard</button>
            <button class="preset-btn" onclick="setPreset(8,8)">Thorough</button>
          </div>
          <div class="config-inputs">
            <label class="config-label">
              <span class="config-label-text">Interactor Discovery Rounds:</span>
              <input type="number" id="interactor-rounds" class="config-input" min="3" max="8" value="3">
            </label>
            <label class="config-label">
              <span class="config-label-text">Function Mapping Rounds:</span>
              <input type="number" id="function-rounds" class="config-input" min="3" max="8" value="3">
            </label>
          </div>
        </div>
      </details>

      <button class="header-btn theme-toggle-btn" onclick="toggleTheme()" title="Toggle Light/Dark Mode" id="theme-toggle">
        <span id="theme-icon">☀️</span>
      </button>
    </div>

    <div id="job-notification" class="job-notification">
      <div class="mini-progress-wrapper" id="mini-progress-wrapper" style="display:none;">
        <span id="mini-progress-text">Initializing...</span>
        <div class="progress-bar-outer">
          <div class="progress-bar-inner" id="mini-progress-bar-inner"></div>
        </div>
        <button id="mini-cancel-btn" class="cancel-btn" onclick="cancelCurrentJob()" style="display:none;">Cancel</button>
      </div>
      <p id="notification-message"></p>
    </div>
  </div>

  <div id="network" class="view-container">
    <div class="controls">
      <button class="control-btn" onclick="zoomIn()" title="Zoom In">+</button>
      <button class="control-btn" onclick="zoomOut()" title="Zoom Out">−</button>
      <div class="control-divider"></div>
      <div class="filter-label">Show:</div>
      <button class="graph-filter-btn activates active" onclick="toggleGraphFilter('activates')" title="Show/Hide Activation">
        <span class="filter-dot activates"></span> Activates
      </button>
      <button class="graph-filter-btn inhibits active" onclick="toggleGraphFilter('inhibits')" title="Show/Hide Inhibition">
        <span class="filter-dot inhibits"></span> Inhibits
      </button>
      <button class="graph-filter-btn binds active" onclick="toggleGraphFilter('binds')" title="Show/Hide Binding">
        <span class="filter-dot binds"></span> Binds
      </button>
      <div class="control-divider"></div>
      <div class="filter-label">Depth:</div>
      <button class="graph-filter-btn depth-filter active" data-depth="1" onclick="toggleDepthFilter(1)" title="Show Depth 1 (Direct interactors)">1</button>
      <button class="graph-filter-btn depth-filter active" data-depth="2" onclick="toggleDepthFilter(2)" title="Show Depth 2 (Indirect interactors)">2</button>
      <button class="graph-filter-btn depth-filter active" data-depth="3" onclick="toggleDepthFilter(3)" title="Show Depth 3 (Extended network)">3</button>
      <div class="control-divider"></div>
      <button class="control-btn" onclick="refreshVisualization()" title="Refresh Visualization">⟳ Refresh</button>
    </div>

    <div class="info-panel"><strong>TIPS:</strong> Click arrows & nodes for details</div>

    <!-- Legend restored -->
    <div class="legend">
      <div class="legend-title">INTERACTION TYPES</div>
      <div class="legend-item">
        <div class="legend-arrow">
          <svg width="30" height="20"><line x1="0" y1="10" x2="20" y2="10" stroke="#059669" stroke-width="2"/><polygon points="20,10 26,10 23,7 23,13" fill="#059669"/></svg>
        </div>Activates
      </div>
      <div class="legend-item">
        <div class="legend-arrow">
          <svg width="30" height="20"><line x1="0" y1="10" x2="20" y2="10" stroke="#dc2626" stroke-width="2"/><line x1="23" y1="6" x2="23" y2="14" stroke="#dc2626" stroke-width="3"/></svg>
        </div>Inhibits
      </div>
      <div class="legend-item">
        <div class="legend-arrow">
          <svg width="30" height="20"><line x1="0" y1="8" x2="26" y2="8" stroke="#7c3aed" stroke-width="2"/><line x1="0" y1="12" x2="26" y2="12" stroke="#7c3aed" stroke-width="2"/></svg>
        </div>Binding
      </div>
      <div class="legend-item" style="margin-top:12px;padding-top:8px;border-top:1px solid #e5e7eb">
        <div class="legend-arrow">
          <svg width="30" height="20"><line x1="0" y1="10" x2="26" y2="10" stroke="#6b7280" stroke-width="2"/></svg>
        </div>Direct (physical)
      </div>
      <div class="legend-item">
        <div class="legend-arrow">
          <svg width="30" height="20"><line x1="0" y1="10" x2="26" y2="10" stroke="#6b7280" stroke-width="2" stroke-dasharray="8,4"/></svg>
        </div>Indirect (cascade)
      </div>
      <div class="legend-item">
        <div class="legend-arrow">
          <svg width="30" height="20"><line x1="0" y1="10" x2="26" y2="10" stroke="#ff8c00" stroke-width="2" stroke-dasharray="5,5"/></svg>
        </div>Incomplete (mediator missing)
      </div>
    </div>

    <svg id="svg"></svg>
  </div>

  <div id="table-view" class="view-container" style="display:none;">
    <div class="table-controls">
      <div class="table-controls-main">
        <div class="table-controls-left">
          <div class="search-container">
            <input type="text" id="table-search" class="table-search-input" placeholder="Search interactions..." oninput="handleSearchInput(event)">
            <button class="search-clear-btn" id="search-clear-btn" onclick="clearSearch()" style="display:none;">×</button>
          </div>
          <div class="filter-chips">
            <button class="filter-chip filter-active activates" onclick="toggleFilter('activates')">Activates</button>
            <button class="filter-chip filter-active inhibits" onclick="toggleFilter('inhibits')">Inhibits</button>
            <button class="filter-chip filter-active binds" onclick="toggleFilter('binds')">Binds</button>
          </div>
        </div>
        <div class="export-dropdown">
          <button class="export-btn" onclick="toggleExportDropdown()">Export ▼</button>
          <div class="export-dropdown-menu" id="export-dropdown-menu">
            <button class="export-option" onclick="exportToCSV(); closeExportDropdown();">Export as CSV</button>
            <button class="export-option" onclick="exportToExcel(); closeExportDropdown();">Export as Excel (.xlsx)</button>
          </div>
        </div>
      </div>
      <div id="filter-results" class="filter-results"></div>
    </div>
    <div class="table-wrapper">
      <table id="interactions-table" class="data-table">
        <thead>
          <tr>
            <th class="col-expand"><span class="expand-header-icon">▼</span></th>
            <th class="col-interaction resizable sortable" data-sort="interaction" onclick="sortTable('interaction')">Interaction <span class="sort-indicator"></span><span class="resize-handle"></span></th>
            <th class="col-effect resizable sortable" data-sort="effect" onclick="sortTable('effect')">Type <span class="sort-indicator"></span><span class="resize-handle"></span></th>
            <th class="col-function resizable sortable" data-sort="function" onclick="sortTable('function')">Function Affected <span class="sort-indicator"></span><span class="resize-handle"></span></th>
            <th class="col-effect-type resizable sortable" data-sort="effectType" onclick="sortTable('effectType')">Effect <span class="sort-indicator"></span><span class="resize-handle"></span></th>
            <th class="col-mechanism resizable sortable" data-sort="mechanism" onclick="sortTable('mechanism')">Mechanism <span class="sort-indicator"></span><span class="resize-handle"></span></th>
          </tr>
        </thead>
        <tbody id="table-body">
          <!-- Populated by buildTableView() -->
        </tbody>
      </table>
    </div>
  </div>

  <div id="chat-view" class="view-container" style="display:none;">
    <div class="chat-container">
      <div class="chat-header">
        <h2 class="chat-title">Network Assistant</h2>
        <p class="chat-subtitle">Ask questions about the protein interaction network</p>
      </div>
      <div id="chat-messages" class="chat-messages">
        <div class="chat-message system-message">
          <div class="message-content">
            👋 Hello! I'm here to help you understand this protein interaction network. Ask me anything about the visible proteins, their interactions, or biological functions.
          </div>
        </div>
      </div>
      <div class="chat-input-wrapper">
        <textarea
          id="chat-input"
          class="chat-input"
          placeholder="Ask about this network (e.g., 'What proteins interact with ATXN3?')..."
          rows="3"
        ></textarea>
        <button id="chat-send-btn" class="chat-send-btn" onclick="sendChatMessage()">
          <span id="chat-send-text">Send</span>
          <span id="chat-send-loading" style="display:none;">Thinking...</span>
        </button>
      </div>
    </div>
  </div>
</div>

<!-- Modal restored -->
<div id="modal" class="modal">
  <div class="modal-content">
    <div class="modal-header">
      <h2 class="modal-title" id="modalTitle">Details</h2>
      <button class="close-btn" onclick="closeModal()">&times;</button>
    </div>
    <div class="modal-body">
      <div id="modalBody"></div>
    </div>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
/* ===== Robust data load & hydration ===== */
let RAW, SNAP, CTX;

try {
  // Validate PLACEHOLDER was replaced
  RAW = PLACEHOLDER_JSON;

  if (!RAW || typeof RAW !== 'object') {
    throw new Error('Invalid data structure: RAW is not an object');
  }

  // Check if PLACEHOLDER wasn't replaced (safety check)
  const rawStr = JSON.stringify(RAW).substring(0, 100);
  if (rawStr.includes('PLACEHOLDER')) {
    throw new Error('Data embedding failed: template placeholder not replaced');
  }

  console.log('✅ Step 1: RAW data loaded', {
    keys: Object.keys(RAW),
    hasSnapshot: !!RAW.snapshot_json,
    hasCtx: !!RAW.ctx_json
  });

  SNAP = (RAW && RAW.snapshot_json && typeof RAW.snapshot_json === 'object') ? RAW.snapshot_json : (RAW || {});
  CTX  = (RAW && RAW.ctx_json && typeof RAW.ctx_json === 'object') ? RAW.ctx_json : {};
  SNAP.interactors = Array.isArray(SNAP.interactors) ? SNAP.interactors : [];
  if (!SNAP.main) SNAP.main = RAW.main || RAW.primary || 'Unknown';

  console.log('✅ Step 2: SNAP extracted', {
    main: SNAP.main,
    keys: Object.keys(SNAP),
    hasProteins: !!SNAP.proteins,
    hasInteractors: !!SNAP.interactors,
    hasInteractions: !!SNAP.interactions
  });

} catch (error) {
  console.error('❌ Data initialization failed:', error);
  document.getElementById('network').innerHTML =
    `<div style="padding: 60px 40px; text-align: center; color: #ef4444; font-family: system-ui, sans-serif;">
      <h2 style="font-size: 24px; margin-bottom: 16px;">⚠️ Failed to Load Visualization</h2>
      <p style="font-size: 16px; color: #6b7280; margin-bottom: 8px;">Error: ${error.message}</p>
      <p style="font-size: 14px; color: #9ca3af;">Check the browser console for details, then try refreshing the page.</p>
    </div>`;
  throw error; // Stop execution
}

function hydrateSnapshotWithCtx(snap, ctx){
  if (!ctx || !ctx.interactors) return snap;
  const byPrimary = new Map();
  ctx.interactors.forEach(ci => { if (ci && ci.primary) byPrimary.set(ci.primary, ci); });
  snap.interactors.forEach(si => {
    const ci = byPrimary.get(si.primary);
    if (!ci) return;
    // Replace/augment functions & evidence with richer ctx details
    if (Array.isArray(ci.functions) && ci.functions.length) si.functions = ci.functions;
    if (!si.evidence && Array.isArray(ci.evidence)) si.evidence = ci.evidence;
    if (!si.support_summary && ci.support_summary) si.support_summary = ci.support_summary;
    // Hydrate new fact-checker fields (optional, for future enhancement)
    if (ci.validation_status) si.validation_status = ci.validation_status;
    if (ci.validated !== undefined) si.validated = ci.validated;
  });
  // also allow ctx.main to override title if needed
  if (!snap.main && ctx.main) snap.main = ctx.main;
  return snap;
}
hydrateSnapshotWithCtx(SNAP, CTX);

console.log('✅ Step 3: Hydration complete');

document.getElementById('networkTitle').textContent = `${SNAP.main} Interaction Network`;

/* ===== Globals ===== */
let svg, g, width, height, simulation, zoomBehavior;
let graphInitialFitDone = false;
let fitToViewTimer = null;

let nodes = [], links = [];
// --- expansion toggle tracking ---
const expansionRegistry = new Map(); // ownerId -> {nodes:Set<string>, links:Set<string>}
const refCounts = new Map();         // entityId (nodeId or linkId) -> number of expansions referencing it
let baseNodes = null;                // Set<string> of initial nodes (never removed)
let baseLinks = null;                // Set<string> of initial links (never removed)

// Multi-graph cluster state
const CLUSTER_RADIUS = 500;          // Radius of each mini force-graph (2.5x larger for spacing)
const clusters = new Map();          // Map<centerId, {center, centerPos, members, localLinks}>
let nextClusterAngle = 0;            // For radial cluster positioning

/**
 * Calculate dynamic cluster separation based on interactor count
 * More interactors = wider spacing to prevent overlap
 */
function getClusterSeparation(interactorCount) {
  const baseDistance = 1200;         // Minimum separation for small clusters
  const scaleFactor = 15;            // Additional distance per interactor
  return baseDistance + (interactorCount * scaleFactor);
}

let currentZoom = 1;
let mainNodeRadius = 32;            // Bigger than interactors but not too fat
let interactorNodeRadius = 24;      // Standard size for interactor nodes
let linkGroup, nodeGroup;            // D3 selections for links and nodes

function initNetwork(){
  const container = document.getElementById('network');
  if (!container) return;

  const fallbackWidth = Math.max(window.innerWidth * 0.75, 960);
  const fallbackHeight = Math.max(window.innerHeight * 0.65, 640);
  width = container.clientWidth || fallbackWidth;
  height = container.clientHeight || fallbackHeight;

  svg = d3.select('#svg').attr('width', width).attr('height', height);

  graphInitialFitDone = false;
  if (fitToViewTimer) {
    clearTimeout(fitToViewTimer);
    fitToViewTimer = null;
  }

  zoomBehavior = d3.zoom()
    .scaleExtent([0.35, 2.8])
    .on('zoom', (ev) => {
      if (g) {
        g.attr('transform', ev.transform);
      }
      currentZoom = ev.transform.k;
    });

  svg.call(zoomBehavior);
  g = svg.append('g');

  // Arrowheads
  const defs = svg.append('defs');
  ['activate','inhibit','binding'].forEach(type=>{
    const color = type==='activate' ? '#059669' : type==='inhibit' ? '#dc2626' : '#7c3aed';
    if (type==='activate'){
      defs.append('marker').attr('id','arrow-activate').attr('viewBox','0 -5 10 10').attr('refX',10).attr('refY',0)
          .attr('markerWidth',10).attr('markerHeight',10).attr('orient','auto')
          .append('path').attr('d','M0,-5L10,0L0,5L3,0Z').attr('fill',color);
    } else if (type==='inhibit'){
      defs.append('marker').attr('id','arrow-inhibit').attr('viewBox','0 -5 10 10').attr('refX',10).attr('refY',0)
          .attr('markerWidth',10).attr('markerHeight',10).attr('orient','auto')
          .append('rect').attr('x',6).attr('y',-4).attr('width',3).attr('height',8).attr('fill',color);
    } else {
      const m = defs.append('marker').attr('id','arrow-binding').attr('viewBox','0 -5 10 10').attr('refX',10).attr('refY',0)
          .attr('markerWidth',10).attr('markerHeight',10).attr('orient','auto');
      m.append('rect').attr('x',4).attr('y',-4).attr('width',2).attr('height',8).attr('fill',color);
      m.append('rect').attr('x',7).attr('y',-4).attr('width',2).attr('height',8).attr('fill',color);
    }
  });

  // Node Gradients - Light Mode
  const mainGrad = defs.append('radialGradient').attr('id', 'mainGradient');
  mainGrad.append('stop').attr('offset', '0%').attr('stop-color', '#6366f1');
  mainGrad.append('stop').attr('offset', '100%').attr('stop-color', '#4338ca');

  const interactorGrad = defs.append('radialGradient').attr('id', 'interactorGradient');
  interactorGrad.append('stop').attr('offset', '0%').attr('stop-color', '#525252');
  interactorGrad.append('stop').attr('offset', '100%').attr('stop-color', '#404040');

  // Node Gradients - Dark Mode
  const mainGradDark = defs.append('radialGradient').attr('id', 'mainGradientDark');
  mainGradDark.append('stop').attr('offset', '0%').attr('stop-color', '#818cf8');
  mainGradDark.append('stop').attr('offset', '100%').attr('stop-color', '#6366f1');

  const interactorGradDark = defs.append('radialGradient').attr('id', 'interactorGradientDark');
  interactorGradDark.append('stop').attr('offset', '0%').attr('stop-color', '#404040');
  interactorGradDark.append('stop').attr('offset', '100%').attr('stop-color', '#262626');

  // Expanded Node Gradients - Distinct from main, darker glow
  const expandedGrad = defs.append('radialGradient').attr('id', 'expandedGradient');
  expandedGrad.append('stop').attr('offset', '0%').attr('stop-color', '#c7d2fe'); // Light indigo (indigo-200)
  expandedGrad.append('stop').attr('offset', '100%').attr('stop-color', '#a5b4fc'); // Light indigo (indigo-300)

  const expandedGradDark = defs.append('radialGradient').attr('id', 'expandedGradientDark');
  expandedGradDark.append('stop').attr('offset', '0%').attr('stop-color', '#a5b4fc'); // Light indigo (indigo-300)
  expandedGradDark.append('stop').attr('offset', '100%').attr('stop-color', '#818cf8'); // Light indigo (indigo-400)

   buildInitialGraph();
   // snapshot base graph ids (non-removable)
   baseNodes = new Set(nodes.map(n => n.id));
   baseLinks = new Set(links.map(l => l.id));
   createSimulation();
}

// calculateSpacing function removed - logic now inline in buildInitialGraph()

function arrowKind(rawArrow, intent, direction){
  const arrowValue = (rawArrow || '').toString().trim().toLowerCase();
  const intentValue = (intent || '').toString().trim().toLowerCase();

  // Comprehensive activation terms
  const activateTerms = ['activate','activates','activation','enhance','enhances','promote','promotes','upregulate','upregulates','stabilize','stabilizes'];
  // Comprehensive inhibition terms
  const inhibitTerms = ['inhibit','inhibits','inhibition','suppress','suppresses','repress','represses','downregulate','downregulates','block','blocks','reduce','reduces'];

  // Check arrow value for activation
  if (activateTerms.some(term => arrowValue.includes(term))) {
    return 'activates';
  }
  // Check arrow value for inhibition
  if (inhibitTerms.some(term => arrowValue.includes(term))) {
    return 'inhibits';
  }
  // Exact binding match
  if (arrowValue === 'binds' || arrowValue === 'binding') {
    return 'binds';
  }
  // Additional arrow value checks
  if (arrowValue === 'activator' || arrowValue === 'positive') {
    return 'activates';
  }
  if (arrowValue === 'negative') {
    return 'inhibits';
  }
  // If arrow is undirected/unknown, check intent
  if (!arrowValue || ['undirected','unknown','none','na','n/a','bidirectional','both','reciprocal','neutral','modulates','regulates'].includes(arrowValue)) {
    if (intentValue === 'activation' || intentValue === 'activates') return 'activates';
    if (intentValue === 'inhibition' || intentValue === 'inhibits') return 'inhibits';
    if (intentValue === 'binding') return 'binds';
    return 'binds';
  }
  // Check intent as fallback
  if (intentValue === 'binding') {
    return 'binds';
  }
  if (intentValue === 'activation') {
    return 'activates';
  }
  if (intentValue === 'inhibition') {
    return 'inhibits';
  }
  // Final fallback
  return ['activates','inhibits','binds'].includes(arrowValue) ? arrowValue : 'binds';
}

function isBiDir(dir){
  const v = (dir||'').toLowerCase();
  return v==='bidirectional'||v==='undirected'||v==='both'||v==='reciprocal';
}

function buildInitialGraph(){
  console.log('✅ Step 4: Starting buildInitialGraph');

  // NEW: Use proteins array for node creation, interactions array for links
  let proteins = SNAP.proteins || [];
  let interactions = SNAP.interactions || [];

  // Format detection logging
  console.log('📊 Data Format Detection:', {
    hasProteins: !!SNAP.proteins,
    hasInteractors: !!SNAP.interactors,
    proteinsCount: proteins.length,
    interactorsCount: (SNAP.interactors || []).length,
    interactionsCount: interactions.length,
    format: (proteins.length > 0) ? 'NEW' :
            (SNAP.interactors && SNAP.interactors.length > 0) ? 'LEGACY' : 'EMPTY'
  });

  // LEGACY FORMAT FALLBACK: Transform old interactors array to new proteins/interactions format
  if (proteins.length === 0 && SNAP.interactors && SNAP.interactors.length > 0) {
    console.log('Legacy format detected - transforming old interactors array to new format...');

    // Extract proteins from interactors
    proteins = [SNAP.main];
    SNAP.interactors.forEach(int => {
      if (int.primary && !proteins.includes(int.primary)) {
        proteins.push(int.primary);
      }
    });

    // Transform interactors to interactions array
    interactions = SNAP.interactors.map(int => {
      // For indirect interactions, source should be upstream_interactor, not main
      const isIndirect = (int.interaction_type || int.type || 'direct') === 'indirect';
      const upstream = int.upstream_interactor;

      // Convert query-relative direction to link-absolute semantics
      // This fixes arrow directionality mismatch between table and modal views
      const direction = int.direction || 'main_to_primary';
      let finalSource, finalTarget, finalDirection;

      if (direction === 'primary_to_main') {
        // Primary acts on main: S1P → ATF6
        finalSource = int.primary;
        finalTarget = SNAP.main;
        finalDirection = 'a_to_b';  // Link-absolute: source → target
      } else if (direction === 'main_to_primary') {
        // Main acts on primary: ATF6 → S1P
        finalSource = SNAP.main;
        finalTarget = int.primary;
        finalDirection = 'a_to_b';  // Link-absolute: source → target
      } else {
        // Bidirectional or undirected
        finalSource = SNAP.main;
        finalTarget = int.primary;
        finalDirection = 'bidirectional';
      }

      // Override source for indirect interactions with upstream mediator
      // If upstream is null/undefined, defaults to query protein (finalSource)
      if (isIndirect && upstream) {
        finalSource = upstream;
      }
      // Note: When upstream is missing for indirect, link comes from query protein
      // This shows "unknown mediator" pathway rather than false assignment

      return {
        source: finalSource,  // D3 will replace this with node object reference
        target: finalTarget,  // D3 will replace this with node object reference
        semanticSource: finalSource,  // Preserve original semantic source
        semanticTarget: finalTarget,  // Preserve original semantic target
        type: int.interaction_type || 'direct',
        arrow: int.arrow || 'binds',
        direction: finalDirection,
        _direction_is_link_absolute: true,  // Flag for modal rendering
        _original_direction: direction,  // Preserve for debugging
        intent: int.intent || 'binding',
        confidence: int.confidence || 0.5,
        interaction_type: int.interaction_type || 'direct',
        upstream_interactor: int.upstream_interactor || null,
        mediator_chain: int.mediator_chain || [],
        depth: int.depth || 1,
        functions: int.functions || [],
        evidence: int.evidence || [],
        pmids: int.pmids || [],
        support_summary: int.support_summary || '',
        all_arrows: int.all_arrows || [],
        all_intents: int.all_intents || [],
        all_directions: int.all_directions || []
      };
    });

    console.log(`Transformed ${SNAP.interactors.length} old interactors to new format`);
  }

  if (!SNAP.main || proteins.length === 0) {
    console.error('❌ buildInitialGraph: Missing data', {
      main: SNAP.main,
      proteins_count: proteins.length,
      interactions_count: interactions.length,
      snap_keys: Object.keys(SNAP),
      has_interactors: !!(SNAP.interactors && SNAP.interactors.length > 0)
    });

    // SHOW ERROR TO USER
    const networkDiv = document.getElementById('network');
    networkDiv.innerHTML = `
      <div style="padding: 60px 40px; text-align: center; color: #ef4444; font-family: system-ui, sans-serif;">
        <h2 style="font-size: 24px; margin-bottom: 16px;">⚠️ No Interaction Data Available</h2>
        <p style="font-size: 16px; color: #6b7280; margin-bottom: 8px;">
          ${SNAP.main ? `Protein: <strong>${SNAP.main}</strong>` : 'Unknown protein'}
        </p>
        <p style="font-size: 14px; color: #9ca3af; margin-bottom: 16px;">
          No proteins or interactions found in the database.
        </p>
        <p style="font-size: 14px; color: #9ca3af;">
          This might mean the protein hasn't been queried yet, or the query failed.
          Try searching for this protein from the home page.
        </p>
        <p style="font-size: 12px; color: #d1d5db; margin-top: 16px;">
          Check browser console for technical details.
        </p>
      </div>
    `;
    return;
  }

  // Count interactors (exclude main protein)
  const interactorCount = proteins.filter(p => p !== SNAP.main).length;

  // Calculate node radii - main is fixed, interactors scale with count
  mainNodeRadius = 72;  // CRITICAL FIX (Issue #7): Large main node for visual prominence (increased 20% for better visibility)
  interactorNodeRadius = Math.max(24, 30 - Math.floor(interactorCount/15));

  // Calculate spacing (only interactor ring, no function ring)
  // Dynamic ring radius: scales with interactor count
  // Formula: circumference = interactorCount * effectiveArcLength
  //          effectiveArcLength = baseArcLength * spacingScale
  //          spacingScale = 1 + (interactorCount / 20)
  //          radius = circumference / (2 * PI)
  const baseArcLength = 180;                      // Base arc length per node
  const spacingScale = 1 + (interactorCount / 20);  // Density scaling factor (sharper growth)
  const effectiveArcLength = baseArcLength * spacingScale;
  const requiredCircumference = Math.max(1, interactorCount) * effectiveArcLength;
  const calculatedRadius = requiredCircumference / (2 * Math.PI);

  // Apply bounds: min 750px, no max (let arc length formula determine natural spacing)
  const minR = 750;
  const interactorR = Math.max(minR, calculatedRadius);

  // Create main protein node (fixed at center)
  nodes.push({
    id: SNAP.main,
    label: SNAP.main,
    type: 'main',
    radius: mainNodeRadius,
    x: width/2,
    y: height/2,
    fx: width/2,
    fy: height/2
  });

  // Classify proteins as direct or indirect by scanning interactions
  const interactorProteins = proteins.filter(p => p !== SNAP.main);
  const directProteins = [];
  const indirectProteins = [];
  const indirectMap = new Map(); // protein -> {upstream, interactionType}

  interactorProteins.forEach(protein => {
    // A protein is DIRECT if there's ANY direct interaction from main to it
    // This handles mediators correctly (KEAP1 is both direct AND appears in indirect chains)
    const directInteraction = interactions.find(int =>
      int.target === protein &&
      int.source === SNAP.main &&
      ((int.interaction_type || int.type || 'direct') === 'direct')
    );

    if (directInteraction) {
      // DIRECT takes precedence - this protein directly interacts with main
      directProteins.push(protein);
    } else {
      // Only mark as indirect if NO direct interaction exists
      const indirectInteraction = interactions.find(int =>
        int.target === protein &&
        (int.interaction_type || int.type || 'direct') === 'indirect'
      );

      if (indirectInteraction) {
        indirectProteins.push(protein);
        indirectMap.set(protein, {
          upstream: indirectInteraction.upstream_interactor,
          type: indirectInteraction.interaction_type
        });
      } else {
        // Fallback: if not clearly direct or indirect, treat as direct
        directProteins.push(protein);
      }
    }
  });

  console.log(`Building initial graph: ${directProteins.length} direct, ${indirectProteins.length} indirect`);

  // Create direct interactor nodes (ring layout around main)
  directProteins.forEach((protein, i) => {
    const angle = (2*Math.PI*i)/Math.max(1, directProteins.length) - Math.PI/2;
    const x = width/2 + Math.cos(angle)*interactorR;
    const y = height/2 + Math.sin(angle)*interactorR;

    nodes.push({
      id: protein,
      label: protein,
      type: 'interactor',
      radius: interactorNodeRadius,
      x: x,
      y: y
    });
  });

  // Create indirect interactor nodes (positioned near upstream, or outer ring if no upstream)
  // NOTE: Positioning will be finalized after links are created
  indirectProteins.forEach((protein, i) => {
    // Temporary position - will be repositioned after links exist
    const angle = (2*Math.PI*i)/Math.max(1, indirectProteins.length) - Math.PI/2;
    const outerR = interactorR * 1.6; // Outer ring
    const x = width/2 + Math.cos(angle)*outerR;
    const y = height/2 + Math.sin(angle)*outerR;

    nodes.push({
      id: protein,
      label: protein,
      type: 'interactor',
      radius: interactorNodeRadius,
      x: x,
      y: y,
      // Mark as indirect for later repositioning
      _is_indirect: true,
      _upstream: indirectMap.get(protein)?.upstream
    });
  });

  // Create interaction links (handles direct, shared, and cross_link types)
  const linkIds = new Set();  // Track created links to avoid duplicates

  interactions.forEach(interaction => {
    const source = interaction.source;
    const target = interaction.target;

    if (!source || !target) {
      console.warn('buildInitialGraph: Interaction missing source or target', interaction);
      return;
    }

    // Verify both nodes exist
    let sourceNode = nodes.find(n => n.id === source);
    const targetNode = nodes.find(n => n.id === target);

    // Handle orphaned indirect interactors (missing upstream mediator)
    let isIncompletePathway = false;
    let missingMediator = null;

    if (!sourceNode && interaction.interaction_type === 'indirect' && targetNode) {
      // Fallback: connect orphaned indirect interactor to main protein
      console.warn(`buildInitialGraph: Upstream mediator '${source}' not found for indirect interactor '${target}'. Creating fallback link from main protein.`);
      sourceNode = nodes.find(n => n.id === SNAP.main);
      isIncompletePathway = true;
      missingMediator = source;
      // Update link to use main protein as source
      interaction.source = SNAP.main;
    }

    if (!sourceNode || !targetNode) {
      console.warn(`buildInitialGraph: Node not found for link ${source}-${target}`);
      return;
    }

    // Determine arrow type first (needed for duplicate detection)
    const arrow = arrowKind(
      interaction.arrow || 'binds',
      interaction.intent || 'binding',
      interaction.direction || 'main_to_primary'
    );

    // Create link ID with arrow type to allow multiple parallel links with different arrows
    // Example: "HDAC6-VCP-activates" and "HDAC6-VCP-binds" are both allowed
    const linkId = `${source}-${target}-${arrow}`;
    const reverseLinkId = `${target}-${source}-${arrow}`;

    // Check if this exact link already exists
    if (linkIds.has(linkId)) {
      console.warn(`buildInitialGraph: Duplicate link ${linkId}`);
      return;
    }

    // Check if reverse link exists (for bidirectional detection)
    const reverseExists = linkIds.has(reverseLinkId);
    if (reverseExists) {
      // Reverse link exists with same arrow type - mark both as bidirectional
      const existing = links.find(l => l.id === reverseLinkId);
      if (existing && !existing.isBidirectional) {
        existing.isBidirectional = true;
        existing.linkOffset = 0;
        existing.showBidirectionalMarkers = true;
      }
    }

    // Determine if bidirectional from direction field
    const isBidirectional = isBiDir(interaction.direction) || reverseExists;

    // Create link object
    const link = {
      id: linkId,
      source: source,
      target: target,
      type: 'interaction',  // All links are interaction type now (no function links)
      interactionType: interaction.interaction_type || 'direct',  // direct, indirect, shared, or cross_link
      arrow: arrow,
      intent: interaction.intent || 'binding',
      direction: interaction.direction || 'main_to_primary',
      data: interaction,  // Full interaction data (includes functions, evidence, etc.)
      isBidirectional: isBidirectional,
      linkOffset: reverseExists ? 1 : 0,  // Offset second link in bidirectional pair
      showBidirectionalMarkers: isBidirectional,
      confidence: interaction.confidence || 0.5,
      _incomplete_pathway: isIncompletePathway,  // Fallback link when upstream mediator missing
      _missing_mediator: missingMediator  // Name of the missing upstream protein
    };

    links.push(link);
    linkIds.add(linkId);
  });

  // === DETECT AND FIX ORPHANED SUBGRAPHS ===
  // Some indirect interactors may form disconnected subgraphs (e.g., circular dependencies)
  // where they reference each other but have no path to the main protein.
  // Perform BFS from main protein to find all reachable nodes, then create fallback links for orphans.

  function findOrphanedNodes(nodes, links, mainProteinId) {
    const visited = new Set();
    const queue = [mainProteinId];
    visited.add(mainProteinId);

    // BFS traversal from main protein
    while (queue.length > 0) {
      const current = queue.shift();

      // Find all links connected to current node (bidirectional search)
      links.forEach(link => {
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;

        // Check both directions (links are navigable both ways)
        if (sourceId === current && !visited.has(targetId)) {
          visited.add(targetId);
          queue.push(targetId);
        }
        if (targetId === current && !visited.has(sourceId)) {
          visited.add(sourceId);
          queue.push(sourceId);
        }
      });
    }

    // Return nodes NOT visited (= orphaned, not reachable from main)
    return nodes.filter(n => !visited.has(n.id) && n.type !== 'main');
  }

  const orphanedNodes = findOrphanedNodes(nodes, links, SNAP.main);

  if (orphanedNodes.length > 0) {
    console.warn(`Detected ${orphanedNodes.length} orphaned nodes (disconnected subgraph):`, orphanedNodes.map(n => n.id));

    // Create fallback links for each orphaned node
    orphanedNodes.forEach(orphanNode => {
      console.warn(`  Creating fallback link: ${SNAP.main} → ${orphanNode.id}`);

      // Determine the missing mediator (upstream interactor if available)
      const missingMediator = orphanNode._upstream || 'pathway';

      const fallbackLink = {
        id: `${SNAP.main}-${orphanNode.id}-fallback`,
        source: SNAP.main,
        target: orphanNode.id,
        type: 'interaction',
        interactionType: 'indirect',
        arrow: 'binds',
        intent: 'binding',
        direction: 'main_to_primary',
        data: { interaction_type: 'indirect' },
        isBidirectional: false,
        linkOffset: 0,
        showBidirectionalMarkers: false,
        confidence: 0.3,
        _incomplete_pathway: true,
        _missing_mediator: missingMediator,
        _orphaned_subgraph: true  // Flag to distinguish from single node orphans
      };

      links.push(fallbackLink);
      linkIds.add(fallbackLink.id);
    });
  }

  // Reposition indirect interactors near their upstream interactors (hybrid layout)
  // Group by upstream and position in small orbital rings around each upstream
  const upstreamGroups = new Map(); // upstream -> [indirect nodes]

  nodes.forEach(node => {
    if (node._is_indirect && node._upstream) {
      if (!upstreamGroups.has(node._upstream)) {
        upstreamGroups.set(node._upstream, []);
      }
      upstreamGroups.get(node._upstream).push(node);

      // Copy upstream info to node for force simulation
      node.upstream_interactor = node._upstream;
      node.interaction_type = 'indirect';
    }
  });

  console.log(`Repositioning ${upstreamGroups.size} groups of indirect interactors`);

  // Position each group around its upstream node
  upstreamGroups.forEach((indirectNodes, upstreamId) => {
    const upstreamNode = nodes.find(n => n.id === upstreamId);

    if (!upstreamNode) {
      console.warn(`Upstream node ${upstreamId} not found, using default position`);
      return;
    }

    console.log(`  ${upstreamId}: positioning ${indirectNodes.length} indirect interactors`);

    // Position indirect nodes in small orbital ring around upstream
    const orbitalRadius = 200; // Distance from upstream
    indirectNodes.forEach((node, idx) => {
      const angle = (2 * Math.PI * idx) / Math.max(indirectNodes.length, 1);
      node.x = upstreamNode.x + Math.cos(angle) * orbitalRadius;
      node.y = upstreamNode.y + Math.sin(angle) * orbitalRadius;
      // Don't fix position - let simulation adjust
      delete node.fx;
      delete node.fy;
    });
  });

  // No function nodes or function links - functions are now shown in modals
}

// ===== ORBITAL RING LAYOUT SYSTEM (No Force Simulation) =====

/**
 * Finds the parent node of a given node (the node that expanded to create it)
 * @param {string} nodeId - ID of node to find parent for
 * @returns {object|null} - Parent node object or null if no parent
 */
function findParentNode(nodeId) {
  // Check if this node is in any expansion registry
  for (const [parentId, registry] of expansionRegistry.entries()) {
    if (registry.nodes && registry.nodes.has(nodeId)) {
      return nodes.find(n => n.id === parentId);
    }
  }

  // For indirect interactors loaded in initial graph: check link data for upstream_interactor
  const indirectLink = links.find(l => {
    const target = (l.target && l.target.id) ? l.target.id : l.target;
    return target === nodeId && (
      (l.data?.interaction_type || l.data?.type || 'direct') === 'indirect' ||
      l.data?.upstream_interactor
    );
  });

  if (indirectLink && indirectLink.data?.upstream_interactor) {
    const upstreamId = indirectLink.data.upstream_interactor;
    const upstreamNode = nodes.find(n => n.id === upstreamId);
    if (upstreamNode) {
      return upstreamNode;
    }
  }

  // No parent found - this is a root-level node
  return null;
}

/**
 * Gets all children of a node (nodes it expanded)
 * @param {string} nodeId - Parent node ID
 * @returns {array} - Array of child node objects
 */
function getChildrenNodes(nodeId) {
  const registry = expansionRegistry.get(nodeId);
  if (!registry || !registry.nodes) return [];

  return nodes.filter(n => registry.nodes.has(n.id));
}

/**
 * CLUSTER MANAGEMENT
 * Each cluster is an independent mini force-graph
 */

/**
 * Calculate cluster radius based on member count
 * Uses same formula as buildInitialGraph for consistency
 * @param {number} memberCount - Number of members in cluster (excluding center)
 * @returns {number} Calculated radius in pixels
 */
function calculateClusterRadius(memberCount) {
  const baseArcLength = 180;
  const spacingScale = 1 + (memberCount / 20);  // Sharper growth for dense graphs
  const effectiveArcLength = baseArcLength * spacingScale;
  const requiredCircumference = Math.max(1, memberCount) * effectiveArcLength;
  const calculatedRadius = requiredCircumference / (2 * Math.PI);
  const minR = 400;
  return Math.max(minR, calculatedRadius);
}

/**
 * Creates a new cluster centered on a protein
 * @param {string} centerId - The protein ID at the center
 * @param {object} position - {x, y} position for cluster center
 * @param {number} initialMemberCount - Expected number of members (optional, for radius calculation)
 */
function createCluster(centerId, position, initialMemberCount = 0) {
  const centerNode = nodes.find(n => n.id === centerId);
  if (!centerNode) return;

  const radius = calculateClusterRadius(initialMemberCount);

  clusters.set(centerId, {
    center: centerId,
    centerPos: position,
    members: new Set([centerId]),
    localLinks: new Set(),
    isDragging: false,
    radius: radius  // Dynamic radius based on member count
  });

  // Fix the center node position
  centerNode.fx = position.x;
  centerNode.fy = position.y;
  centerNode.x = position.x;
  centerNode.y = position.y;

  console.log(`Created cluster for ${centerId} at (${position.x}, ${position.y}) with radius ${radius.toFixed(0)}px`);
}

/**
 * Adds a node to a cluster
 * @param {string} clusterId - Cluster center ID
 * @param {string} nodeId - Node to add
 */
function addNodeToCluster(clusterId, nodeId) {
  const cluster = clusters.get(clusterId);
  if (!cluster) return;

  cluster.members.add(nodeId);
}

/**
 * Finds which cluster a node belongs to
 * @param {string} nodeId
 * @returns {string|null} - Cluster center ID or null
 */
function getNodeCluster(nodeId) {
  for (const [clusterId, cluster] of clusters.entries()) {
    if (cluster.members.has(nodeId)) {
      return clusterId;
    }
  }
  return null;
}

/**
 * Classifies a link as intra-cluster, inter-cluster, shared, or indirect
 * @param {object} link
 * @returns {string} - 'intra-cluster', 'inter-cluster', 'shared', or 'indirect'
 */
function classifyLink(link) {
  // Indirect interaction links (cascade/pathway, not physical)
  if ((link.interaction_type || link.type || 'direct') === 'indirect') {
    return 'indirect';
  }

  // Shared interaction links (already marked)
  if (link.interactionType === 'shared' || link.interactionType === 'cross_link') {
    return 'shared';
  }

  const srcCluster = getNodeCluster(link.source.id || link.source);
  const tgtCluster = getNodeCluster(link.target.id || link.target);

  // No cluster info yet - treat as intra for now
  if (!srcCluster || !tgtCluster) {
    return 'intra-cluster';
  }

  // Same cluster = intra-cluster (has force)
  if (srcCluster === tgtCluster) {
    return 'intra-cluster';
  }

  // Different clusters = inter-cluster (no force)
  return 'inter-cluster';
}

/**
 * Calculates next cluster position (radial layout around canvas)
 * @param {number} interactorCount - Number of interactors in the cluster
 * @returns {{x: number, y: number}}
 */
function getNextClusterPosition(interactorCount = 5) {
  const centerX = width / 2;
  const centerY = height / 2;

  const angle = nextClusterAngle;
  nextClusterAngle += (Math.PI * 2) / 5; // Space for ~5 clusters around circle

  const separation = getClusterSeparation(interactorCount);
  const x = centerX + Math.cos(angle) * separation;
  const y = centerY + Math.sin(angle) * separation;

  return { x, y };
}

/**
 * Calculates position for a node using orbital rings
 * Each node orbits around its parent in a circle
 * @param {object} node - Node to position
 * @returns {{x: number, y: number}} - Calculated position
 */
function calculateOrbitalPosition(node) {
  const centerX = width / 2;
  const centerY = height / 2;

  // Main protein at canvas center
  if (node.type === 'main') {
    return { x: centerX, y: centerY };
  }

  // Find parent node
  const parent = findParentNode(node.id);

  // If no parent, this is a level-1 interactor (orbits main protein)
  if (!parent) {
    // Get all level-1 nodes
    const level1Nodes = nodes.filter(n => {
      const depth = depthMap.get(n.id);
      return n.type === 'interactor' && depth === 1;
    });

    const nodeIndex = level1Nodes.findIndex(n => n.id === node.id);
    if (nodeIndex === -1) {
      console.warn(`Node ${node.id} not found in level-1 list`);
      return { x: centerX + RADII.level1, y: centerY };
    }

    // Distribute evenly around main protein
    const angle = (2 * Math.PI * nodeIndex) / Math.max(level1Nodes.length, 1);
    const x = centerX + Math.cos(angle) * RADII.level1;
    const y = centerY + Math.sin(angle) * RADII.level1;

    return { x, y };
  }

  // This node has a parent - orbit around the parent
  const parentX = parent.x || centerX;
  const parentY = parent.y || centerY;

  // Get all siblings (nodes with same parent)
  const siblings = getChildrenNodes(parent.id);
  const nodeIndex = siblings.findIndex(n => n.id === node.id);

  if (nodeIndex === -1) {
    console.warn(`Node ${node.id} not found in siblings list`);
    return { x: parentX + 200, y: parentY };
  }

  // Distribute evenly around parent
  const angle = (2 * Math.PI * nodeIndex) / Math.max(siblings.length, 1);

  // Use fixed orbital radius (distance from parent)
  const orbitalRadius = 200;

  const x = parentX + Math.cos(angle) * orbitalRadius;
  const y = parentY + Math.sin(angle) * orbitalRadius;

  return { x, y };
}

/**
 * Custom D3 force: Maintains minimum and maximum distance from cluster center
 * Enforces orbital ring structure with minimum radius
 */
function forceClusterBounds(strength = 0.3) {
  return function force(alpha) {
    // For each cluster, maintain bounds for members using cluster-specific radius
    clusters.forEach((cluster, clusterId) => {
      const centerNode = nodes.find(n => n.id === cluster.center);
      if (!centerNode) return;

      // Use cluster-specific radius (dynamic based on member count)
      const clusterRadius = cluster.radius || CLUSTER_RADIUS; // Fallback to global constant if not set
      const minRadius = clusterRadius * 0.5;  // Minimum distance (40% of radius)
      const maxRadius = clusterRadius;  // Maximum distance (90% of radius)

      // Use fx/fy if set (center is fixed), otherwise fall back to x/y
      const centerX = Number.isFinite(centerNode.fx) ? centerNode.fx : centerNode.x;
      const centerY = Number.isFinite(centerNode.fy) ? centerNode.fy : centerNode.y;

      // Apply boundary force to cluster members (except center itself)
      cluster.members.forEach(memberId => {
        if (memberId === cluster.center) return; // Skip center node

        const member = nodes.find(n => n.id === memberId);
        if (!member) return;

        const dx = member.x - centerX;
        const dy = member.y - centerY;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance < 1) {
          // Node is at center, push it outward in random direction
          const angle = Math.random() * Math.PI * 2;
          member.vx += Math.cos(angle) * alpha * strength * 20;
          member.vy += Math.sin(angle) * alpha * strength * 20;
          return;
        }

        // Too close to center - PUSH AWAY STRONGLY
        // Use exponential scaling: closer = much stronger push
        if (distance < minRadius) {
          const proximityRatio = (minRadius - distance) / minRadius; // 0 to 1, higher = closer
          const pushMultiplier = 5 + (proximityRatio * 10); // 5x to 15x based on proximity
          const pushForce = ((minRadius - distance) / distance) * alpha * strength * pushMultiplier;
          member.vx += (dx / distance) * pushForce;
          member.vy += (dy / distance) * pushForce;
        }
        // Too far from center - PULL IN (gentle)
        else if (distance > maxRadius) {
          const pullForce = ((distance - maxRadius) / distance) * alpha * strength * 0.8;
          member.vx -= (dx / distance) * pullForce;
          member.vy -= (dy / distance) * pullForce;
        }
      });
    });
  };
}

/**
 * Custom D3 force: Attracts indirect interactors toward their upstream interactor
 * Creates visual clustering to show cascade/pathway relationships
 */
function forceIndirectClustering(strength = 0.2) {
  return function force(alpha) {
    nodes.forEach(node => {
      // Only apply to indirect interactors (those with upstream_interactor field)
      if (!node.upstream_interactor) return;

      // Find the upstream node
      const upstream = nodes.find(n => n.id === node.upstream_interactor);
      if (!upstream) return;

      // Calculate vector from indirect node to upstream node
      const dx = upstream.x - node.x;
      const dy = upstream.y - node.y;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance < 1) return; // Avoid division by zero

      // Apply attractive force toward upstream (gentle pull)
      const force = alpha * strength;
      node.vx += (dx / distance) * force * 10;
      node.vy += (dy / distance) * force * 10;
    });
  };
}

/**
 * Initializes cluster structure and node positions
 */
function initializeClusterLayout() {
  const centerX = width / 2;
  const centerY = height / 2;

  // Find main protein
  const mainNode = nodes.find(n => n.type === 'main');
  if (!mainNode) return;

  // Count interactors for dynamic radius calculation
  const interactors = nodes.filter(n => n.id !== mainNode.id);
  const interactorCount = interactors.length;

  // Create root cluster at canvas center with dynamic radius
  createCluster(mainNode.id, { x: centerX, y: centerY }, interactorCount);

  // Add all initial interactors to root cluster
  const rootCluster = clusters.get(mainNode.id);
  interactors.forEach((node, idx) => {
    // Position evenly around center in a circle using cluster's calculated radius
    const angle = (2 * Math.PI * idx) / interactors.length - Math.PI / 2;
    const radius = rootCluster.radius * 0.6; // Start within cluster (60% of calculated radius)
    node.x = centerX + Math.cos(angle) * radius;
    node.y = centerY + Math.sin(angle) * radius;

    addNodeToCluster(mainNode.id, node.id);
  });

  // Mark all initial links as intra-cluster
  links.forEach(link => {
    rootCluster.localLinks.add(link.id);
  });

  console.log(`Initialized cluster layout: 1 cluster with ${nodes.length} nodes, radius ${rootCluster.radius.toFixed(0)}px`);
}

/**
 * Creates force simulation with cluster-local forces
 */
function createSimulation(){
  const N = nodes.length;

  // Initialize cluster layout and node positions
  initializeClusterLayout();

  // Filter links: only intra-cluster links have force
  const intraClusterLinks = links.filter(link => {
    const type = classifyLink(link);
    return type === 'intra-cluster';
  });

  console.log(`Force simulation: ${links.length} total links, ${intraClusterLinks.length} with force`);

  // Create force simulation with cluster-local forces (very gentle)
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(intraClusterLinks).id(d=>d.id).distance(300).strength(0.1))
    .force('charge', d3.forceManyBody().strength(-20))
    .force('collision', d3.forceCollide().radius(d=>{
      if (d.type==='main') return mainNodeRadius + 15;
      if (d.type==='interactor') return interactorNodeRadius + 10;
      return 50;
    }).strength(0.3).iterations(2))
    .force('clusterBounds', forceClusterBounds())
    .force('indirect', forceIndirectClustering());

  // Simulation settings - very low velocity decay for minimal snapback
  simulation.alpha(0.5).alphaDecay(0.02).velocityDecay(0.2);

  // Auto-stop after settling
  simulation.on('end', () => {
    if (!graphInitialFitDone) {
      scheduleFitToView(80);
      graphInitialFitDone = true;
    }
  });

  // Initial fit
  if (!graphInitialFitDone) {
    scheduleFitToView(520, true);
  }

  // LINKS
  const link = g.append('g').selectAll('path')
    .data(links).enter().append('path')
    .attr('class', d=>{
      const arrow = d.arrow||'binds';
      let classes = 'link';
      if (arrow==='binds') classes += ' link-binding';
      else if (arrow==='activates') classes += ' link-activate';
      else if (arrow==='inhibits') classes += ' link-inhibit';
      else classes += ' link-binding';
      // Check data.interaction_type for indirect links
      if (d.data && (d.data.interaction_type || d.data.type || 'direct') === 'indirect') {
        classes += ' link-indirect';
      }
      // Check data._is_shared_link or interactionType for shared links
      if ((d.data && d.data._is_shared_link) || d.interactionType === 'shared' || d.interactionType === 'cross_link') {
        classes += ' link-shared';
      }
      // Check for incomplete pathway (fallback link)
      if (d._incomplete_pathway) {
        classes += ' link-incomplete';
      }
      return classes;
    })
    .attr('marker-start', d=>{
      const dir = (d.direction || '').toLowerCase();
      // marker-start shows arrow at source end
      // Use for bidirectional (both ends) only
      if (dir === 'bidirectional') {
        const a=d.arrow||'binds';
        if (a==='activates') return 'url(#arrow-activate)';
        if (a==='inhibits') return 'url(#arrow-inhibit)';
        return 'url(#arrow-binding)';
      }
      return null;
    })
    .attr('marker-end', d=>{
      const dir = (d.direction || '').toLowerCase();
      // marker-end shows arrow at target end (default for all directed arrows)
      // Support both query-relative (main_to_primary) AND absolute (a_to_b) directions
      // Query-relative: main_to_primary, primary_to_main, bidirectional
      // Absolute: a_to_b, b_to_a (used for shared links and database storage)
      if (dir === 'main_to_primary' || dir === 'primary_to_main' || dir === 'bidirectional' ||
          dir === 'a_to_b' || dir === 'b_to_a') {
        const a=d.arrow||'binds';
        if (a==='activates') return 'url(#arrow-activate)';
        if (a==='inhibits') return 'url(#arrow-inhibit)';
        return 'url(#arrow-binding)';
      }
      return null;
    })
    .attr('fill','none')
    .on('mouseover', function(){ d3.select(this).style('stroke-width','3.5'); svg.style('cursor','pointer'); })
    .on('mouseout',  function(){ d3.select(this).style('stroke-width',null);  svg.style('cursor',null); })
    .on('click', handleLinkClick);

  // NODES
  const node = g.append('g').selectAll('g')
    .data(nodes).enter().append('g')
    .attr('class','node-group')
    .call(d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended));

  node.each(function(d){
    const group = d3.select(this);
    if (d.type==='main'){
      group.append('circle')
        .attr('class','node main-node')
        .attr('r', mainNodeRadius)
        .style('cursor','pointer')
        .on('click', (ev)=>{ ev.stopPropagation(); handleNodeClick(d); });
      group.append('text').attr('class','node-label main-label').attr('dy',5).text(d.label);
    } else if (d.type==='interactor'){
      // Check if this interactor has been expanded (is a cluster center)
      const isExpanded = clusters.has(d.id);
      const isIndirect = d._is_indirect || false;
      let nodeClass = 'node';
      if (isExpanded) nodeClass += ' expanded-node';
      else if (isIndirect) nodeClass += ' interactor-node-indirect';
      else nodeClass += ' interactor-node';
      group.append('circle')
        .attr('class', nodeClass)
        .attr('r', interactorNodeRadius)
        .style('cursor','pointer')
        .on('click', (ev)=>{ ev.stopPropagation(); handleNodeClick(d); });
      group.append('text').attr('class','node-label').attr('dy',5).text(d.label);
    } else if (d.type==='function'){
      const display = d.label || 'Function';
      const temp = group.append('text').attr('class','function-label').text(display).attr('visibility','hidden');
      const bbox = temp.node().getBBox(); temp.remove();
      const pad=16, rectW=Math.max(bbox.width+pad*2, 110), rectH=Math.max(bbox.height+pad*1.5, 36);
      const nodeClass = d.isQueryFunction ? 'function-node-query' : 'function-node-interactor';
      const confClass = 'fn-solid';
      group.append('rect')
        .attr('class',`node function-node ${nodeClass} ${confClass}`)
        .attr('x', -rectW/2).attr('y', -rectH/2).attr('width', rectW).attr('height', rectH)
        .attr('rx',6).attr('ry',6)
        .on('click', (ev)=>{ ev.stopPropagation(); showFunctionModalFromNode(d); });
      group.append('text').attr('class','function-label').attr('dy',4).text(display).style('pointer-events','none');
    }
  });

  // Tick handler - updates positions on every frame
  simulation.on('tick', ()=>{
    // Use current selections (updated by updateGraphWithTransitions)
    if (linkGroup) linkGroup.attr('d', calculateLinkPath);
    if (nodeGroup) nodeGroup.attr('transform', d=> `translate(${d.x},${d.y})`);
  });

  // Store selections
  linkGroup = link;
  nodeGroup = node;
}

// Drag handlers for cluster-aware force simulation
function dragstarted(ev, d){
  console.log(`\n========== DRAG START ==========`);
  console.log(`Dragged node:`, { id: d.id, type: d.type, x: d.x, y: d.y, fx: d.fx, fy: d.fy });
  console.log(`Total clusters in system:`, clusters.size);
  console.log(`All cluster centers:`, Array.from(clusters.keys()));

  if (!ev.active) simulation.alphaTarget(0.3).restart();

  // Check if this is a cluster center
  const cluster = clusters.get(d.id);
  console.log(`\n🔍 CLUSTER LOOKUP for '${d.id}':`, cluster ? '✅ FOUND' : '❌ NOT FOUND');

  if (cluster) {
    console.log(`📊 CLUSTER DATA:`, {
      center: cluster.center,
      memberCount: cluster.members.size,
      members: Array.from(cluster.members),
      isDragging: cluster.isDragging,
      centerPos: cluster.centerPos
    });
  }

  if (cluster) {
    console.log(`✓ CLUSTER CENTER DRAG DETECTED`);
    console.log(`  Cluster members:`, Array.from(cluster.members));
    console.log(`  Cluster center pos:`, cluster.centerPos);

    // Mark cluster as being dragged
    cluster.isDragging = true;

    // Ensure drag start position is valid
    const startX = Number.isFinite(d.x) ? d.x : (d.fx || 0);
    const startY = Number.isFinite(d.y) ? d.y : (d.fy || 0);
    cluster.dragStartPos = { x: startX, y: startY };
    console.log(`  Drag start position:`, cluster.dragStartPos);

    // Store initial positions of all members
    cluster.memberStartPos = new Map();
    let fixedCount = 0;
    let notFoundCount = 0;
    let invalidPosCount = 0;

    cluster.members.forEach(memberId => {
      const member = nodes.find(n => n.id === memberId);
      if (!member) {
        console.log(`  ✗ Member '${memberId}' NOT FOUND in nodes array`);
        notFoundCount++;
        return;
      }

      const memberX = Number.isFinite(member.x) ? member.x : 0;
      const memberY = Number.isFinite(member.y) ? member.y : 0;

      if (memberX === 0 && memberY === 0) {
        console.log(`  ⚠ Member '${memberId}' has (0,0) position`);
        invalidPosCount++;
      }

      cluster.memberStartPos.set(memberId, { x: memberX, y: memberY });
      member.fx = memberX;
      member.fy = memberY;
      fixedCount++;

      console.log(`  ✓ Member '${memberId}': pos (${memberX.toFixed(1)}, ${memberY.toFixed(1)}) -> FIXED`);
    });

    console.log(`  Summary: ${fixedCount} fixed, ${notFoundCount} not found, ${invalidPosCount} invalid`);
  } else {
    console.log(`✓ REGULAR NODE DRAG`);
    d.fx = d.x;
    d.fy = d.y;
  }

  console.log(`================================\n`);
}

function dragged(ev, d){
  // Check if this is a cluster center
  const cluster = clusters.get(d.id);

  if (cluster && cluster.isDragging) {
    // Calculate cluster drag offset
    const dx = ev.x - cluster.dragStartPos.x;
    const dy = ev.y - cluster.dragStartPos.y;

    // Move all cluster members together
    let movedCount = 0;
    let notFoundCount = 0;
    let noStartPosCount = 0;
    const movedNodes = [];

    cluster.members.forEach(memberId => {
      const member = nodes.find(n => n.id === memberId);
      if (!member) {
        notFoundCount++;
        console.warn(`  [DRAG] Member '${memberId}' not found in nodes array!`);
        return;
      }

      const startPos = cluster.memberStartPos.get(memberId);
      if (!startPos) {
        noStartPosCount++;
        console.warn(`  [DRAG] No start pos for '${memberId}'`);
        return;
      }

      if (!Number.isFinite(startPos.x) || !Number.isFinite(startPos.y)) {
        console.warn(`  [DRAG] Invalid start pos for '${memberId}':`, startPos);
        return;
      }

      const newX = startPos.x + dx;
      const newY = startPos.y + dy;

      member.fx = newX;
      member.fy = newY;
      member.x = newX;
      member.y = newY;
      movedCount++;
      movedNodes.push(memberId);
    });

    // Update cluster center position
    cluster.centerPos = { x: ev.x, y: ev.y };

    // Log every 10 drag events to see what's moving
    if (!cluster._dragCounter) cluster._dragCounter = 0;
    cluster._dragCounter++;
    if (cluster._dragCounter === 1 || cluster._dragCounter % 10 === 0) {
      console.log(`\n🎯 [DRAG] Dragging cluster '${d.id}'`);
      console.log(`  - Offset: (${dx.toFixed(0)}, ${dy.toFixed(0)})`);
      console.log(`  - Moved ${movedCount}/${cluster.members.size} members`);
      console.log(`  - Moved nodes:`, movedNodes.slice(0, 5), movedNodes.length > 5 ? `... +${movedNodes.length - 5} more` : '');
      if (notFoundCount > 0 || noStartPosCount > 0) {
        console.warn(`  - Issues: ${notFoundCount} not found, ${noStartPosCount} no start pos`);
      }
    }
  } else if (cluster) {
    console.log(`[DRAG] Cluster found but isDragging=false for ${d.id}`);
    d.fx = ev.x;
    d.fy = ev.y;
  } else {
    // Regular node drag
    d.fx = ev.x;
    d.fy = ev.y;
  }
}

function dragended(ev, d){
  if (!ev.active) simulation.alphaTarget(0);

  // Check if this is a cluster center
  const cluster = clusters.get(d.id);
  if (cluster && cluster.isDragging) {
    console.log(`[DRAG END] Cluster ${d.id} - releasing members`);

    cluster.isDragging = false;
    cluster._dragCounter = 0; // Reset counter

    // Keep cluster center fixed at new position
    d.fx = ev.x;
    d.fy = ev.y;

    // Release member nodes so they can settle with local forces
    let releasedCount = 0;
    cluster.members.forEach(memberId => {
      if (memberId !== d.id) { // Don't release the center itself
        const member = nodes.find(n => n.id === memberId);
        if (member) {
          member.fx = null;
          member.fy = null;
          releasedCount++;
        }
      }
    });

    // Update cluster center position
    cluster.centerPos = { x: ev.x, y: ev.y };

    console.log(`[DRAG END] Released ${releasedCount} members, reheating simulation`);

    // Reheat simulation to settle members in new position
    reheatSimulation(0.2);
  } else {
    // Release non-center nodes (except cluster centers which stay fixed)
    if (!clusters.has(d.id)) {
      d.fx = null;
      d.fy = null;
    }
  }
}

/**
 * Calculates SVG path for a link (shared between render and update)
 */
function calculateLinkPath(d) {
  // Get source/target positions (handle both object and id references)
  const sourceNode = typeof d.source === 'object' ? d.source : nodes.find(n => n.id === d.source);
  const targetNode = typeof d.target === 'object' ? d.target : nodes.find(n => n.id === d.target);

  if (!sourceNode || !targetNode) {
    console.warn('Link missing source or target:', d);
    return 'M 0 0'; // Empty path
  }

  const sx = sourceNode.x || 0;
  const sy = sourceNode.y || 0;
  const tx = targetNode.x || 0;
  const ty = targetNode.y || 0;

  const dx = tx - sx;
  const dy = ty - sy;
  const dist = Math.max(1e-6, Math.sqrt(dx * dx + dy * dy));

  // Calculate node radii for edge offset
  const rS = sourceNode.type === 'main' ? mainNodeRadius : (sourceNode.type === 'interactor' ? interactorNodeRadius : 0);
  const rT = targetNode.type === 'main' ? mainNodeRadius : (targetNode.type === 'interactor' ? interactorNodeRadius : 0);

  // Calculate offset for bidirectional links
  let offset = 0;
  if (d.isBidirectional && d.type === 'interaction') {
    offset = d.linkOffset === 0 ? -10 : 10;
  }

  // Calculate perpendicular offset
  const perpX = -dy / dist * offset;
  const perpY = dx / dist * offset;

  // Calculate start/end points (offset from node centers)
  const x1 = sx + (dx / dist) * rS + perpX;
  const y1 = sy + (dy / dist) * rS + perpY;
  const x2 = tx - (dx / dist) * rT + perpX;
  const y2 = ty - (dy / dist) * rT + perpY;

  // Check if this is a shared link (interactor-to-interactor)
  const isShared = (d.data && d.data._is_shared_link) || d.interactionType === 'shared' || d.interactionType === 'cross_link';

  // Use curved path for bidirectional or shared links
  if ((d.isBidirectional && d.type === 'interaction') || isShared) {
    const midX = (x1 + x2) / 2;
    const midY = (y1 + y2) / 2;

    let curveX, curveY;

    // SHARED LINKS: Curve outward around the ring (away from center)
    if (isShared) {
      // Get center position (main protein node)
      const mainNode = nodes.find(n => n.type === 'main');
      const centerX = mainNode?.x || width / 2;
      const centerY = mainNode?.y || height / 2;

      // Calculate vector from center to midpoint (points outward)
      const toMidX = midX - centerX;
      const toMidY = midY - centerY;
      const toMidDist = Math.max(1e-6, Math.sqrt(toMidX * toMidX + toMidY * toMidY));

      // Calculate curve offset: base (clears main node) + scaled by link length
      // Longer links (opposite interactors) get more prominent curves
      const baseOffset = 160;  // Clears main node (72px) + larger margin for 750px ring
      const linkLengthFactor = Math.min(dist / 300, 1.8);  // Cap at 1.8x
      const totalOffset = baseOffset + (linkLengthFactor * 60);

      // Push control point outward from center
      const outwardX = (toMidX / toMidDist) * totalOffset;
      const outwardY = (toMidY / toMidDist) * totalOffset;
      curveX = midX + outwardX;
      curveY = midY + outwardY;
    } else {
      // BIDIRECTIONAL (non-shared): Use perpendicular offset for gentle curve
      curveX = midX + perpX;
      curveY = midY + perpY;
    }

    return `M ${x1} ${y1} Q ${curveX} ${curveY} ${x2} ${y2}`;
  }

  // Straight line for unidirectional links
  return `M ${x1} ${y1} L ${x2} ${y2}`;
}

/**
 * Updates all link paths based on current node positions
 */
function updateLinkPaths(linkSelection) {
  linkSelection.attr('d', calculateLinkPath);
}

// Drag handlers removed - static layout with fixed positions
// User can zoom/pan the entire graph, but nodes don't move individually

/* ===============================================================
   MODAL SYSTEM
   =============================================================== */

function openModal(titleHTML, bodyHTML){
  document.getElementById('modalTitle').innerHTML = titleHTML;
  document.getElementById('modalBody').innerHTML = bodyHTML;
  document.getElementById('modal').classList.add('active');

  // Wire up expandable function rows after modal opens
  setTimeout(() => {
    document.querySelectorAll('.function-expandable-row').forEach(row => {
      const header = row.querySelector('.function-row-header');
      if (header) {
        header.addEventListener('click', () => {
          row.classList.toggle('expanded');
        });
      }
    });
  }, 100);
}

function closeModal(){
  document.getElementById('modal').classList.remove('active');
}

document.getElementById('modal').addEventListener('click', (e)=>{
  if (e.target.id==='modal') closeModal();
});

/* Helper: Render an expandable function row */
function renderExpandableFunction(fn, mainProtein, interactorProtein, defaultInteractionEffect){
  const functionName = escapeHtml(fn.function || 'Function');

  // IMPORTANT: Separate interaction effect from function effect
  // 1. Interaction effect: Effect on the downstream protein (NEW: from fn.interaction_effect)
  // 2. Function effect: Effect on this specific function (from fn.arrow)

  // CRITICAL: Compute protein order and arrow direction from fn.interaction_direction
  // Each function can have its own direction (main_to_primary, primary_to_main, or bidirectional)
  const fnDirection = fn.interaction_direction || fn.direction || 'main_to_primary';

  let sourceProtein, targetProtein, arrowSymbol;
  if (fnDirection === 'primary_to_main') {
    // Interactor → Main
    sourceProtein = interactorProtein;
    targetProtein = mainProtein;
    arrowSymbol = '→';
  } else if (fnDirection === 'bidirectional') {
    // Main ↔ Interactor
    sourceProtein = mainProtein;
    targetProtein = interactorProtein;
    arrowSymbol = '↔';
  } else {
    // Default: main_to_primary (Main → Interactor)
    sourceProtein = mainProtein;
    targetProtein = interactorProtein;
    arrowSymbol = '→';
  }

  // NEW: Read interaction_effect from function data (fallback to defaultInteractionEffect for legacy)
  // For chain contexts, prefer specific arrows over generic 'binds'
  let interactionEffect = fn.interaction_effect || defaultInteractionEffect || 'binds';
  const fnArrow = fn.arrow || 'binds';

  // Avoid defaulting to 'binds' when better information is available from chain context
  if (interactionEffect === 'binds' && fn._context && fn._context.type === 'chain') {
    // Check if function arrow is more specific (activate/inhibit)
    if (fnArrow === 'activates' || fnArrow === 'inhibits') {
      interactionEffect = fnArrow; // Use function arrow as interaction effect for chains
    }
  }

  const normalizedFunctionArrow = arrowKind(fnArrow, fn.intent, fn.direction);
  const normalizedInteractionEffect = arrowKind(interactionEffect, fn.intent, fn.direction);
  const confidence = fn.confidence || 0;

  const functionArrowText = formatArrow(fnArrow);
  const interactionEffectText = formatArrow(interactionEffect);

  // Extract the immediate source protein (who acts on the target)
  // For chains: extract from chain context; for direct: use sourceProtein
  const sourceProteinForEffect = fn._context && fn._context.type === 'chain'
    ? extractSourceProteinFromChain(fn, targetProtein)
    : sourceProtein;

  // Build interaction effect badge (effect on the downstream protein)
  const interactionEffectBadge = `<span class="interaction-effect-badge interaction-effect-${normalizedInteractionEffect}">${interactionEffectText}</span>`;

  // Build function effect badge (effect on this specific function)
  const functionEffectBadge = `<span class="function-effect-badge function-effect-${normalizedFunctionArrow}">${functionArrowText}</span>`;

  // Legacy compatibility: effectBadge is now the interaction effect
  const effectBadge = interactionEffectBadge;

  // Build context badge (direct pair vs chain context)
  let contextBadge = '';
  if (fn._context) {
    const contextType = fn._context.type || 'direct';
    if (contextType === 'chain') {
      contextBadge = '<span class="context-badge" style="background: #f59e0b; color: white; font-size: 9px; padding: 2px 6px; border-radius: 3px; margin-left: 6px;">CHAIN CONTEXT</span>';
    } else if (contextType === 'direct') {
      contextBadge = '<span class="context-badge" style="background: #10b981; color: white; font-size: 9px; padding: 2px 6px; border-radius: 3px; margin-left: 6px;">DIRECT PAIR</span>';
    }
  }

  // Expanded content sections
  let expandedSections = '';

  // Effects Summary Section - Show BOTH interaction and function effects
  expandedSections += `
    <div class="function-detail-section section-effects-summary section-highlighted" style="background: var(--color-bg-secondary); border-left: 3px solid var(--color-primary);">
      <div class="function-section-title">🎯 Effects Summary</div>
      <div class="function-section-content">
        <div style="margin-bottom: 12px;">
          <div style="font-size: 11px; color: var(--color-text-secondary); margin-bottom: 4px; font-weight: 600; text-transform: uppercase;">Interaction Effect (on protein)</div>
          <div>
            <span class="detail-effect detail-effect-${normalizedInteractionEffect}" style="font-size: 0.875rem; padding: 0.25rem 0.75rem;">${interactionEffectText}</span>
            <span style="margin-left: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">${escapeHtml(targetProtein)} is ${toPastTense(interactionEffectText)} by ${escapeHtml(sourceProteinForEffect)}</span>
          </div>
        </div>
        <div>
          <div style="font-size: 11px; color: var(--color-text-secondary); margin-bottom: 4px; font-weight: 600; text-transform: uppercase;">Function Effect (on ${escapeHtml(functionName)})</div>
          <div>
            <span class="function-effect function-effect-${normalizedFunctionArrow}" style="font-size: 0.875rem; padding: 0.25rem 0.75rem;">${functionArrowText}</span>
            <span style="margin-left: 0.5rem; font-size: 0.875rem; color: var(--color-text-secondary);">${escapeHtml(functionName)} is ${toPastTense(functionArrowText)} by ${escapeHtml(sourceProteinForEffect)}</span>
          </div>
        </div>
      </div>
    </div>
  `;

  // Context Section - Show chain information for chain context functions
  if (fn._context && fn._context.type === 'chain' && fn._context.chain) {
    const chainArray = fn._context.chain;
    const queryProtein = fn._context.query_protein || '';
    if (Array.isArray(chainArray) && chainArray.length > 0 && queryProtein) {
      const fullChain = [queryProtein, ...chainArray].map(p => escapeHtml(p)).join(' → ');

      // Build Full Chain Cascade breakdown
      let cascadeHTML = '';

      // Build the cascade by analyzing each step in the chain
      const fullChainArray = [queryProtein, ...chainArray];

      if (fullChainArray.length >= 2) {
        cascadeHTML = '<div style="margin-top: 12px; padding: 12px; background: rgba(245, 158, 11, 0.1); border-radius: 6px;">';
        cascadeHTML += '<div style="font-size: 12px; font-weight: 600; color: #92400e; margin-bottom: 8px;">⚡ Full Chain Cascade:</div>';

        // For a chain like ATF6 → SREBP2 → HMGCR:
        // 1. ATF6 → SREBP2 [interaction arrow from query context]
        // 2. SREBP2 → HMGCR [THIS function's context shows the direct pair OR chain effect]
        // 3. ATF6 indirectly affects HMGCR via SREBP2

        for (let i = 0; i < fullChainArray.length - 1; i++) {
          const stepSource = fullChainArray[i];
          const stepTarget = fullChainArray[i + 1];

          // Try to determine arrow for this step
          let stepArrow = 'affects';
          let stepArrowColor = '#6b7280';

          // Last step (direct pair adjacent to target)
          if (i === fullChainArray.length - 2) {
            // This is the step involving the target protein
            // Try to infer direct pair effect from function data hints
            // Note: Currently the function shows chain effect, not direct pair
            // This is a limitation we're working around
            stepArrow = formatArrow(fnArrow);
            const arrowType = arrowKind(fnArrow, fn.intent, fn.direction);
            stepArrowColor = arrowType === 'activates' ? '#059669' : arrowType === 'inhibits' ? '#dc2626' : '#7c3aed';
          } else if (i === 0) {
            // First step (query → first intermediate)
            // Try to infer from interaction effect
            stepArrow = formatArrow(interactionEffect);
            const arrowType = arrowKind(interactionEffect, fn.intent, fn.direction);
            stepArrowColor = arrowType === 'activates' ? '#059669' : arrowType === 'inhibits' ? '#dc2626' : '#7c3aed';
          }

          cascadeHTML += `
            <div style="display: flex; align-items: center; margin: 6px 0; font-size: 12px;">
              <span style="font-weight: 500;">${escapeHtml(stepSource)}</span>
              <span style="margin: 0 8px; color: ${stepArrowColor}; font-weight: 600;">→ [${stepArrow}]</span>
              <span style="font-weight: 500;">${escapeHtml(stepTarget)}</span>
            </div>
          `;
        }

        // Add indirect effect summary
        const queryEffect = formatArrow(interactionEffect);
        const pairEffect = formatArrow(fnArrow);
        const indirectEffect = interactionEffect; // Simplified: query's effect propagates through chain

        cascadeHTML += `
          <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(245, 158, 11, 0.3);">
            <div style="font-size: 11px; color: #78350f; font-weight: 600; margin-bottom: 4px;">Indirect Effect:</div>
            <div style="font-size: 12px; color: #92400e;">
              <strong>${escapeHtml(queryProtein)}</strong> indirectly ${toPastTense(formatArrow(indirectEffect)).toLowerCase()}s
              <strong>${escapeHtml(targetProtein)}</strong> via ${toPastTense(queryEffect).toLowerCase()}ing
              <strong>${escapeHtml(sourceProteinForEffect)}</strong>
            </div>
          </div>
        `;

        cascadeHTML += '</div>';
      }

      expandedSections += `
        <div class="function-detail-section" style="background: #fffbeb; border-left: 3px solid #f59e0b;">
          <div class="function-section-title">🔗 Chain Context</div>
          <div class="function-section-content">
            <div style="font-size: 13px; color: #92400e;">
              This function emerges from the pathway: <strong>${fullChain}</strong>
            </div>
            <div style="font-size: 11px; color: #78350f; margin-top: 4px; font-style: italic;">
              The effects shown represent the compound result of the full cascade.
            </div>
            ${cascadeHTML}
          </div>
        </div>
      `;
    }
  }

  // Mechanism Section - Shows function effect badge + actual mechanism from cellular_process
  if (fn.cellular_process) {
    expandedSections += `
      <div class="function-detail-section section-mechanism section-highlighted">
        <div class="function-section-title">⚙️ Mechanism</div>
        <div class="function-section-content">
          <span class="effect-badge effect-${normalizedFunctionArrow}" style="font-size: 0.875rem; padding: 0.25rem 0.75rem;">${functionArrowText}</span>
          <span style="margin-left: 0.5rem;">${escapeHtml(fn.cellular_process)}</span>
        </div>
      </div>
    `;
  } else {
    // Fallback if cellular_process is missing
    expandedSections += `
      <div class="function-detail-section section-mechanism section-highlighted">
        <div class="function-section-title">⚙️ Mechanism</div>
        <div class="function-section-content">
          <span class="effect-badge effect-${normalizedFunctionArrow}" style="font-size: 0.875rem; padding: 0.25rem 0.75rem;">${functionArrowText}</span>
          <span style="margin-left: 0.5rem; color: var(--color-text-secondary);">
            ${fnArrow === 'activates' ? 'Stimulates or enhances activity' :
              fnArrow === 'inhibits' ? 'Suppresses or reduces activity' :
              'Physical association or binding'}
          </span>
        </div>
      </div>
    `;
  }

  // Effect Description - color-coded by function arrow type
  if (fn.effect_description) {
    expandedSections += `
      <div class="function-detail-section section-effect section-highlighted effect-${normalizedFunctionArrow}">
        <div class="function-section-title">💡 Effect</div>
        <div class="function-section-content">${escapeHtml(fn.effect_description)}</div>
      </div>
    `;
  }

  // Biological Cascade - MULTI-SCENARIO SUPPORT
  if (Array.isArray(fn.biological_consequence) && fn.biological_consequence.length > 0) {
    // Each array element represents a separate cascade scenario
    const cascadesHTML = fn.biological_consequence
      .map((cascade, idx) => {
        const text = (cascade == null ? '' : cascade).toString().trim();
        if (!text) return '';

        // Split by arrow and clean each step within this cascade
        const steps = text.split('→').map(s => s.trim()).filter(s => s.length > 0);
        if (steps.length === 0) return '';

        return `
          <div class="cascade-scenario">
            <div class="cascade-scenario-label">Scenario ${idx + 1}</div>
            <div class="cascade-flow-container">
              ${steps.map(step => `<div class="cascade-flow-item">${escapeHtml(step)}</div>`).join('')}
            </div>
          </div>
        `;
      })
      .filter(html => html.length > 0)
      .join('');

    if (cascadesHTML.length > 0) {
      const numCascades = fn.biological_consequence.filter(c => c && c.toString().trim()).length;
      const title = numCascades > 1
        ? `Biological Cascades (${numCascades} scenarios)`
        : 'Biological Cascade';

      expandedSections += `
        <div class="function-detail-section">
          <div class="function-section-title">${title}</div>
          ${cascadesHTML}
        </div>
      `;
    }
  }

  // Specific Effects
  if (Array.isArray(fn.specific_effects) && fn.specific_effects.length > 0) {
    expandedSections += `
      <div class="function-detail-section section-specific-effects section-highlighted">
        <div class="function-section-title">⚡ Specific Effects</div>
        <ul style="margin: 0; padding-left: 1.5em;">
          ${fn.specific_effects.map(eff => `<li class="function-section-content">${escapeHtml(eff)}</li>`).join('')}
        </ul>
      </div>
    `;
  }

  // Evidence
  if (Array.isArray(fn.evidence) && fn.evidence.length > 0) {
    expandedSections += `
      <div class="function-detail-section">
        <div class="function-section-title">Evidence & Publications</div>
        ${fn.evidence.map(ev => {
          const title = ev.paper_title || (ev.pmid ? `PMID: ${ev.pmid}` : 'Untitled');
          const metaParts = [];
          if (ev.journal) metaParts.push(escapeHtml(ev.journal));
          if (ev.year) metaParts.push(escapeHtml(ev.year));
          const meta = metaParts.length ? metaParts.join(' · ') : '';

          let pmidLinks = '';
          if (ev.pmid) {
            pmidLinks += `<a href="https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(ev.pmid)}" target="_blank" class="pmid-badge" onclick="event.stopPropagation();">PMID: ${escapeHtml(ev.pmid)}</a>`;
          }
          if (ev.doi) {
            pmidLinks += `<a href="https://doi.org/${escapeHtml(ev.doi)}" target="_blank" class="pmid-badge" onclick="event.stopPropagation();">DOI</a>`;
          }

          return `
            <div class="evidence-card">
              <div class="evidence-title">${escapeHtml(title)}</div>
              ${meta ? `<div class="evidence-meta">${meta}</div>` : ''}
              ${ev.relevant_quote ? `<div class="evidence-quote">"${escapeHtml(ev.relevant_quote)}"</div>` : ''}
              ${pmidLinks ? `<div style="margin-top: var(--space-2);">${pmidLinks}</div>` : ''}
            </div>
          `;
        }).join('')}
      </div>
    `;
  } else if (Array.isArray(fn.pmids) && fn.pmids.length > 0) {
    // Just PMIDs, no full evidence
    expandedSections += `
      <div class="function-detail-section">
        <div class="function-section-title">References</div>
        <div>
          ${fn.pmids.map(pmid => `<a href="https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(pmid)}" target="_blank" class="pmid-badge">PMID: ${escapeHtml(pmid)}</a>`).join('')}
        </div>
      </div>
    `;
  }

  // Build interaction pair display with BOTH badges
  // Format: [InteractionEffect] Source → Target  ||  FunctionName [FunctionEffect]
  let interactionDisplay = '';
  if (sourceProtein && targetProtein && arrowSymbol) {
    interactionDisplay = `
      <span class="detail-interaction-with-effect">
        ${interactionEffectBadge}
        <span class="detail-interaction">
          ${escapeHtml(sourceProtein)}
          <span class="detail-arrow">${arrowSymbol}</span>
          ${escapeHtml(targetProtein)}
        </span>
      </span>
    `;
  }

  return `
    <div class="function-expandable-row">
      <div class="function-row-header">
        <div class="function-row-left">
          <div class="function-expand-icon">▼</div>
          ${interactionDisplay}
          <span class="function-separator" style="margin: 0 8px; color: var(--color-text-secondary);">||</span>
          <div class="function-name-with-effect">
            <div class="function-name-display">${functionName}</div>
            ${functionEffectBadge}
          </div>
          ${contextBadge}
        </div>
      </div>
      <div class="function-expanded-content">
        ${expandedSections || '<div class="function-section-content" style="color: var(--color-text-secondary);">No additional details available</div>'}
      </div>
    </div>
  `;
}

function handleLinkClick(ev, d){
  ev.stopPropagation();
  if (!d) return;
  if (d.type==='function'){
    showFunctionModalFromLink(d);
  } else if (d.type==='interaction'){
    showInteractionModal(d);
  }
}

/* ===============================================================
   Interaction Modal: NEW DESIGN with Expandable Functions
   =============================================================== */
function showInteractionModal(link, clickedNode = null){
  const L = link.data || link;  // Link properties are directly on link object or in data

  // Use semantic source/target (biological direction) instead of D3's geometric source/target
  // Semantic fields preserve the biological meaning, while link.source/target are D3 node references
  const srcName = L.semanticSource || ((link.source && link.source.id) ? link.source.id : link.source);
  const tgtName = L.semanticTarget || ((link.target && link.target.id) ? link.target.id : link.target);
  const safeSrc = escapeHtml(srcName || '-');
  const safeTgt = escapeHtml(tgtName || '-');

  // Determine which protein was clicked (if any)
  // If called from node click, use clickedNode; otherwise determine from link
  let clickedProteinId = null;
  if (clickedNode) {
    clickedProteinId = clickedNode.id;
  }

  // Determine arrow direction
  // IMPORTANT: Direction field has different semantics for direct vs indirect interactions
  // - Direct: direction is QUERY-RELATIVE (main_to_primary = query→interactor)
  // - Indirect: direction is LINK-ABSOLUTE (main_to_primary = source→target after transformation)
  const direction = L.direction || link.direction || 'main_to_primary';
  const isIndirect = L.interaction_type === 'indirect';
  const directionIsLinkAbsolute = L._direction_is_link_absolute || isIndirect;

  let arrowSymbol = '↔';
  if (directionIsLinkAbsolute) {
    // Direction is LINK-ABSOLUTE (source→target semantics)
    // For indirect: direction already transformed to link context
    if (direction === 'bidirectional') arrowSymbol = '↔';
    else arrowSymbol = '→';  // Unidirectional: source→target
  } else {
    // Direction is QUERY-RELATIVE (main→primary semantics)
    // For direct: use standard query-relative logic
    if (direction === 'main_to_primary' || direction === 'a_to_b') arrowSymbol = '→';
    else if (direction === 'primary_to_main' || direction === 'b_to_a') arrowSymbol = '←';
  }

  // === BUILD INTERACTION METADATA SECTION ===
  let interactionMetadataHTML = '';

  // 0. Warning for incomplete pathway (missing mediator)
  if (link._incomplete_pathway && link._missing_mediator) {
    interactionMetadataHTML += `
      <div class="modal-detail-section" style="margin-bottom: var(--space-4); padding: var(--space-3); background: rgba(255, 140, 0, 0.15); border-left: 3px solid #ff8c00; border-radius: 4px;">
        <div style="display: flex; align-items: center; gap: var(--space-2);">
          <span style="font-size: 16px;">⚠️</span>
          <div>
            <div style="font-weight: 600; color: #ff8c00; margin-bottom: var(--space-1);">Incomplete Pathway</div>
            <div style="font-size: 13px; color: var(--color-text-secondary);">
              The upstream mediator <strong style="color: var(--color-text-primary);">${escapeHtml(link._missing_mediator)}</strong>
              is not present in the query results. This link connects directly to the main protein as a fallback.
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // 1. Summary (support_summary or summary)
  const summary = L.support_summary || L.summary;
  if (summary) {
    interactionMetadataHTML += `
      <div class="modal-detail-section" style="margin-bottom: var(--space-6);">
        <div class="modal-functions-header">Summary</div>
        <div class="modal-detail-value">${escapeHtml(summary)}</div>
      </div>
    `;
  }

  // 2. Interaction Type - AGGREGATE FROM FUNCTIONS (not from metadata)
  // This section will be built AFTER functions are loaded, moved below functions definition

  // 3. Mechanism (intent badge only, no text) - uses CSS class for dark mode support
  const intent = L.intent;
  if (intent) {
    interactionMetadataHTML += `
      <div class="modal-detail-section" style="margin-bottom: var(--space-6);">
        <div class="modal-detail-label">MECHANISM</div>
        <div class="modal-detail-value" style="margin-top: 8px;">
          <span class="mechanism-badge">
            ${escapeHtml(intent)}
          </span>
        </div>
      </div>
    `;
  }

  // === BUILD FUNCTIONS SECTION ===
  // Deduplication helper to remove duplicate function entries
  function deduplicateFunctions(functionArray) {
    const seen = new Set();
    return functionArray.filter(fn => {
      const key = `${fn.function || ''}|${fn.arrow || ''}|${fn.cellular_process || ''}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  const rawFunctions = Array.isArray(L.functions) ? L.functions : [];
  const functions = deduplicateFunctions(rawFunctions);
  let functionsHTML = '';

  // === BUILD INTERACTION TYPE SECTION (from interaction arrow, NOT functions) ===
  // IMPORTANT: This shows the effect on the downstream PROTEIN, not individual functions
  // Use the link's arrow field which represents the interaction effect from arrow determination

  const isDarkMode = document.body.classList.contains('dark-mode');
  const arrowColors = isDarkMode ? {
    'activates': { bg: '#065f46', text: '#a7f3d0', border: '#047857', label: 'ACTIVATES' },
    'inhibits': { bg: '#991b1b', text: '#fecaca', border: '#b91c1c', label: 'INHIBITS' },
    'binds': { bg: '#5b21b6', text: '#ddd6fe', border: '#6d28d9', label: 'BINDS' },
    'regulates': { bg: '#854d0e', text: '#fef3c7', border: '#a16207', label: 'REGULATES' },
    'complex': { bg: '#6366f1', text: '#e0e7ff', border: '#4f46e5', label: 'COMPLEX' }
  } : {
    'activates': { bg: '#d1fae5', text: '#047857', border: '#059669', label: 'ACTIVATES' },
    'inhibits': { bg: '#fee2e2', text: '#b91c1c', border: '#dc2626', label: 'INHIBITS' },
    'binds': { bg: '#ede9fe', text: '#6d28d9', border: '#7c3aed', label: 'BINDS' },
    'regulates': { bg: '#fef3c7', text: '#a16207', border: '#d97706', label: 'REGULATES' },
    'complex': { bg: '#e0e7ff', text: '#4f46e5', border: '#6366f1', label: 'COMPLEX' }
  };

  // Get interaction arrow (effect on the downstream protein)
  const interactionArrow = L.arrow || link.arrow || 'binds';
  const normalized = interactionArrow === 'activates' || interactionArrow === 'activate' ? 'activates'
                   : interactionArrow === 'inhibits' || interactionArrow === 'inhibit' ? 'inhibits'
                   : interactionArrow === 'regulates' || interactionArrow === 'regulate' ? 'regulates'
                   : interactionArrow === 'complex' ? 'complex'
                   : 'binds';

  // Build HTML for interaction type
  const interactionTypeHTML = `
    <div style="margin-bottom: 8px;">
      <div style="font-size: 11px; color: var(--color-text-secondary); margin-bottom: 4px; font-weight: 500;">
        <span class="detail-interaction">
          ${escapeHtml(srcName)}
          <span class="detail-arrow">${arrowSymbol}</span>
          ${escapeHtml(tgtName)}
        </span>
      </div>
      <div>
        <span class="interaction-type-badge" style="display: inline-block; padding: 2px 8px; background: ${arrowColors[normalized].bg}; color: ${arrowColors[normalized].text}; border: 1px solid ${arrowColors[normalized].border}; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; margin-right: 4px; margin-bottom: 4px;">
          ${arrowColors[normalized].label}
        </span>
      </div>
    </div>
  `;

  // Add to metadata HTML
  interactionMetadataHTML += `
    <div class="modal-detail-section" style="margin-bottom: var(--space-6);">
      <div class="modal-detail-label">INTERACTION TYPE</div>
      <div class="modal-detail-value" style="margin-top: 8px;">
        ${interactionTypeHTML}
      </div>
    </div>
  `;

  // Build type badge for function headers
  const interactionTitle = `${safeSrc} ${arrowSymbol} ${safeTgt}`;
  const isSharedInteraction = L._is_shared_link || false;
  const isIndirectInteraction = L.interaction_type === 'indirect';
  let functionTypeBadge = '';
  if (isSharedInteraction) {
    functionTypeBadge = '<span class="mechanism-badge" style="background: #9333ea; color: white; font-size: 9px; padding: 2px 6px;">SHARED</span>';
  } else if (isIndirectInteraction) {
    // Build full chain path display for INDIRECT label
    // Try to extract chain from first function with chain context
    let chainDisplay = '';
    const firstChainFunc = functions.find(f => f._context && f._context.type === 'chain' && f._context.chain);
    if (firstChainFunc && firstChainFunc._context.chain) {
      chainDisplay = buildFullChainPath(SNAP.main, firstChainFunc._context.chain, L);
    }

    // Fallback: use upstream_interactor if no chain found
    if (!chainDisplay && L.upstream_interactor) {
      chainDisplay = `${escapeHtml(SNAP.main)} → ${escapeHtml(L.upstream_interactor)} → ${escapeHtml(L.primary)}`;
    }

    functionTypeBadge = chainDisplay
      ? `<span class="mechanism-badge" style="background: #f59e0b; color: white; font-size: 9px; padding: 2px 6px;">${chainDisplay}</span>`
      : `<span class="mechanism-badge" style="background: #f59e0b; color: white; font-size: 9px; padding: 2px 6px;">INDIRECT</span>`;
  } else {
    functionTypeBadge = '<span class="mechanism-badge" style="background: #10b981; color: white; font-size: 9px; padding: 2px 6px;">DIRECT</span>';
  }

  if (functions.length > 0) {
    if (isIndirectInteraction) {
      // For indirect interactions: Don't group by direction - show all together
      // Direction is no longer query-relative, so grouping would be confusing
      const arrows = L.arrows || {};
      const arrowCount = Object.values(arrows).flat().filter((v, i, a) => a.indexOf(v) === i).length;

      functionsHTML = `<div class="modal-functions-header">Functions (${functions.length})${arrowCount > 1 ? ` <span style="background:#f59e0b;color:white;padding:2px 6px;border-radius:10px;font-size:10px;margin-left:8px;">${arrowCount} arrows</span>` : ''}</div>`;

      // Display all functions without direction grouping
      functionsHTML += `<div style="margin:16px 0;">
        ${functions.map(f => {
          const effectArrow = f.arrow || 'complex';
          return renderExpandableFunction(f, SNAP.main, L.primary, effectArrow);
        }).join('')}
      </div>`;

    } else {
      // For direct interactions: Group by INTERACTION DIRECTION
      // Functions should be grouped by which protein acts on which, showing the directionality
      const grp = {
        main_to_primary: [],
        primary_to_main: [],
        bidirectional: []
      };
      functions.forEach(f => grp[(f.direction || 'main_to_primary')].push(f));

      const arrows = L.arrows || {};
      const arrowCount = Object.values(arrows).flat().filter((v, i, a) => a.indexOf(v) === i).length;

      // Determine protein names for direction labels
      const queryProtein = SNAP.main;
      const interactorProtein = safeSrc === queryProtein ? safeTgt : safeSrc;

      functionsHTML = `<div class="modal-functions-header">Functions (${functions.length})${arrowCount > 1 ? ` <span style="background:#f59e0b;color:white;padding:2px 6px;border-radius:10px;font-size:10px;margin-left:8px;">${arrowCount} arrows</span>` : ''}</div>`;

      // Direction labels with arrow symbols based on interaction type
      const directionConfig = {
        main_to_primary: {
          source: queryProtein,
          target: interactorProtein,
          arrowSymbol: '→',
          color: '#3b82f6',  // Blue
          bg: '#dbeafe'
        },
        primary_to_main: {
          source: interactorProtein,
          target: queryProtein,
          arrowSymbol: '→',
          color: '#9333ea',  // Purple
          bg: '#f3e8ff'
        },
        bidirectional: {
          source: queryProtein,
          target: interactorProtein,
          arrowSymbol: '↔',
          color: '#059669',  // Green
          bg: '#d1fae5'
        }
      };

      ['main_to_primary', 'primary_to_main', 'bidirectional'].forEach(dir => {
        if (grp[dir].length) {
          const config = directionConfig[dir];
          functionsHTML += `<div style="">
            <div style="">
              <span class="detail-interaction">
                ${escapeHtml(config.source)}
                <span class="detail-arrow">${config.arrowSymbol}</span>
                ${escapeHtml(config.target)}
              </span> (${grp[dir].length})
            </div>
            ${grp[dir].map(f => {
              // Within each direction, show effect type badge
              const effectArrow = f.arrow || 'complex';
              const effectColor = effectArrow === 'activates' ? '#059669' : effectArrow === 'inhibits' ? '#dc2626' : '#6b7280';
              const effectSymbol = effectArrow === 'activates' ? '-->' : effectArrow === 'inhibits' ? '--|' : '--=';

              // Pass main and interactor proteins - let renderExpandableFunction compute direction from fn.interaction_direction
              return `<div style="">
                <div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">
                  <span style="display:inline-block;padding:2px 6px;background:${effectColor};color:white;border-radius:3px;font-size:9px;font-weight:600;">${effectSymbol} ${effectArrow.toUpperCase()}</span>
                  <span style="font-weight:600;font-size:11px;">${escapeHtml(f.function || 'Unknown Function')}</span>
                </div>
                ${renderExpandableFunction(f, queryProtein, interactorProtein, effectArrow)}
              </div>`;
            }).join('')}
          </div>`;
        }
      });
    }
  } else {
    const emptyMessage = isSharedInteraction
      ? 'Shared interactions may not include context-specific functions.'
      : 'No functions associated with this interaction.';
    functionsHTML = `
      <div class="modal-functions-header">Functions</div>
      <div style="padding: var(--space-4); color: var(--color-text-secondary); font-style: italic;">
        ${emptyMessage}
      </div>
    `;
  }

  // === BUILD EXPAND/COLLAPSE FOOTER (if called from node click) ===
  let footerHTML = '';
  if (clickedProteinId) {
    const proteinLabel = clickedProteinId;
    const isMainProtein = clickedProteinId === SNAP.main;
    const isExpanded = expanded.has(clickedProteinId);
    const canExpand = (depthMap.get(clickedProteinId) ?? 1) < MAX_DEPTH;
    const hasInteractions = true; // Always true for showInteractionModal (single link exists)

    if (isMainProtein) {
      // Main protein: show single "Find New Interactions" button
      footerHTML = `
        <div class="modal-footer" style="border-top: 1px solid var(--color-border); padding: 16px; background: var(--color-bg-secondary);">
          <button onclick="handleQueryFromModal('${clickedProteinId}')" class="btn-primary" style="padding: 8px 20px; background: #10b981; color: white; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; font-size: 14px; font-family: var(--font-sans); transition: background 0.2s;">
            Find New Interactions
          </button>
        </div>
      `;
    } else {
      // Interactor: show conditional Expand + Query buttons
      footerHTML = `
        <div class="modal-footer" style="border-top: 1px solid var(--color-border); padding: 16px; background: var(--color-bg-secondary);">
          <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
            ${canExpand && !isExpanded && hasInteractions ? `
              <button onclick="handleExpandFromModal('${clickedProteinId}')" class="btn-primary" style="padding: 8px 20px; background: #3b82f6; color: white; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; font-size: 14px; font-family: var(--font-sans); transition: background 0.2s;">
                Expand
              </button>
            ` : ''}
            ${canExpand && !isExpanded && !hasInteractions ? `
              <button disabled style="padding: 8px 20px; background: #d1d5db; color: #6b7280; border: none; border-radius: 6px; font-weight: 500; font-size: 14px; cursor: not-allowed; font-family: var(--font-sans);">
                Expand (No data)
              </button>
            ` : ''}
            ${isExpanded ? `
              <button onclick="handleCollapseFromModal('${clickedProteinId}')" class="btn-secondary" style="padding: 8px 20px; background: #ef4444; color: white; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; font-size: 14px; font-family: var(--font-sans); transition: background 0.2s;">
                Collapse
              </button>
            ` : ''}
            <button onclick="handleQueryFromModal('${clickedProteinId}')" class="btn-primary" style="padding: 8px 20px; background: #10b981; color: white; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; font-size: 14px; font-family: var(--font-sans); transition: background 0.2s;">
              Query
            </button>
            ${!canExpand && !isExpanded ? `
              <div style="padding: 8px 20px; background: #f3f4f6; color: #6b7280; border-radius: 6px; font-size: 13px; font-family: var(--font-sans); font-style: italic;">
                Max depth reached (${MAX_DEPTH})
              </div>
            ` : ''}
          </div>
          <div style="margin-top: 12px; font-size: 12px; color: var(--color-text-secondary); font-family: var(--font-sans);">
            Expand uses existing data • Query finds new interactions
          </div>
        </div>
      `;
    }
  }

  // === BUILD MODAL TITLE WITH TYPE BADGE ===
  // Determine interaction type and create badge
  const isShared = L._is_shared_link || false;
  // isIndirect already declared at line 5518 - reuse that variable
  const mediatorChain = L.mediator_chain || [];
  const chainDepth = L.depth || 1;

  // Check if THIS interaction's target is a mediator for OTHER indirect interactions
  // (e.g., KEAP1 is mediator in p62→KEAP1→NRF2)
  const isMediator = (tgtName === L.upstream_interactor || srcName === L.upstream_interactor);

  let typeBadge = '';
  if (isShared) {
    typeBadge = '<span class="mechanism-badge" style="background: #9333ea; color: white; font-size: 10px; padding: 3px 8px; margin-left: 12px;">SHARED</span>';
  } else if (isIndirect) {
    // Build full chain path display for INDIRECT label
    // Try to extract chain from first function with chain context
    let chainDisplay = '';
    const firstChainFunc = functions.find(f => f._context && f._context.type === 'chain' && f._context.chain);
    if (firstChainFunc && firstChainFunc._context.chain) {
      chainDisplay = buildFullChainPath(SNAP.main, firstChainFunc._context.chain, L);
    }

    // Fallback: use upstream_interactor if no chain found
    if (!chainDisplay && L.upstream_interactor) {
      chainDisplay = `${escapeHtml(SNAP.main)} → ${escapeHtml(L.upstream_interactor)} → ${escapeHtml(L.primary)}`;
    }

    typeBadge = chainDisplay
      ? `<span class="mechanism-badge" style="background: #f59e0b; color: white; font-size: 10px; padding: 3px 8px; margin-left: 12px;">${chainDisplay}</span>`
      : `<span class="mechanism-badge" style="background: #f59e0b; color: white; font-size: 10px; padding: 3px 8px; margin-left: 12px;">INDIRECT</span>`;
  } else if (isMediator) {
    // This protein is a mediator in indirect chains AND this link is direct
    typeBadge = `<span class="mechanism-badge" style="background: #10b981; color: white; font-size: 10px; padding: 3px 8px; margin-left: 12px;">DIRECT</span>
                 <span class="mechanism-badge" style="background: #6366f1; color: white; font-size: 10px; padding: 3px 8px; margin-left: 4px;">MEDIATOR</span>`;
  } else {
    typeBadge = '<span class="mechanism-badge" style="background: #10b981; color: white; font-size: 10px; padding: 3px 8px; margin-left: 12px;">DIRECT</span>';
  }

  let modalTitle = `
    <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
      <span style="font-size: 18px; font-weight: 600;">${safeSrc} ${arrowSymbol} ${safeTgt}</span>
      ${typeBadge}
    </div>
  `;

  // Add full chain display for ALL indirect interactions
  if (isIndirect) {
    let fullChainText = '';
    if (mediatorChain.length > 0) {
      // CRITICAL FIX (Issue #2): Use chain_with_arrows if available for typed arrows
      const chainWithArrows = L.chain_with_arrows || [];

      if (chainWithArrows.length > 0) {
        // CRITICAL FIX (Issue #1): For shared links, use correct protein perspective
        // Check if this is a shared link and reconstruct chain from shared interactor's perspective
        if (isShared && L._shared_between && L._shared_between.length >= 2) {
          // Find the shared interactor (not the main query protein)
          const sharedInteractor = L._shared_between.find(p => p !== SNAP.main);

          if (sharedInteractor) {
            // Filter chain segments to show only those starting from shared interactor
            const relevantSegments = chainWithArrows.filter(seg =>
              seg.from === sharedInteractor || chainWithArrows.indexOf(seg) > chainWithArrows.findIndex(s => s.from === sharedInteractor)
            );

            if (relevantSegments.length > 0) {
              const arrowSymbols = {
                'activates': ' <span style="color:#059669;font-weight:700;">--&gt;</span> ',
                'inhibits': ' <span style="color:#dc2626;font-weight:700;">--|</span> ',
                'binds': ' <span style="color:#7c3aed;font-weight:700;">---</span> ',
                'complex': ' <span style="color:#f59e0b;font-weight:700;">--=</span> '
              };

              fullChainText = relevantSegments.map((segment, i) => {
                const arrow = arrowSymbols[segment.arrow] || ' → ';
                if (i === relevantSegments.length - 1) {
                  return escapeHtml(segment.from) + arrow + escapeHtml(segment.to);
                } else {
                  return escapeHtml(segment.from) + arrow;
                }
              }).join('');
            } else {
              // Fallback: shared interactor → target
              fullChainText = `${escapeHtml(sharedInteractor)} → ${escapeHtml(tgtName)}`;
            }
          } else {
            // Couldn't find shared interactor, use default
            fullChainText = chainWithArrows.map((segment, i) => {
              const arrow = arrowSymbols[segment.arrow] || ' → ';
              return i === chainWithArrows.length - 1
                ? escapeHtml(segment.from) + arrow + escapeHtml(segment.to)
                : escapeHtml(segment.from) + arrow;
            }).join('');
          }
        } else {
          // NOT a shared link: Display full chain with typed arrows
          const arrowSymbols = {
            'activates': ' <span style="color:#059669;font-weight:700;">--&gt;</span> ',
            'inhibits': ' <span style="color:#dc2626;font-weight:700;">--|</span> ',
            'binds': ' <span style="color:#7c3aed;font-weight:700;">---</span> ',
            'complex': ' <span style="color:#f59e0b;font-weight:700;">--=</span> '
          };

          fullChainText = chainWithArrows.map((segment, i) => {
            const arrow = arrowSymbols[segment.arrow] || ' → ';
            if (i === chainWithArrows.length - 1) {
              // Last segment: show "from arrow to"
              return escapeHtml(segment.from) + arrow + escapeHtml(segment.to);
            } else {
              // Middle segments: only show "from arrow" (to avoid duplication)
              return escapeHtml(segment.from) + arrow;
            }
          }).join('');
        }
      } else {
        // FALLBACK: Generic arrows (old data or no chain_with_arrows)
        // CRITICAL FIX (Issue #1): For shared links, start chain from shared interactor
        let startProtein = SNAP.main;

        if (isShared && L._shared_between && L._shared_between.length >= 2) {
          const sharedInteractor = L._shared_between.find(p => p !== SNAP.main);
          if (sharedInteractor) {
            startProtein = sharedInteractor;
          }
        }

        const fullChain = [startProtein, ...mediatorChain, tgtName];
        fullChainText = fullChain.map(p => escapeHtml(p)).join(' → ');
      }
    } else if (L.upstream_interactor && L.upstream_interactor !== SNAP.main) {
      // Indirect with single upstream (no chain array but has upstream)
      // TODO: Could enhance to look up arrow types here too
      fullChainText = `${escapeHtml(SNAP.main)} → ${escapeHtml(L.upstream_interactor)} → ${escapeHtml(tgtName)}`;
    } else {
      // First-ring indirect: no mediator specified (pathway incomplete)
      fullChainText = `${escapeHtml(SNAP.main)} → ${escapeHtml(tgtName)} <span style="font-style: italic; color: #f59e0b;">(direct mediator unknown)</span>`;
    }

    modalTitle = `
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
          <span style="font-size: 18px; font-weight: 600;">${safeSrc} ${arrowSymbol} ${safeTgt}</span>
          ${typeBadge}
        </div>
        <div style="font-size: 13px; color: var(--color-text-secondary); font-weight: normal; padding: 4px 8px; background: var(--color-bg-tertiary); border-radius: 4px; border-left: 3px solid #f59e0b;">
          <strong>Full Chain:</strong> ${fullChainText}
        </div>
      </div>
    `;
  }

  // === COMBINE SECTIONS AND DISPLAY ===
  const fullModalContent = interactionMetadataHTML + functionsHTML + footerHTML;
  openModal(modalTitle, fullModalContent);
}

/* DEPRECATED: Old interactor modal - now using unified interaction modal for both arrows and nodes */
// showInteractorModal removed - nodes now use showInteractionModal with expand/collapse footer

/* Handle node click - show interaction modal with expand/collapse controls */
function handleNodeClick(node){
  // Find ALL links involving this node
  const nodeLinks = links.filter(l => {
    const src = (l.source && l.source.id) ? l.source.id : l.source;
    const tgt = (l.target && l.target.id) ? l.target.id : l.target;
    return src === node.id || tgt === node.id;
  });

  if (nodeLinks.length === 0) {
    // Fallback: show error message
    openModal(`Protein: ${escapeHtml(node.label || node.id)}`,
      '<div style="color:#6b7280; padding: 20px; text-align: center;">No interactions found for this protein.</div>');
  } else if (nodeLinks.length === 1) {
    // Single interaction - use standard modal
    showInteractionModal(nodeLinks[0], node);
  } else {
    // Multiple interactions - show aggregated modal
    showAggregatedInteractionsModal(nodeLinks, node);
  }
}

/* Show aggregated modal for nodes with multiple interactions */
function showAggregatedInteractionsModal(nodeLinks, clickedNode) {
  const nodeId = clickedNode.id;
  const nodeLabel = clickedNode.label || nodeId;

  // Group links by type (direct, indirect, shared)
  const directLinks = [];
  const indirectLinks = [];
  const sharedLinks = [];

  nodeLinks.forEach(link => {
    const L = link.data || {};
    if (L._is_shared_link) {
      sharedLinks.push(link);
    } else if (L.interaction_type === 'indirect') {
      indirectLinks.push(link);
    } else {
      directLinks.push(link);
    }
  });

  // Build sections HTML
  let sectionsHTML = '';

  // Helper to render a single interaction section
  function renderInteractionSection(link, sectionType) {
    const L = link.data || link;  // Link properties are directly on link object or in data

    // Use semantic source/target (biological direction) instead of D3's geometric source/target
    const srcName = L.semanticSource || ((link.source && link.source.id) ? link.source.id : link.source);
    const tgtName = L.semanticTarget || ((link.target && link.target.id) ? link.target.id : link.target);
    const safeSrc = escapeHtml(srcName || '-');
    const safeTgt = escapeHtml(tgtName || '-');

    // Determine arrow symbol
    // Support both query-relative AND absolute directions
    const direction = L.direction || link.direction || 'main_to_primary';
    let arrowSymbol = '↔';
    if (direction === 'main_to_primary' || direction === 'a_to_b') arrowSymbol = '→';
    else if (direction === 'primary_to_main' || direction === 'b_to_a') arrowSymbol = '←';

    // Type badge
    let typeBadgeHTML = '';
    if (sectionType === 'shared') {
      typeBadgeHTML = '<span class="mechanism-badge" style="background: #9333ea; color: white;">SHARED</span>';
    } else if (sectionType === 'indirect') {
      // Build full chain path display for INDIRECT label
      // Try to extract chain from first function with chain context
      let chainDisplay = '';
      const functions = L.functions || [];
      const firstChainFunc = functions.find(f => f._context && f._context.type === 'chain' && f._context.chain);
      if (firstChainFunc && firstChainFunc._context.chain) {
        chainDisplay = buildFullChainPath(SNAP.main, firstChainFunc._context.chain, L);
      }

      // Fallback: use upstream_interactor if no chain found
      if (!chainDisplay && L.upstream_interactor) {
        chainDisplay = `${escapeHtml(SNAP.main)} → ${escapeHtml(L.upstream_interactor)} → ${escapeHtml(L.primary)}`;
      }

      typeBadgeHTML = chainDisplay
        ? `<span class="mechanism-badge" style="background: #f59e0b; color: white;">${chainDisplay}</span>`
        : `<span class="mechanism-badge" style="background: #f59e0b; color: white;">INDIRECT</span>`;
    } else {
      typeBadgeHTML = '<span class="mechanism-badge" style="background: #10b981; color: white;">DIRECT</span>';
    }

    // Interaction title
    const interactionTitle = `${safeSrc} ${arrowSymbol} ${safeTgt}`;

    // Arrow type badge
    const arrow = L.arrow || link.arrow || 'binds';
    const normalizedArrow = arrow === 'activates' || arrow === 'activate' ? 'activates'
                          : arrow === 'inhibits' || arrow === 'inhibit' ? 'inhibits'
                          : 'binds';
    const isDarkMode = document.body.classList.contains('dark-mode');
    const arrowColors = isDarkMode ? {
      'activates': { bg: '#065f46', text: '#a7f3d0', border: '#047857', label: 'ACTIVATES' },
      'inhibits': { bg: '#991b1b', text: '#fecaca', border: '#b91c1c', label: 'INHIBITS' },
      'binds': { bg: '#5b21b6', text: '#ddd6fe', border: '#6d28d9', label: 'BINDS' }
    } : {
      'activates': { bg: '#d1fae5', text: '#047857', border: '#059669', label: 'ACTIVATES' },
      'inhibits': { bg: '#fee2e2', text: '#b91c1c', border: '#dc2626', label: 'INHIBITS' },
      'binds': { bg: '#ede9fe', text: '#6d28d9', border: '#7c3aed', label: 'BINDS' }
    };
    const colors = arrowColors[normalizedArrow];

    // Functions
    function deduplicateFunctions(functionArray) {
      const seen = new Set();
      return functionArray.filter(fn => {
        const key = `${fn.function || ''}|${fn.arrow || ''}|${fn.cellular_process || ''}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
    }

    const rawFunctions = Array.isArray(L.functions) ? L.functions : [];
    const functions = deduplicateFunctions(rawFunctions);

    let functionsHTML = '';
    if (functions.length > 0) {
      functionsHTML = functions.map(fn => {
        // Add interaction context label to each function box
        return `
          <div class="function-context-header" style="padding: 8px 12px; background: var(--color-bg-secondary); border-bottom: 1px solid var(--color-border); font-size: 11px; font-weight: 600; color: var(--color-text-secondary); display: flex; align-items: center; gap: 8px;">
            <span class="detail-interaction">
              ${safeSrc}
              <span class="detail-arrow">${arrowSymbol}</span>
              ${safeTgt}
            </span>
            ${typeBadgeHTML}
          </div>
          ${renderExpandableFunction(fn, srcName, tgtName, link.arrow)}
        `;
      }).join('');
    } else {
      const emptyMessage = sectionType === 'shared'
        ? 'Shared interactions may not include context-specific functions.'
        : 'No functions associated with this interaction.';
      functionsHTML = `
        <div style="padding: var(--space-4); color: var(--color-text-secondary); font-style: italic;">
          ${emptyMessage}
        </div>
      `;
    }

    return `
      <div class="interaction-section" style="margin-bottom: 24px; border: 1px solid var(--color-border); border-radius: 8px; overflow: hidden;">
        <div class="interaction-section-header" style="padding: 12px 16px; background: var(--color-bg-secondary); display: flex; align-items: center; justify-content: space-between; gap: 12px;">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-weight: 600; font-size: 14px;">${interactionTitle}</span>
            ${typeBadgeHTML}
          </div>
          <span class="interaction-type-badge" style="display: inline-block; padding: 2px 8px; background: ${colors.bg}; color: ${colors.text}; border: 1px solid ${colors.border}; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px;">
            ${colors.label}
          </span>
        </div>
        <div class="interaction-section-body" style="padding: 16px;">
          ${L.support_summary ? `
            <div style="margin-bottom: 16px;">
              <div class="modal-detail-label">SUMMARY</div>
              <div class="modal-detail-value">${escapeHtml(L.support_summary)}</div>
            </div>
          ` : ''}
          <div class="modal-functions-header">Biological Functions (${functions.length})</div>
          ${functionsHTML}
        </div>
      </div>
    `;
  }

  // CRITICAL FIX (Issue #6): Enhanced section headers for visual distinction
  // Render all sections with prominent, color-coded headers
  if (directLinks.length > 0) {
    sectionsHTML += `<div class="modal-section-divider" style="margin: 24px 0 16px 0; padding: 12px 16px; background: linear-gradient(135deg, #dbeafe 0%, #e0e7ff 100%); border-left: 6px solid #3b82f6; border-radius: 8px; box-shadow: 0 2px 4px rgba(59,130,246,0.1);">
      <h3 style="margin: 0; font-size: 16px; font-weight: 700; color: #1e40af; text-transform: uppercase; letter-spacing: 1px; display: flex; align-items: center; gap: 8px;">
        <span style="display: inline-block; width: 8px; height: 8px; background: #3b82f6; border-radius: 50%;"></span>
        DIRECT INTERACTIONS (${directLinks.length})
      </h3>
    </div>`;
    directLinks.forEach(link => {
      sectionsHTML += renderInteractionSection(link, 'direct');
    });
  }

  if (indirectLinks.length > 0) {
    sectionsHTML += `<div class="modal-section-divider" style="margin: 24px 0 16px 0; padding: 12px 16px; background: linear-gradient(135deg, #fef3c7 0%, #fed7aa 100%); border-left: 6px solid #f59e0b; border-radius: 8px; box-shadow: 0 2px 4px rgba(245,158,11,0.1);">
      <h3 style="margin: 0; font-size: 16px; font-weight: 700; color: #92400e; text-transform: uppercase; letter-spacing: 1px; display: flex; align-items: center; gap: 8px;">
        <span style="display: inline-block; width: 8px; height: 8px; background: #f59e0b; border-radius: 50%;"></span>
        INDIRECT INTERACTIONS (${indirectLinks.length})
      </h3>
    </div>`;
    indirectLinks.forEach(link => {
      sectionsHTML += renderInteractionSection(link, 'indirect');
    });
  }

  if (sharedLinks.length > 0) {
    sectionsHTML += `<div class="modal-section-divider" style="margin: 24px 0 16px 0; padding: 12px 16px; background: linear-gradient(135deg, #f3e8ff 0%, #fae8ff 100%); border-left: 6px solid #9333ea; border-radius: 8px; box-shadow: 0 2px 4px rgba(147,51,234,0.1);">
      <h3 style="margin: 0; font-size: 16px; font-weight: 700; color: #581c87; text-transform: uppercase; letter-spacing: 1px; display: flex; align-items: center; gap: 8px;">
        <span style="display: inline-block; width: 8px; height: 8px; background: #9333ea; border-radius: 50%;"></span>
        SHARED INTERACTIONS (${sharedLinks.length})
      </h3>
    </div>`;
    sharedLinks.forEach(link => {
      sectionsHTML += renderInteractionSection(link, 'shared');
    });
  }

  // Expand/collapse footer
  const isMainProtein = nodeId === SNAP.main;
  const isExpanded = expanded.has(nodeId);
  const canExpand = (depthMap.get(nodeId) ?? 1) < MAX_DEPTH;
  const hasInteractions = nodeLinks.length > 0;

  let footerHTML = '';
  if (isMainProtein) {
    // Main protein: show single "Find New Interactions" button
    footerHTML = `
      <div class="modal-footer" style="border-top: 1px solid var(--color-border); padding: 16px; background: var(--color-bg-secondary);">
        <button onclick="handleQueryFromModal('${nodeId}')" class="btn-primary" style="padding: 8px 20px; background: #10b981; color: white; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; font-size: 14px; font-family: var(--font-sans); transition: background 0.2s;">
          Find New Interactions
        </button>
      </div>
    `;
  } else {
    // Interactor: show conditional Expand + Query buttons
    footerHTML = `
      <div class="modal-footer" style="border-top: 1px solid var(--color-border); padding: 16px; background: var(--color-bg-secondary);">
        <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
          ${canExpand && !isExpanded && hasInteractions ? `
            <button onclick="handleExpandFromModal('${nodeId}')" class="btn-primary" style="padding: 8px 20px; background: #3b82f6; color: white; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; font-size: 14px; font-family: var(--font-sans); transition: background 0.2s;">
              Expand
            </button>
          ` : ''}
          ${canExpand && !isExpanded && !hasInteractions ? `
            <button disabled style="padding: 8px 20px; background: #d1d5db; color: #6b7280; border: none; border-radius: 6px; font-weight: 500; font-size: 14px; cursor: not-allowed; font-family: var(--font-sans);">
              Expand (No data)
            </button>
          ` : ''}
          ${isExpanded ? `
            <button onclick="handleCollapseFromModal('${nodeId}')" class="btn-secondary" style="padding: 8px 20px; background: #ef4444; color: white; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; font-size: 14px; font-family: var(--font-sans); transition: background 0.2s;">
              Collapse
            </button>
          ` : ''}
          <button onclick="handleQueryFromModal('${nodeId}')" class="btn-primary" style="padding: 8px 20px; background: #10b981; color: white; border: none; border-radius: 6px; font-weight: 500; cursor: pointer; font-size: 14px; font-family: var(--font-sans); transition: background 0.2s;">
            Query
          </button>
          ${!canExpand && !isExpanded ? `
            <div style="padding: 8px 20px; background: #f3f4f6; color: #6b7280; border-radius: 6px; font-size: 13px; font-family: var(--font-sans); font-style: italic;">
              Max depth reached (${MAX_DEPTH})
            </div>
          ` : ''}
        </div>
        <div style="margin-top: 12px; font-size: 12px; color: var(--color-text-secondary); font-family: var(--font-sans);">
          Expand uses existing data • Query finds new interactions
        </div>
      </div>
    `;
  }

  const modalTitle = `${escapeHtml(nodeLabel)} - All Interactions (${nodeLinks.length})`;
  const modalContent = `
    <div style="max-height: 70vh; overflow-y: auto; padding: 16px;">
      ${sectionsHTML}
    </div>
    ${footerHTML}
  `;

  openModal(modalTitle, modalContent);
}

/* Helper functions for expand/collapse from modal */
function handleExpandFromModal(proteinId){
  closeModal();
  const node = nodes.find(n => n.id === proteinId);
  if (node) {
    expandInteractor(node);
  }
}

function handleCollapseFromModal(proteinId){
  closeModal();
  collapseInteractor(proteinId);
}

async function handleQueryFromModal(proteinId) {
  closeModal();

  // Get configuration from localStorage
  const config = {
    protein: proteinId,
    interactor_rounds: parseInt(localStorage.getItem('interactor_rounds')) || 3,
    function_rounds: parseInt(localStorage.getItem('function_rounds')) || 3,
    max_depth: parseInt(localStorage.getItem('max_depth')) || 3,
    skip_validation: localStorage.getItem('skip_validation') === 'true',
    skip_deduplicator: localStorage.getItem('skip_deduplicator') === 'true',
    skip_arrow_determination: localStorage.getItem('skip_arrow_determination') === 'true'
  };

  miniProgress(`Querying ${proteinId}...`, null, null, proteinId);

  try {
    const response = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });

    if (!response.ok) {
      const errorData = await response.json();
      miniDone(`<span style="color: #ef4444;">Query failed: ${errorData.error || 'Unknown error'}</span>`);
      return;
    }

    const data = await response.json();

    if (data.status === 'processing') {
      // Poll for completion
      await pollUntilComplete(proteinId, ({ current, total, text }) => {
        miniProgress(text || 'Processing', current, total, proteinId);
      });

      // Reload page to show updated data
      miniDone(`<span>Query complete! Reloading...</span>`);
      setTimeout(() => { window.location.reload(); }, 1000);
    } else {
      miniDone(`<span style="color: #ef4444;">Unexpected status: ${data.status}</span>`);
    }
  } catch (error) {
    console.error('[ERROR] Query from modal failed:', error);
    miniDone(`<span style="color: #ef4444;">Failed to start query</span>`);
  }
}

// Search protein from visualizer page
async function searchProteinFromVisualizer(proteinName) {
  miniProgress(`Searching for ${proteinName}...`, null, null);

  try {
    const response = await fetch(`/api/search/${encodeURIComponent(proteinName)}`);

    if (!response.ok) {
      const errorData = await response.json();
      miniDone(`<span style="color: #ef4444;">${errorData.error || 'Search failed'}</span>`);
      return;
    }

    const data = await response.json();

    if (data.status === 'found') {
      // Protein exists - navigate to it
      miniDone(`<span>Found! Loading ${proteinName}...</span>`);
      setTimeout(() => {
        window.location.href = `/api/visualize/${encodeURIComponent(proteinName)}?t=${Date.now()}`;
      }, 500);
    } else {
      // Not found - show query prompt
      miniDone(`<span>${proteinName} not found. <button onclick="startQueryFromVisualizer('${proteinName}')" style="padding: 4px 12px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; margin-left: 8px;">Start Query</button></span>`);
    }
  } catch (error) {
    console.error('[ERROR] Search failed:', error);
    miniDone(`<span style="color: #ef4444;">Search failed</span>`);
  }
}

// Start query from visualizer page
async function startQueryFromVisualizer(proteinName) {
  const config = {
    protein: proteinName,
    interactor_rounds: parseInt(localStorage.getItem('interactor_rounds')) || 3,
    function_rounds: parseInt(localStorage.getItem('function_rounds')) || 3,
    max_depth: parseInt(localStorage.getItem('max_depth')) || 3,
    skip_validation: localStorage.getItem('skip_validation') === 'true',
    skip_deduplicator: localStorage.getItem('skip_deduplicator') === 'true',
    skip_arrow_determination: localStorage.getItem('skip_arrow_determination') === 'true'
  };

  miniProgress(`Querying ${proteinName}...`, null, null, proteinName);

  try {
    const response = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });

    if (!response.ok) {
      const errorData = await response.json();
      miniDone(`<span style="color: #ef4444;">Query failed: ${errorData.error || 'Unknown error'}</span>`);
      return;
    }

    const data = await response.json();

    if (data.status === 'processing') {
      await pollUntilComplete(proteinName, ({ current, total, text }) => {
        miniProgress(text || 'Processing', current, total, proteinName);
      });

      miniDone(`<span>Query complete! Loading visualization...</span>`);
      setTimeout(() => {
        window.location.href = `/api/visualize/${encodeURIComponent(proteinName)}?t=${Date.now()}`;
      }, 1000);
    } else {
      miniDone(`<span style="color: #ef4444;">Unexpected status: ${data.status}</span>`);
    }
  } catch (error) {
    console.error('[ERROR] Query failed:', error);
    miniDone(`<span style="color: #ef4444;">Failed to start query</span>`);
  }
}

function showFunctionModalFromNode(fnNode){
  // Find the corresponding link to get the normalized arrow
  const linkId = `${fnNode.parent}-${fnNode.id}`;
  const correspondingLink = links.find(l => l.id === linkId);

  // Leverage the same renderer as link, but pass the fields explicitly
  showFunctionModal({
    fn: fnNode.data,
    interactor: fnNode.interactorData,
    affected: fnNode.parent,
    label: fnNode.label,
    linkArrow: correspondingLink ? correspondingLink.arrow : undefined
  });
}

/* Function modal (from function link click) */
function showFunctionModalFromLink(link){
  const payload = link.data || {};
  showFunctionModal({
    fn: payload.fn || {},
    interactor: payload.interactor || {},
    affected: (payload.interactor && payload.interactor.primary) || '—',
    label: (payload.fn && payload.fn.function) || 'Function',
    linkArrow: link.arrow  // Pass the link's already-normalized arrow
  });
}

/* Render function modal (interactor → fn) */
function showFunctionModal({ fn, interactor, affected, label, linkArrow }){

  // Format references with full paper details from evidence using beautiful wrappers
  const evs = Array.isArray(fn.evidence) ? fn.evidence : [];
  const evHTML = evs.length ? `<div class="expanded-evidence-list">${evs.map(ev=>{
    const primaryLink = ev.pmid ? `https://pubmed.ncbi.nlm.nih.gov/${ev.pmid}` : (ev.doi ? `https://doi.org/${ev.doi}` : null);
    return `<div class="expanded-evidence-wrapper">
      <div class="expanded-evidence-card" data-evidence-link="${primaryLink || ''}" data-has-link="${primaryLink ? 'true' : 'false'}">
        <div class="expanded-evidence-title">${ev.paper_title || 'Title not available'}</div>
        <div class="expanded-evidence-meta">
          ${ev.authors ? `<div class="expanded-evidence-meta-item"><strong>Authors:</strong> ${ev.authors}</div>` : ''}
          ${ev.journal ? `<div class="expanded-evidence-meta-item"><strong>Journal:</strong> ${ev.journal}</div>` : ''}
          ${ev.year ? `<div class="expanded-evidence-meta-item"><strong>Year:</strong> ${ev.year}</div>` : ''}
        </div>
        ${ev.relevant_quote ? `<div class="expanded-evidence-quote">"${ev.relevant_quote}"</div>` : ''}
        <div class="expanded-evidence-pmids" style="margin-top:8px;">
          ${ev.pmid ? `<a href="https://pubmed.ncbi.nlm.nih.gov/${ev.pmid}" target="_blank" class="expanded-pmid-badge" onclick="event.stopPropagation();">PMID: ${ev.pmid}</a>` : ''}
          ${ev.doi ? `<a href="https://doi.org/${ev.doi}" target="_blank" class="expanded-pmid-badge" onclick="event.stopPropagation();">DOI: ${ev.doi}</a>` : ''}
        </div>
      </div>
    </div>`;
  }).join('')}</div>` : (Array.isArray(fn.pmids) && fn.pmids.length
      ? fn.pmids.map(p=> `<a class="pmid-link" target="_blank" href="https://pubmed.ncbi.nlm.nih.gov/${p}">PMID: ${p}</a>`).join(', ')
      : '<div class="expanded-empty">No references available</div>');

  // Format specific effects with 3D wrappers
  let effectsHTML = '';
  if (Array.isArray(fn.specific_effects) && fn.specific_effects.length) {
    const effectChips = fn.specific_effects.map(s=>`
      <div class="expanded-effect-chip-wrapper">
        <div class="expanded-effect-chip">${s}</div>
      </div>`).join('');
    effectsHTML = `
      <tr class="info-row">
        <td class="info-label">SPECIFIC EFFECTS</td>
        <td class="info-value">
          <div class="expanded-effects-grid">${effectChips}</div>
        </td>
      </tr>`;
  }

  // Format biological cascade - NORMALIZED VERTICAL FLOWCHART
  const createCascadeHTML = (value) => {
    const segments = Array.isArray(value) ? value : (value ? [value] : []);
    if (segments.length === 0) {
      return '<div class="expanded-empty">Cascading biological effects not specified</div>';
    }

    // Normalize: flatten all segments and split by arrow (→)
    const allSteps = [];
    segments.forEach(segment => {
      const text = (segment == null ? '' : segment).toString().trim();
      if (!text) return;

      // Split by arrow and clean each step
      const steps = text.split('→').map(s => s.trim()).filter(s => s.length > 0);
      allSteps.push(...steps);
    });

    if (allSteps.length === 0) {
      return '<div class="expanded-empty">Cascading biological effects not specified</div>';
    }

    // Create vertical flowchart blocks
    const items = allSteps.map(step =>
      `<div class="cascade-flow-item">${escapeHtml(step)}</div>`
    ).join('');

    return `<div class="cascade-wrapper"><div class="cascade-flow-container">${items}</div></div>`;
  };
  const biologicalConsequenceHTML = createCascadeHTML(fn.biological_consequence);

  const mechanism = interactor && interactor.intent ? (interactor.intent[0].toUpperCase()+interactor.intent.slice(1)) : 'Not specified';

  // EFFECT TYPE: Use the link's already-normalized arrow
  // The link was created with the normalized arrow, so we MUST use that for consistency
  const normalizedArrow = linkArrow || 'binds';  // Default to binds if no link arrow provided
  const arrowColor = normalizedArrow === 'activates' ? '#059669' : (normalizedArrow === 'inhibits' ? '#dc2626' : '#7c3aed');
  const arrowStr = fn.effect_description ?
    `<strong style="color:${arrowColor};">${fn.effect_description}</strong>` :
    (normalizedArrow === 'activates' ?
      '<strong style="color:#059669;">✓ Function is enhanced or activated</strong>' :
      (normalizedArrow === 'inhibits' ?
        '<strong style="color:#dc2626;">✗ Function is inhibited or disrupted</strong>' :
        '<strong style="color:#7c3aed;">⊕ Binds/Interacts</strong>'));

  // Check for validity field (from fact-checker)
  const validity = fn.validity || 'TRUE';
  const validationNote = fn.validation_note || '';
  const isConflicting = validity === 'CONFLICTING';
  const isFalse = validity === 'FALSE';

  // Build conflict warning HTML if needed
  let conflictWarningHTML = '';
  if (isConflicting || isFalse) {
    const warningType = isFalse ? 'Invalid Claim' : 'Conflicting Evidence';
    const warningIcon = isFalse ? '❌' : '⚠️';
    const warningColor = isFalse ? '#dc2626' : '#f59e0b';
    conflictWarningHTML = `
      <tr class="info-row">
        <td colspan="2">
          <div style="background:${isFalse ? '#fee2e2' : '#fff3cd'};border-left:4px solid ${warningColor};padding:12px 16px;margin:8px 0;border-radius:4px;">
            <div style="font-weight:600;color:${warningColor};margin-bottom:4px;">
              ${warningIcon} <strong>${warningType}</strong>
            </div>
            <div style="color:#374151;font-size:13px;">${validationNote}</div>
          </div>
        </td>
      </tr>`;
  }

  // Update function label to show asterisk for conflicting claims
  const functionLabel = isConflicting ? `⚠ ${label} *` : label;

  // Wrap mechanism with beautiful wrapper
  const mechanismHTML = mechanism !== 'Not specified'
    ? `<div class="expanded-mechanism-wrapper"><span class="mechanism-badge">${mechanism}</span></div>`
    : '<span class="muted-text">Not specified</span>';

  // Wrap cellular process with beautiful wrapper
  const cellularHTML = fn.cellular_process
    ? `<div class="expanded-cellular-wrapper"><div class="expanded-cellular-process"><div class="expanded-cellular-process-text">${fn.cellular_process}</div></div></div>`
    : '<div class="expanded-empty">Molecular mechanism not specified</div>';

  // Wrap effect type with beautiful wrapper
  const effectTypeColor = normalizedArrow === 'activates' ? 'activates' : (normalizedArrow === 'inhibits' ? 'inhibits' : 'binds');
  const effectTypeText = fn.effect_description || (normalizedArrow === 'activates' ? '✓ Function is enhanced or activated' : (normalizedArrow === 'inhibits' ? '✗ Function is inhibited or disrupted' : '⊕ Binds/Interacts'));
  const effectTypeHTML = `<div class="expanded-effect-type ${effectTypeColor}"><span class="effect-type-badge ${effectTypeColor}">${effectTypeText}</span></div>`;

  // Wrap function and protein names prominently
  const functionHTML = `<div class="function-name-wrapper ${effectTypeColor}"><span class="function-name ${effectTypeColor}" style="font-size: 18px;">${functionLabel}</span></div>`;
  const affectedHTML = `<div class="interaction-name-wrapper"><div class="interaction-name" style="font-size: 16px;">${affected}</div></div>`;

  const body = `
    <table class="info-table">
      ${conflictWarningHTML}
      <tr class="info-row"><td class="info-label">FUNCTION</td><td class="info-value">${functionHTML}</td></tr>
      <tr class="info-row"><td class="info-label">AFFECTED PROTEIN</td><td class="info-value">${affectedHTML}</td></tr>
      <tr class="info-row"><td class="info-label">EFFECT TYPE</td><td class="info-value">${effectTypeHTML}</td></tr>
      <tr class="info-row"><td class="info-label">MECHANISM</td><td class="info-value">${mechanismHTML}</td></tr>
      <tr class="info-row"><td class="info-label">CELLULAR PROCESS</td><td class="info-value">${cellularHTML}</td></tr>
      <tr class="info-row"><td class="info-label">BIOLOGICAL CASCADE</td><td class="info-value">${biologicalConsequenceHTML}</td></tr>
      ${effectsHTML}
      <tr class="info-row"><td class="info-label">REFERENCES</td><td class="info-value">${evHTML}</td></tr>
    </table>`;
  openModal(`Function: ${label}`, body);
}

/* ===== Progress helpers (viz page) ===== */
// Custom error for cancellations (to distinguish from other errors)
class CancellationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'CancellationError';
  }
}

let currentJobProtein = null;  // Track the current job for cancellation

function showHeader(){
  const header = document.querySelector('.header');
  if (header) header.classList.add('header-visible');
}
function hideHeader(){
  const header = document.querySelector('.header');
  if (header) header.classList.remove('header-visible');
}

function miniProgress(text, current, total, proteinName){
  const wrap = document.getElementById('mini-progress-wrapper');
  const bar  = document.getElementById('mini-progress-bar-inner');
  const txt  = document.getElementById('mini-progress-text');
  const msg  = document.getElementById('notification-message');
  const cancelBtn = document.getElementById('mini-cancel-btn');

  if (msg) msg.innerHTML = '';
  if (!wrap || !bar || !txt) return;

  // Show header when progress starts
  showHeader();
  wrap.style.display = 'grid';

  // Track current job
  if (proteinName) {
    currentJobProtein = proteinName;
    currentRunningJob = proteinName;  // Keep both variables in sync
    // Show cancel button for all jobs
    if (cancelBtn) {
      cancelBtn.style.display = 'inline-block';
      cancelBtn.disabled = false;  // Re-enable in case it was disabled
    }
  }

  if (typeof current==='number' && typeof total==='number' && total>0){
    const pct = Math.max(0, Math.min(100, Math.round((current/total)*100)));
    bar.style.width = pct+'%';
    // Simplified format for visualization page: just protein name and percentage
    if (proteinName) {
      txt.textContent = `${proteinName}: ${pct}%`;
    } else {
      txt.textContent = `${text||'Processing…'} (${pct}%)`;
    }
  } else {
    bar.style.width = '25%';
    // When no progress numbers available, show protein name with status
    if (proteinName) {
      txt.textContent = `${proteinName}: ${text || 'Processing…'}`;
    } else {
      txt.textContent = text || 'Processing…';
    }
  }
}

function miniDone(html){
  const wrap = document.getElementById('mini-progress-wrapper');
  const bar  = document.getElementById('mini-progress-bar-inner');
  const msg  = document.getElementById('notification-message');
  const cancelBtn = document.getElementById('mini-cancel-btn');

  if (wrap) wrap.style.display='none';
  if (bar) bar.style.width='0%';
  if (cancelBtn) cancelBtn.style.display='none';
  if (msg && html) msg.innerHTML = html;

  // Hide header after a delay
  setTimeout(hideHeader, 3000);
  currentJobProtein = null;
  currentRunningJob = null;  // Clear both variables
}

async function cancelCurrentJob(){
  if (!currentJobProtein) {
    console.warn('No current job to cancel');
    return;
  }

  const cancelBtn = document.getElementById('mini-cancel-btn');
  if (cancelBtn) cancelBtn.disabled = true;

  try {
    const response = await fetch(`/api/cancel/${encodeURIComponent(currentJobProtein)}`, {
      method: 'POST'
    });

    if (response.ok) {
      miniDone('<span style="color:#dc2626;">Job cancelled.</span>');
    } else {
      const data = await response.json();
      miniDone(`<span style="color:#dc2626;">Failed to cancel: ${data.error || 'Unknown error'}</span>`);
    }
  } catch (error) {
    console.error('Cancel request failed:', error);
    miniDone('<span style="color:#dc2626;">Failed to cancel job.</span>');
  } finally {
    if (cancelBtn) cancelBtn.disabled = false;
  }
}
async function pollUntilComplete(p, onUpdate){
  for(;;){
    await new Promise(r=>setTimeout(r, 4000));
    try{
      const r = await fetch(`/api/status/${encodeURIComponent(p)}`);
      if (!r.ok){ onUpdate && onUpdate({text:`Waiting on ${p}…`}); continue; }
      const s = await r.json();
      if (s.status==='complete'){ onUpdate && onUpdate({text:`Complete: ${p}`,current:1,total:1}); break; }
      if (s.status==='cancelled' || s.status==='cancelling'){
        miniDone('<span style="color:#dc2626;">Job cancelled.</span>');
        throw new CancellationError('Job was cancelled by user');
      }
      const prog = s.progress || s;
      onUpdate && onUpdate({current:prog.current, total:prog.total, text:prog.text || s.status || 'Processing'});
    }catch(e){
      if (e instanceof CancellationError || e.name === 'CancellationError') throw e;
      onUpdate && onUpdate({text:`Rechecking ${p}…`});
    }
  }
}

// === Pruned expansion (client prefers prune, falls back to full) ===
const PRUNE_KEEP = 20;  // (#2) client cap; backend will enforce its own hard cap

function getCurrentProteinNodes() {
  // Only main + interactors (omit function boxes) (#3)
  return nodes.filter(n => n.type === 'main' || n.type === 'interactor').map(n => n.id);
}

function findMainEdgePayload(targetId) {
  // Enrich pruning relevance when main ↔ target exists; otherwise omit (#3)
  const hit = links.find(l => l.type === 'interaction' && (
    ((l.source.id || l.source) === SNAP.main && (l.target.id || l.target) === targetId) ||
    ((l.source.id || l.source) === targetId && (l.target.id || l.target) === SNAP.main)
  ));
  if (!hit) return null;
  const L = hit.data || {};
  return {
    arrow: hit.arrow || L.arrow || '',
    intent: L.intent || hit.intent || '',
    direction: L.direction || hit.direction || '',
    support_summary: L.support_summary || ''
  };
}

async function pollPruned(jobId, onUpdate) {
  for (;;) {
    await new Promise(r => setTimeout(r, 3000));
    try {
      const r = await fetch(`/api/expand/status/${encodeURIComponent(jobId)}`);
      if (!r.ok) throw new Error(`status ${r.status}`);
      const s = await r.json();
      if (s.status === 'complete') { onUpdate && onUpdate({ text: s.text || 'complete' }); break; }
      if (s.status === 'error') throw new Error(s.text || 'prune error');
      onUpdate && onUpdate({ text: s.text || s.status || 'processing' });
    } catch {
      onUpdate && onUpdate({ text: 'checking…' });
    }
  }
}

async function queueAndWaitFull(protein) {
  // (#6) Only label text changes, bar stays the same
  miniProgress('Initializing…', null, null, protein);
  const q = await fetch('/api/query', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ protein })
  });
  if (!q.ok) throw new Error('failed to queue full job');

  try {
    await pollUntilComplete(protein, ({ current, total, text }) =>
      miniProgress(text || 'Processing', current, total, protein)
    );
  } catch (e) {
    // Re-throw with proper error type
    if (e instanceof CancellationError || e.name === 'CancellationError') {
      throw new CancellationError(e.message);
    }
    throw e;
  }
}

async function tryPrunedExpand(interNode) {
  const payload = {
    parent: SNAP.main,                    // (#1) always the current root as parent
    protein: interNode.id,
    current_nodes: getCurrentProteinNodes(),
    parent_edge: findMainEdgePayload(interNode.id) || undefined,
    max_keep: PRUNE_KEEP                  // (#2) client-side cap
  };

  const resp = await fetch('/api/expand/pruned', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!resp.ok) throw new Error(`pruned request failed: ${resp.status}`);
  const j = await resp.json();
  const jobId = j.job_id;

  if (j.status === 'needs_full') {
    await queueAndWaitFull(interNode.id);
    return await tryPrunedExpand(interNode); // re-enter prune after full is built
  }

  if (j.status === 'queued' || j.status === 'processing') {
    // (#6) progress label: show "Pruning (relevance…)" and switch to "LLM" if backend reports it
    miniProgress('Pruning (relevance)…', null, null, interNode.id);
    await pollPruned(jobId, p => {
      const t = (p.text || '').toLowerCase();
      const label = t.includes('llm') ? 'Pruning (LLM)' : 'Pruning (relevance)';
      miniProgress(`${label}…`, null, null, interNode.id);
    });
  } else if (j.status !== 'complete') {
    throw new Error(`unexpected pruned status: ${j.status || 'unknown'}`);
  }

  const rr = await fetch(`/api/expand/results/${encodeURIComponent(jobId)}`);
  if (!rr.ok) throw new Error(`failed to load pruned results`);
  const pruned = await rr.json();
  await mergeSubgraph(pruned, interNode);
  miniDone(`<span>Added pruned subgraph for <b>${interNode.id}</b> (≤${PRUNE_KEEP}).</span>`);
}

// Current full-flow used as fallback
async function expandViaFullFlow(interNode) {
  const id = interNode.id;
  let res = await fetch(`/api/results/${encodeURIComponent(id)}`);
  if (res.ok) {
    const raw = await res.json();
    await mergeSubgraph(raw, interNode);
    miniDone(`<span>Added subgraph for <b>${id}</b>.</span>`);
    return;
  }
  if (res.status === 404) {
    try {
      await queueAndWaitFull(id);
    } catch (e) {
      // Re-throw cancellation errors
      if (e instanceof CancellationError || e.name === 'CancellationError') {
        throw e;
      }
      throw e;
    }
    const r2 = await fetch(`/api/results/${encodeURIComponent(id)}`);
    if (!r2.ok) { miniDone(`<span>No results for ${id} after job.</span>`); return; }
    const raw2 = await r2.json();
    await mergeSubgraph(raw2, interNode);
    miniDone(`<span>Added subgraph for <b>${id}</b>.</span>`);
    return;
  }
  miniDone(`<span>Error loading ${id}: ${res.status}</span>`);
}

/* ===== Expand-on-click with depth limit ===== */
const MAX_DEPTH = 3;
const depthMap = new Map();
const expanded = new Set();
(function seedDepths(){
  const main = SNAP.main; depthMap.set(main,0);
  SNAP.interactors.forEach(it=> {
    // Assign depth based on interaction_type
    // direct interactions = depth 1, indirect = depth 2
    const depth = (it.interaction_type === 'indirect') ? 2 : 1;
    depthMap.set(it.primary, depth);
  });
})();

async function expandInteractor(interNode){
  const id = interNode.id;
  const depth = depthMap.get(id) ?? 1;
  const msg = document.getElementById('notification-message');

  // Toggle collapse
  if (expanded.has(id)){
    await collapseInteractor(id);
    if (msg) msg.innerHTML = `<span>Collapsed subgraph for <b>${id}</b>.</span>`;
    return;
  }
  if (depth >= MAX_DEPTH){
    if (msg) msg.innerHTML = `<span>Depth limit (${MAX_DEPTH}) reached for ${id}.</span>`;
    return;
  }

  try {
    // Prefer pruned; clean fallback to full flow
    await tryPrunedExpand(interNode).catch(async (e) => {
      // Don't fallback if user cancelled
      if (e instanceof CancellationError || e.name === 'CancellationError') {
        throw e;  // Re-throw cancellation errors
      }
      console.warn('Pruned expand failed, falling back:', e);
      await expandViaFullFlow(interNode);
    });
  } catch (err) {
    // Don't show error message for cancellations
    if (err instanceof CancellationError || err.name === 'CancellationError') {
      return;  // Silent exit on cancellation
    }
    miniDone(`<span>Error expanding ${id}: ${err?.message || err}</span>`);
  }
}

async function mergeSubgraph(raw, clickedNode){
  console.log(`\n🔄 ========== MERGE SUBGRAPH START ==========`);
  console.log(`  Clicked node:`, clickedNode.id);
  console.log(`  Raw data keys:`, Object.keys(raw || {}));

  // NEW: Extract from new data structure
  const sub = (raw && raw.snapshot_json) ? raw.snapshot_json : raw;
  console.log(`  Snapshot data keys:`, Object.keys(sub || {}));
  console.log(`  Has 'proteins' array:`, Array.isArray(sub?.proteins));
  console.log(`  Has 'interactions' array:`, Array.isArray(sub?.interactions));

  // NEW: Check for new data structure (proteins and interactions arrays)
  if (!sub || !Array.isArray(sub.proteins) || !Array.isArray(sub.interactions)) {
    console.error('❌ mergeSubgraph: Invalid data structure!');
    console.error('  Expected: { proteins: [...], interactions: [...] }');
    console.error('  Got:', sub);
    return;
  }

  console.log(`  ✓ Data format valid`);
  console.log(`  - Proteins (${sub.proteins.length}):`, sub.proteins);
  console.log(`  - Interactions (${sub.interactions.length}):`, sub.interactions.length, 'items');

  // Determine cluster position for the expansion
  // Calculate ONCE and store for later cluster creation
  let newClusterPos = null;
  let centerX, centerY;

  if (clusters.has(clickedNode.id)) {
    // Cluster already exists, use its position
    const cluster = clusters.get(clickedNode.id);
    centerX = cluster.centerPos.x;
    centerY = cluster.centerPos.y;
  } else {
    // New cluster - calculate position now, create cluster later
    // Pass interactor count for dynamic spacing
    const interactorCount = sub.proteins.length - 1; // Exclude the clicked protein itself
    newClusterPos = getNextClusterPosition(interactorCount);
    centerX = newClusterPos.x;
    centerY = newClusterPos.y;
  }

  const nodeIds = new Set(nodes.map(n=>n.id));
  const linkIds = new Set(links.map(l=>l.id));
  const parentDepth = depthMap.get(clickedNode.id) ?? 1;
  const childDepth = Math.min(MAX_DEPTH, parentDepth+1);

  const regNodes = new Set();
  const regLinks = new Set();

  // NEW: Add protein nodes (exclude clicked node if already exists)
  const newProteins = sub.proteins.filter(p => p !== clickedNode.id && !nodeIds.has(p));

  // Calculate cluster radius for positioning (use existing cluster if available, or calculate new one)
  let clusterRadius;
  if (clusters.has(clickedNode.id)) {
    clusterRadius = clusters.get(clickedNode.id).radius;
  } else {
    // Calculate radius for new cluster based on protein count
    clusterRadius = calculateClusterRadius(newProteins.length);
  }

  newProteins.forEach((protein, idx) => {
    // Position nodes in a small circle within the cluster
    const angle = (2*Math.PI*idx)/Math.max(1, newProteins.length) - Math.PI/2;
    const radius = clusterRadius * 0.6; // Position within cluster bounds (60% of calculated radius)
    const x = centerX + Math.cos(angle)*radius;
    const y = centerY + Math.sin(angle)*radius;

    // Create new protein node
    nodes.push({
      id: protein,
      label: protein,
      type: 'interactor',
      radius: interactorNodeRadius,
      x: x,
      y: y
    });

    nodeIds.add(protein);
    depthMap.set(protein, childDepth);

    // Track for expansion registry (for collapse)
    if (!baseNodes || !baseNodes.has(protein)){
      if (!regNodes.has(protein)){
        refCounts.set(protein, (refCounts.get(protein) || 0) + 1);
        regNodes.add(protein);
      }
    }
  });

  // NEW: Add interaction links (all types: direct, shared, cross_link)
  sub.interactions.forEach(interaction => {
    const source = interaction.source;
    const target = interaction.target;

    if (!source || !target) {
      console.warn('mergeSubgraph: Interaction missing source/target', interaction);
      return;
    }

    // Determine arrow type
    const arrow = arrowKind(
      interaction.arrow || 'binds',
      interaction.intent || 'binding',
      interaction.direction || 'main_to_primary'
    );

    // Create link ID with arrow type (to allow parallel links with different arrows)
    const linkId = `${source}-${target}-${arrow}`;
    const reverseLinkId = `${target}-${source}-${arrow}`;

    // Skip if link already exists in base graph
    const inBase = (baseLinks && (baseLinks.has(linkId) || baseLinks.has(reverseLinkId)));
    if (inBase) {
      return;
    }

    // Skip if link already added in this merge
    if (linkIds.has(linkId)) {
      return;
    }

    // Check if reverse exists
    const reverseExists = linkIds.has(reverseLinkId);

    // Determine if bidirectional
    const isBidirectional = isBiDir(interaction.direction) || reverseExists;

    // Create link
    const link = {
      id: linkId,
      source: source,
      target: target,
      type: 'interaction',
      interactionType: interaction.type || 'direct',
      arrow: arrow,
      intent: interaction.intent || 'binding',
      direction: interaction.direction || 'main_to_primary',
      data: interaction,
      isBidirectional: isBidirectional,
      linkOffset: reverseExists ? 1 : 0,
      showBidirectionalMarkers: isBidirectional,
      confidence: interaction.confidence || 0.5
    };

    links.push(link);
    linkIds.add(linkId);

    // Track for expansion registry (for collapse)
    if (!baseLinks || !baseLinks.has(linkId)){
      if (!regLinks.has(linkId)){
        refCounts.set(linkId, (refCounts.get(linkId) || 0) + 1);
        regLinks.add(linkId);
      }
    }
  });

  console.log(`\n🔧 EXPANSION: Creating/updating cluster for ${clickedNode.id}`);
  console.log(`  - Current clusters:`, Array.from(clusters.keys()));
  console.log(`  - clusters.has('${clickedNode.id}'):`, clusters.has(clickedNode.id));
  console.log(`  - newClusterPos:`, newClusterPos);

  // Create new cluster for the expanded protein if needed
  if (!clusters.has(clickedNode.id) && newClusterPos) {
    // Remove clicked node from its old cluster
    const oldClusterId = getNodeCluster(clickedNode.id);
    console.log(`  - Old cluster ID for ${clickedNode.id}:`, oldClusterId);
    if (oldClusterId) {
      const oldCluster = clusters.get(oldClusterId);
      if (oldCluster) {
        oldCluster.members.delete(clickedNode.id);
        console.log(`  ✓ Removed ${clickedNode.id} from cluster ${oldClusterId}`);
      }
    }

    // Create new cluster and move the clicked node to it
    createCluster(clickedNode.id, newClusterPos, newProteins.length);
    console.log(`  ✅ CREATED NEW CLUSTER for ${clickedNode.id} at (${newClusterPos.x}, ${newClusterPos.y})`);
    console.log(`  - Cluster now exists:`, clusters.has(clickedNode.id));
  } else if (clusters.has(clickedNode.id)) {
    console.log(`  ℹ️ Cluster already exists for ${clickedNode.id}, will add new members`);
  } else if (!newClusterPos) {
    console.error(`  ❌ ERROR: newClusterPos is null/undefined!`);
  }

  // ALWAYS add new proteins to the cluster (whether newly created or pre-existing)
  // CRITICAL FIX: This was inside the conditional above, causing drag issues on re-expansion
  const targetCluster = clusters.get(clickedNode.id);
  console.log(`\n🔧 ADDING MEMBERS to cluster ${clickedNode.id}`);
  console.log(`  - targetCluster found:`, !!targetCluster);
  console.log(`  - newProteins:`, newProteins);
  console.log(`  - newProteins.length:`, newProteins.length);

  if (targetCluster && newProteins.length > 0) {
    console.log(`  ✓ Adding ${newProteins.length} proteins to cluster`);
    // Add all new proteins to the expanded cluster
    newProteins.forEach(protein => {
      addNodeToCluster(clickedNode.id, protein);
      console.log(`    - Added ${protein} to cluster ${clickedNode.id}`);
    });

    // Mark intra-cluster links
    sub.interactions.forEach(interaction => {
      const source = interaction.source;
      const target = interaction.target;
      const arrow = arrowKind(interaction.arrow || 'binds', interaction.intent || 'binding', interaction.direction || 'main_to_primary');
      const linkId = `${source}-${target}-${arrow}`;

      // If both nodes are in the cluster, it's an intra-cluster link
      if (targetCluster.members.has(source) && targetCluster.members.has(target)) {
        targetCluster.localLinks.add(linkId);
      }
    });

    // CRITICAL FIX: Ensure all cluster member positions are valid and synced
    // This prevents drag issues where member positions might not be initialized yet
    let validPosCount = 0;
    let invalidPosCount = 0;
    const clusterCenterX = centerX; // Use the centerX/centerY calculated earlier
    const clusterCenterY = centerY;

    targetCluster.members.forEach(memberId => {
      const member = nodes.find(n => n.id === memberId);
      if (member) {
        if (Number.isFinite(member.x) && Number.isFinite(member.y) &&
            member.x !== 0 && member.y !== 0) {
          validPosCount++;
        } else {
          invalidPosCount++;
          // If position is invalid, set it to cluster center + small offset
          const offset = Math.random() * 50 - 25;
          member.x = clusterCenterX + offset;
          member.y = clusterCenterY + offset;
          console.warn(`Fixed invalid position for ${memberId}: set to (${member.x}, ${member.y})`);
        }
      }
    });

    console.log(`\n✅ CLUSTER UPDATE COMPLETE for ${clickedNode.id}:`);
    console.log(`  - Position: (${clusterCenterX}, ${clusterCenterY})`);
    console.log(`  - Members (${targetCluster.members.size}):`, Array.from(targetCluster.members));
    console.log(`  - New proteins added: ${newProteins.join(', ')}`);
    console.log(`  - Center node position: (${clickedNode.x}, ${clickedNode.y}), fixed: (${clickedNode.fx}, ${clickedNode.fy})`);
    console.log(`  - Member positions: ${validPosCount} valid, ${invalidPosCount} fixed`);
    console.log(`  - Cluster in map:`, clusters.has(clickedNode.id));
    console.log(`  - Total clusters:`, clusters.size);
    console.log(`  - All cluster keys:`, Array.from(clusters.keys()));
  } else if (!targetCluster) {
    console.error(`❌ CLUSTER ERROR: No cluster found for ${clickedNode.id} after creation attempt!`);
  } else if (newProteins.length === 0) {
    console.warn(`⚠️ WARNING: No new proteins to add to cluster ${clickedNode.id}`);
  }

  // Mark expansion as complete
  expanded.add(clickedNode.id);
  expansionRegistry.set(clickedNode.id, { nodes: regNodes, links: regLinks });

  // Reposition indirect interactors near their upstream interactors (hybrid layout)
  // Group newly added indirect nodes by upstream
  const newIndirectGroups = new Map();

  nodes.forEach(node => {
    if (regNodes.has(node.id) && node.type === 'interactor') {
      // Check if this newly added node is an indirect interactor
      const link = links.find(l => {
        const target = (l.target && l.target.id) ? l.target.id : l.target;
        return target === node.id;
      });

      if (link?.data?.interaction_type === 'indirect' && link?.data?.upstream_interactor) {
        const upstream = link.data.upstream_interactor;
        if (!newIndirectGroups.has(upstream)) {
          newIndirectGroups.set(upstream, []);
        }
        newIndirectGroups.get(upstream).push(node);

        // Copy upstream info to node for force simulation
        node.upstream_interactor = upstream;
        node.interaction_type = 'indirect';
      }
    }
  });

  // Position each group around its upstream node
  newIndirectGroups.forEach((indirectNodes, upstreamId) => {
    const upstreamNode = nodes.find(n => n.id === upstreamId);

    if (!upstreamNode) {
      console.warn(`mergeSubgraph: Upstream node ${upstreamId} not found`);
      return;
    }

    console.log(`mergeSubgraph: positioning ${indirectNodes.length} indirect nodes around ${upstreamId}`);

    // Position in small orbital ring around upstream
    const orbitalRadius = 200;
    indirectNodes.forEach((node, idx) => {
      const angle = (2 * Math.PI * idx) / Math.max(indirectNodes.length, 1);
      node.x = upstreamNode.x + Math.cos(angle) * orbitalRadius;
      node.y = upstreamNode.y + Math.sin(angle) * orbitalRadius;
      delete node.fx;
      delete node.fy;
    });
  });

  console.log(`\n📍 BEFORE updateGraphWithTransitions:`);
  console.log(`  - ${clickedNode.id} position:`, { x: clickedNode.x, y: clickedNode.y, fx: clickedNode.fx, fy: clickedNode.fy });

  // Update graph with smooth transitions
  updateGraphWithTransitions();

  console.log(`\n📍 AFTER updateGraphWithTransitions:`);
  console.log(`  - ${clickedNode.id} position:`, { x: clickedNode.x, y: clickedNode.y, fx: clickedNode.fx, fy: clickedNode.fy });
}

// --- collapse helper: remove one expansion safely ---
async function collapseInteractor(ownerId){
  const reg = expansionRegistry.get(ownerId);
  if (!reg){ expanded.delete(ownerId); return; }

  // Remove links first
  const toRemoveLinks = [];
  reg.links.forEach(lid => {
    if (baseLinks && baseLinks.has(lid)) return; // never remove base
    const c = (refCounts.get(lid) || 0) - 1;
    if (c <= 0){ refCounts.delete(lid); toRemoveLinks.push(lid); }
    else { refCounts.set(lid, c); }
  });
  if (toRemoveLinks.length){
    links = links.filter(l => !toRemoveLinks.includes(l.id));
  }

  // Remove nodes (only if no remaining incident links)
  const toRemoveNodes = [];
  reg.nodes.forEach(nid => {
    if (baseNodes && baseNodes.has(nid)) return;
    const c = (refCounts.get(nid) || 0) - 1;
    if (c <= 0){
      const stillUsed = links.some(l => ((l.source.id||l.source)===nid) || ((l.target.id||l.target)===nid));
      if (!stillUsed){ refCounts.delete(nid); toRemoveNodes.push(nid); }
      else { refCounts.set(nid, 0); }
    } else {
      refCounts.set(nid, c);
    }
  });
  if (toRemoveNodes.length){
    nodes = nodes.filter(n => !toRemoveNodes.includes(n.id));
  }

  // Remove cluster if it was created for this expansion
  if (clusters.has(ownerId)) {
    // Before deleting, move the owner node back to root cluster
    const ownerNode = nodes.find(n => n.id === ownerId);
    if (ownerNode) {
      // Release fixed position so it can move
      ownerNode.fx = null;
      ownerNode.fy = null;

      // Find the main cluster (root cluster)
      const mainNode = nodes.find(n => n.type === 'main');
      if (mainNode && clusters.has(mainNode.id)) {
        const rootCluster = clusters.get(mainNode.id);
        rootCluster.members.add(ownerId);

        // Position it near the root cluster center for smooth transition
        const rootPos = rootCluster.centerPos;
        const angle = Math.random() * Math.PI * 2;
        const radius = rootCluster.radius * 0.7; // Use cluster's calculated radius
        ownerNode.x = rootPos.x + Math.cos(angle) * radius;
        ownerNode.y = rootPos.y + Math.sin(angle) * radius;

        console.log(`Moved ${ownerId} back to root cluster ${mainNode.id}`);
      }
    }

    clusters.delete(ownerId);
    console.log(`Removed cluster for ${ownerId}`);
  }

  expansionRegistry.delete(ownerId);
  expanded.delete(ownerId);
  updateGraphWithTransitions();
}

/**
 * Updates graph with smooth D3 transitions (works with force simulation)
 */
function updateGraphWithTransitions(){
  // Initialize new nodes with orbital positions
  nodes.forEach(node => {
    if (!Number.isFinite(node.x) || !Number.isFinite(node.y)) {
      const pos = calculateOrbitalPosition(node);
      node.x = pos.x;
      node.y = pos.y;
    }
  });

  // Update links with transitions
  if (!linkGroup) {
    // First render - no transitions
    rebuild();
    return;
  }

  // LINK UPDATE PATTERN
  const linkData = linkGroup.data(links, d => d.id);

  // EXIT: Remove old links
  linkData.exit()
    .transition().duration(300)
    .style('opacity', 0)
    .remove();

  // UPDATE: Update existing links
  linkData
    .transition().duration(400)
    .attr('d', calculateLinkPath);

  // ENTER: Add new links
  const linkEnter = linkData.enter().append('path')
    .attr('class', d=>{
      const arrow = d.arrow||'binds';
      let classes = 'link';
      if (arrow==='binds') classes += ' link-binding';
      else if (arrow==='activates') classes += ' link-activate';
      else if (arrow==='inhibits') classes += ' link-inhibit';
      else classes += ' link-binding';
      if (d.interaction_type === 'indirect') {
        classes += ' link-indirect';
      }
      if (d.interactionType === 'shared' || d.interactionType === 'cross_link') {
        classes += ' link-shared';
      }
      if (d._incomplete_pathway) {
        classes += ' link-incomplete';
      }
      return classes;
    })
    .attr('marker-start', d=>{
      const dir = (d.direction || '').toLowerCase();
      // marker-start shows arrow at source end
      // Use for bidirectional (both ends) only
      if (dir === 'bidirectional') {
        const a=d.arrow||'binds';
        if (a==='activates') return 'url(#arrow-activate)';
        if (a==='inhibits') return 'url(#arrow-inhibit)';
        return 'url(#arrow-binding)';
      }
      return null;
    })
    .attr('marker-end', d=>{
      const dir = (d.direction || '').toLowerCase();
      // marker-end shows arrow at target end (default for all directed arrows)
      // Support both query-relative (main_to_primary) AND absolute (a_to_b) directions
      // Query-relative: main_to_primary, primary_to_main, bidirectional
      // Absolute: a_to_b, b_to_a (used for shared links and database storage)
      if (dir === 'main_to_primary' || dir === 'primary_to_main' || dir === 'bidirectional' ||
          dir === 'a_to_b' || dir === 'b_to_a') {
        const a=d.arrow||'binds';
        if (a==='activates') return 'url(#arrow-activate)';
        if (a==='inhibits') return 'url(#arrow-inhibit)';
        return 'url(#arrow-binding)';
      }
      return null;
    })
    .attr('fill','none')
    .attr('d', calculateLinkPath)
    .style('opacity', 0)
    .on('mouseover', function(){ d3.select(this).style('stroke-width','3.5'); svg.style('cursor','pointer'); })
    .on('mouseout',  function(){ d3.select(this).style('stroke-width',null);  svg.style('cursor',null); })
    .on('click', handleLinkClick);

  linkEnter.transition().duration(400).style('opacity', 1);

  // Merge enter + update
  linkGroup = linkEnter.merge(linkData);

  // NODE UPDATE PATTERN
  const nodeData = nodeGroup.data(nodes, d => d.id);

  // EXIT: Remove old nodes
  nodeData.exit()
    .transition().duration(300)
    .style('opacity', 0)
    .remove();

  // UPDATE: Move existing nodes and update expanded state
  nodeData.each(function(d) {
    if (d.type === 'interactor') {
      // Update class based on whether this node is now a cluster center
      const isExpanded = clusters.has(d.id);
      const nodeClass = isExpanded ? 'node expanded-node' : 'node interactor-node';
      d3.select(this).select('circle').attr('class', nodeClass);
    }
  });
  nodeData
    .transition().duration(500)
    .attr('transform', d => `translate(${d.x},${d.y})`);

  // ENTER: Add new nodes
  const nodeEnter = nodeData.enter().append('g')
    .attr('class','node-group')
    .attr('transform', d => {
      // Start from parent position for smooth animation
      const parent = nodes.find(n => {
        const registry = expansionRegistry.get(n.id);
        return registry && registry.nodes && registry.nodes.has(d.id);
      });
      if (parent && parent.x && parent.y) {
        return `translate(${parent.x},${parent.y})`;
      }
      return `translate(${d.x},${d.y})`;
    })
    .style('opacity', 0);

  nodeEnter.each(function(d){
    const group = d3.select(this);
    if (d.type==='main'){
      group.append('circle')
        .attr('class','node main-node')
        .attr('r', mainNodeRadius)
        .style('cursor','pointer')
        .on('click', (ev)=>{ ev.stopPropagation(); handleNodeClick(d); });
      group.append('text').attr('class','node-label main-label').attr('dy',5).text(d.label);
    } else if (d.type==='interactor'){
      // Check if this interactor has been expanded (is a cluster center)
      const isExpanded = clusters.has(d.id);
      const nodeClass = isExpanded ? 'node expanded-node' : 'node interactor-node';
      group.append('circle')
        .attr('class', nodeClass)
        .attr('r', interactorNodeRadius)
        .style('cursor','pointer')
        .on('click', (ev)=>{ ev.stopPropagation(); handleNodeClick(d); });
      group.append('text').attr('class','node-label main-label').attr('dy',5).text(d.label);
    }
  });

  // Animate new nodes to final position
  nodeEnter.transition().duration(500)
    .attr('transform', d => `translate(${d.x},${d.y})`)
    .style('opacity', 1);

  // Merge enter + update
  nodeGroup = nodeEnter.merge(nodeData);

  // Add drag handlers to new nodes
  nodeEnter.call(d3.drag()
    .on('start', dragstarted)
    .on('drag', dragged)
    .on('end', dragended));

  // Update simulation with new data
  if (simulation) {
    console.log(`\n⚙️ BEFORE simulation.nodes():`);
    // Log a few cluster centers
    clusters.forEach((cluster, centerId) => {
      const centerNode = nodes.find(n => n.id === centerId);
      if (centerNode) {
        console.log(`  - ${centerId}:`, { x: centerNode.x, y: centerNode.y, fx: centerNode.fx, fy: centerNode.fy });
      }
    });

    simulation.nodes(nodes);

    console.log(`\n⚙️ AFTER simulation.nodes():`);
    clusters.forEach((cluster, centerId) => {
      const centerNode = nodes.find(n => n.id === centerId);
      if (centerNode) {
        console.log(`  - ${centerId}:`, { x: centerNode.x, y: centerNode.y, fx: centerNode.fx, fy: centerNode.fy });
      }
    });

    // Filter to only intra-cluster links for force
    const intraClusterLinks = links.filter(link => {
      const type = classifyLink(link);
      return type === 'intra-cluster';
    });

    simulation.force('link').links(intraClusterLinks);
    console.log(`Simulation updated: ${intraClusterLinks.length}/${links.length} links with force`);

    // Reheat simulation to settle new nodes
    if (nodeEnter.size() > 0) {
      console.log(`\n⚙️ BEFORE reheatSimulation():`);
      clusters.forEach((cluster, centerId) => {
        const centerNode = nodes.find(n => n.id === centerId);
        if (centerNode) {
          console.log(`  - ${centerId}:`, { x: centerNode.x, y: centerNode.y, fx: centerNode.fx, fy: centerNode.fy });
        }
      });

      reheatSimulation(0.4);

      console.log(`\n⚙️ AFTER reheatSimulation():`);
      clusters.forEach((cluster, centerId) => {
        const centerNode = nodes.find(n => n.id === centerId);
        if (centerNode) {
          console.log(`  - ${centerId}:`, { x: centerNode.x, y: centerNode.y, fx: centerNode.fx, fy: centerNode.fy });
        }
      });
    }
  }

  // Update table view
  buildTableView();

  // After transitions complete, zoom to new nodes
  if (nodeEnter.size() > 0) {
    setTimeout(() => {
      focusOnNewNodes(nodeEnter.data());
    }, 600); // Wait for node animations to complete
  }
}

/**
 * Smoothly zooms camera to focus on newly added nodes
 * @param {array} newNodes - Array of newly added node data objects
 */
function focusOnNewNodes(newNodes) {
  if (!newNodes || newNodes.length === 0) return;

  // Calculate bounding box of new nodes
  const padding = 150;
  const xs = newNodes.map(n => n.x).filter(x => Number.isFinite(x));
  const ys = newNodes.map(n => n.y).filter(y => Number.isFinite(y));

  if (xs.length === 0 || ys.length === 0) return;

  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  // Calculate cluster dimensions
  const clusterWidth = Math.max(maxX - minX, 100); // Min 100px
  const clusterHeight = Math.max(maxY - minY, 100);
  const clusterCenterX = (minX + maxX) / 2;
  const clusterCenterY = (minY + maxY) / 2;

  // Calculate zoom scale to fit cluster with padding
  const viewWidth = width || 1000;
  const viewHeight = height || 800;
  const scaleX = (viewWidth - padding * 2) / clusterWidth;
  const scaleY = (viewHeight - padding * 2) / clusterHeight;
  const scale = Math.min(Math.max(scaleX, scaleY, 0.5), 2.0); // Clamp between 0.5x and 2x

  // Calculate translate to center the cluster
  const translateX = viewWidth / 2 - scale * clusterCenterX;
  const translateY = viewHeight / 2 - scale * clusterCenterY;

  // Apply smooth zoom transition
  const transform = d3.zoomIdentity
    .translate(translateX, translateY)
    .scale(scale);

  svg.transition()
    .duration(750)
    .ease(d3.easeCubicOut)
    .call(zoomBehavior.transform, transform);
}

/**
 * Full rebuild (used for initial render only)
 */
function rebuild(){
  // Clear existing visualization
  g.selectAll('*').remove();

  // Create force simulation with orbital constraints
  createSimulation();

  // Rebind interactor click handlers
  try{
    g.selectAll('.node-group').filter(d=>d.type==='interactor')
      .on('click', (ev,d)=>{ ev.stopPropagation(); handleNodeClick(d); });
  }catch(e){}

  // Update table view when graph changes
  buildTableView();
}

/* Zoom controls */
function scheduleFitToView(delay = 450, animate = true) {
  if (fitToViewTimer) {
    clearTimeout(fitToViewTimer);
  }
  fitToViewTimer = setTimeout(() => {
    fitGraphToView(120, animate);
  }, Math.max(0, delay));
}

function fitGraphToView(padding = 120, animate = true) {
  if (!svg || !zoomBehavior) return;
  const container = document.getElementById('network');
  if (!container) return;

  const viewWidth = container.clientWidth || width || 0;
  const viewHeight = container.clientHeight || height || 0;
  if (viewWidth < 10 || viewHeight < 10) return;

  width = viewWidth;
  height = viewHeight;
  svg.attr('width', width).attr('height', height);

  const positioned = nodes.filter(n => Number.isFinite(n.x) && Number.isFinite(n.y));
  if (!positioned.length) return;

  const [minX, maxX] = d3.extent(positioned, d => d.x);
  const [minY, maxY] = d3.extent(positioned, d => d.y);
  if (!Number.isFinite(minX) || !Number.isFinite(maxX) || !Number.isFinite(minY) || !Number.isFinite(maxY)) return;

  const graphWidth = Math.max(maxX - minX, 1);
  const graphHeight = Math.max(maxY - minY, 1);
  const safePadding = Math.min(padding, Math.min(viewWidth, viewHeight) / 3);

  const scaleX = (viewWidth - safePadding * 2) / graphWidth;
  const scaleY = (viewHeight - safePadding * 2) / graphHeight;
  const targetScale = Math.max(0.35, Math.min(2.4, Math.min(scaleX, scaleY)));

  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;

  const translateX = (viewWidth / 2) - targetScale * centerX;
  const translateY = (viewHeight / 2) - targetScale * centerY;
  const transform = d3.zoomIdentity.translate(translateX, translateY).scale(targetScale);

  if (animate) {
    svg.transition().duration(500).ease(d3.easeCubicOut).call(zoomBehavior.transform, transform);
  } else {
    svg.call(zoomBehavior.transform, transform);
  }

  graphInitialFitDone = true;
}

function reheatSimulation(alpha = 0.65) {
  if (!simulation) return;
  const targetAlpha = Math.max(alpha, simulation.alpha());
  simulation.alpha(targetAlpha).alphaTarget(0);
  simulation.restart();
}

function zoomIn(){
  if (!svg || !zoomBehavior) return;
  svg.transition().duration(250).ease(d3.easeCubicOut).call(zoomBehavior.scaleBy, 1.2);
}
function zoomOut(){
  if (!svg || !zoomBehavior) return;
  svg.transition().duration(250).ease(d3.easeCubicOut).call(zoomBehavior.scaleBy, 0.8);
}
function resetView(){
  if (!svg || !zoomBehavior) return;
  nodes.forEach(node => {
    if (node.type === 'main') {
      node.fx = width / 2;
      node.fy = height / 2;
    } else {
      node.fx = null;
      node.fy = null;
    }
  });
  reheatSimulation(0.7);
  scheduleFitToView(360, true);
}

function toggleTheme(){
  document.body.classList.toggle('dark-mode');
  const isDark = document.body.classList.contains('dark-mode');
  const icon = document.getElementById('theme-icon');
  if (icon) {
    icon.textContent = isDark ? '☀️' : '🌙';
  }
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

/* ===== Graph Filters ===== */
let graphActiveFilters = new Set(['activates', 'inhibits', 'binds']);
let graphActiveDepths = new Set([0, 1, 2, 3]); // All depths visible by default (0=main, 1=direct, 2=indirect, 3=tertiary)

function toggleGraphFilter(filterType) {
  if (graphActiveFilters.has(filterType)) {
    graphActiveFilters.delete(filterType);
  } else {
    graphActiveFilters.add(filterType);
  }

  // Update button visual state
  const btn = document.querySelector(`.graph-filter-btn.${filterType}`);
  if (btn) {
    btn.classList.toggle('active');
  }

  // Update graph visibility
  applyGraphFilters();
}

function toggleDepthFilter(depth) {
  // Never allow hiding depth 0 (main protein)
  if (depth === 0) return;

  if (graphActiveDepths.has(depth)) {
    graphActiveDepths.delete(depth);
  } else {
    graphActiveDepths.add(depth);
  }

  // Update button visual state
  const btn = document.querySelector(`.depth-filter[data-depth="${depth}"]`);
  if (btn) {
    btn.classList.toggle('active');
  }

  // Update graph visibility
  applyGraphFilters();
}

function refreshVisualization() {
  // Rebuild the graph from current data
  if (typeof buildInitialGraph === 'function') {
    buildInitialGraph();
  }
}

function applyGraphFilters() {
  if (!g) return;

  // Update link visibility and opacity
  g.selectAll('path.link').each(function(d) {
    const link = d3.select(this);
    const arrow = d.arrow || 'binds';

    if (d.type === 'interaction') {
      // Check both arrow type and depth filters
      const targetNode = nodes.find(n => n.id === (d.target?.id || d.target));
      const sourceNode = nodes.find(n => n.id === (d.source?.id || d.source));
      const maxDepth = Math.max(
        depthMap.get(targetNode?.id || '') || 0,
        depthMap.get(sourceNode?.id || '') || 0
      );

      const arrowMatch = graphActiveFilters.has(arrow);
      const depthMatch = graphActiveDepths.has(maxDepth);
      const shouldShow = arrowMatch && depthMatch;

      link.style('display', shouldShow ? null : 'none');
      link.style('opacity', shouldShow ? 0.7 : 0);
    }
  });

  // Update node visibility - hide interactors if all their interactions are filtered out OR depth filtered
  g.selectAll('g.node-group').each(function(d) {
    const nodeGroup = d3.select(this);

    // Main protein is always visible
    if (d.type === 'main') {
      nodeGroup.style('opacity', 1);
      nodeGroup.style('pointer-events', 'all');
      return;
    }

    if (d.type === 'interactor') {
      const nodeDepth = depthMap.get(d.id) || 0;
      const depthVisible = graphActiveDepths.has(nodeDepth);

      // Check if any links to this interactor are visible
      const hasVisibleLink = depthVisible && links.some(l => {
        if (l.type !== 'interaction') return false;
        const targetId = (l.target && l.target.id) ? l.target.id : l.target;
        const sourceId = (l.source && l.source.id) ? l.source.id : l.source;
        const isConnected = targetId === d.id || sourceId === d.id;
        const arrow = l.arrow || 'binds';

        // Check if the link itself passes depth filter
        const linkTargetNode = nodes.find(n => n.id === targetId);
        const linkSourceNode = nodes.find(n => n.id === sourceId);
        const linkMaxDepth = Math.max(
          depthMap.get(linkTargetNode?.id || '') || 0,
          depthMap.get(linkSourceNode?.id || '') || 0
        );

        return isConnected && graphActiveFilters.has(arrow) && graphActiveDepths.has(linkMaxDepth);
      });

      nodeGroup.style('opacity', hasVisibleLink ? 1 : 0.2);
      nodeGroup.style('pointer-events', hasVisibleLink ? 'all' : 'none');
    }
  });
}

/* ===== Table View ===== */
// Search and filter state
let searchQuery = '';
let activeFilters = new Set(['activates', 'inhibits', 'binds']);
let searchDebounceTimer = null;

function switchView(viewName) {
  const graphView = document.getElementById('network');
  const tableView = document.getElementById('table-view');
  const chatView = document.getElementById('chat-view');
  const tabs = document.querySelectorAll('.tab-btn');
  const header = document.querySelector('.header');
  const container = document.querySelector('.container');

  // Hide all views first
  graphView.style.display = 'none';
  tableView.style.display = 'none';
  chatView.style.display = 'none';

  // Remove active from all tabs
  tabs.forEach(tab => tab.classList.remove('active'));

  if (viewName === 'graph') {
    graphView.style.display = 'block';
    tabs[0].classList.add('active');
    // Remove static class to restore auto-hide behavior
    if (header) header.classList.remove('header-static');
    // Enable graph view scroll behavior
    document.body.classList.remove('table-view-active');
    document.body.classList.add('graph-view-active');
    if (container) container.classList.add('graph-active');
    scheduleFitToView(180, true);
  } else if (viewName === 'table') {
    tableView.style.display = 'flex';
    tabs[1].classList.add('active');
    buildTableView(); // Rebuild on switch to ensure current state
    // Make header static (always visible) for table view
    if (header) header.classList.add('header-static');
    // Enable page scroll for table view
    document.body.classList.remove('graph-view-active');
    document.body.classList.add('table-view-active');
    if (container) container.classList.remove('graph-active');
    // Reset search and filters when switching to table view
    searchQuery = '';
    activeFilters = new Set(['activates', 'inhibits', 'binds']);
    const searchInput = document.getElementById('table-search');
    if (searchInput) searchInput.value = '';
    document.querySelectorAll('.filter-chip').forEach(chip => chip.classList.add('filter-active'));
    applyFilters();
  } else if (viewName === 'chat') {
    chatView.style.display = 'block';
    tabs[2].classList.add('active');
    // Use auto-hide header for chat view (same as graph view)
    if (header) header.classList.remove('header-static');
    // Enable page scroll for chat view
    document.body.classList.remove('graph-view-active');
    document.body.classList.add('table-view-active');
    if (container) container.classList.remove('graph-active');
    // Focus chat input when switching to chat view
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
      setTimeout(() => chatInput.focus(), 100);
    }
  }
}

function handleSearchInput(event) {
  const query = event.target.value;
  const clearBtn = document.getElementById('search-clear-btn');

  // Show/hide clear button
  if (clearBtn) {
    clearBtn.style.display = query ? 'flex' : 'none';
  }

  // Debounce search
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    searchQuery = query.toLowerCase().trim();
    applyFilters();
  }, 300);
}

function clearSearch() {
  const searchInput = document.getElementById('table-search');
  if (searchInput) {
    searchInput.value = '';
    searchQuery = '';
    const clearBtn = document.getElementById('search-clear-btn');
    if (clearBtn) clearBtn.style.display = 'none';
    applyFilters();
  }
}

function toggleFilter(filterType) {
  if (activeFilters.has(filterType)) {
    activeFilters.delete(filterType);
  } else {
    activeFilters.add(filterType);
  }

  // Update visual state
  const chip = document.querySelector(`.filter-chip.${filterType}`);
  if (chip) {
    chip.classList.toggle('filter-active');
  }

  applyFilters();
}

function applyFilters() {
  const tbody = document.getElementById('table-body');
  if (!tbody) return;

  const functionRows = tbody.querySelectorAll('tr.function-row');
  let visibleCount = 0;

  functionRows.forEach(row => {
    const arrow = row.dataset.arrow || 'binds';
    const searchText = row.dataset.search || '';

    const typeMatch = activeFilters.has(arrow);
    const searchMatch = !searchQuery || searchText.includes(searchQuery);

    const shouldShow = typeMatch && searchMatch;
    row.style.display = shouldShow ? '' : 'none';

    if (shouldShow) visibleCount++;
  });

  updateFilterResults(visibleCount, functionRows.length);
}

function updateFilterResults(visible, total) {
  const resultsDiv = document.getElementById('filter-results');
  if (!resultsDiv) return;

  if (visible === undefined) {
    resultsDiv.textContent = '';
    return;
  }

  if (total === 0) {
    resultsDiv.textContent = '';
    resultsDiv.style.color = '#6b7280';
    return;
  }

  if (visible === 0) {
    resultsDiv.textContent = 'No interactions match current filters';
    resultsDiv.style.color = '#dc2626';
  } else if (visible === total) {
    resultsDiv.textContent = '';
  } else {
    resultsDiv.textContent = `Showing ${visible} of ${total} interactions`;
    resultsDiv.style.color = '#6b7280';
  }
}

/* ===== Table Sorting ===== */
let currentSortColumn = null;
let currentSortDirection = null;

function sortTable(column) {
  const tbody = document.getElementById('table-body');
  if (!tbody) return;

  const rows = Array.from(tbody.querySelectorAll('tr.function-row'));

  // Toggle sort direction
  if (currentSortColumn === column) {
    if (currentSortDirection === 'asc') {
      currentSortDirection = 'desc';
    } else if (currentSortDirection === 'desc') {
      // Third click: reset to unsorted
      currentSortColumn = null;
      currentSortDirection = null;
    } else {
      currentSortDirection = 'asc';
    }
  } else {
    currentSortColumn = column;
    currentSortDirection = 'asc';
  }

  // Update header indicators
  document.querySelectorAll('.data-table th.sortable').forEach(th => {
    th.classList.remove('sort-asc', 'sort-desc');
  });

  if (currentSortColumn && currentSortDirection) {
    const header = document.querySelector(`.data-table th[data-sort="${column}"]`);
    if (header) {
      header.classList.add(`sort-${currentSortDirection}`);
    }

    // Sort rows
    rows.sort((a, b) => {
      let aVal, bVal;

      switch (column) {
        case 'interaction':
          aVal = (a.querySelector('.interaction-name')?.textContent || '').trim();
          bVal = (b.querySelector('.interaction-name')?.textContent || '').trim();
          break;
        case 'function':
          aVal = (a.querySelector('.col-function .function-name')?.textContent || '').trim();
          bVal = (b.querySelector('.col-function .function-name')?.textContent || '').trim();
          break;
        case 'effect':
          aVal = (a.querySelector('.col-effect .effect-badge')?.textContent || '').trim();
          bVal = (b.querySelector('.col-effect .effect-badge')?.textContent || '').trim();
          break;
        case 'effectType':
          aVal = (a.querySelector('.col-effect-type')?.textContent || '').trim();
          bVal = (b.querySelector('.col-effect-type')?.textContent || '').trim();
          break;
        case 'mechanism':
          aVal = (a.querySelector('.col-mechanism')?.textContent || '').trim();
          bVal = (b.querySelector('.col-mechanism')?.textContent || '').trim();
          break;
        default:
          return 0;
      }

      const comparison = aVal.localeCompare(bVal, undefined, { numeric: true, sensitivity: 'base' });
      return currentSortDirection === 'asc' ? comparison : -comparison;
    });
  }

  // Re-append rows in sorted order
  rows.forEach(row => {
    // Also move the corresponding expanded row if it exists
    const expandedRow = row.nextElementSibling;
    tbody.appendChild(row);
    if (expandedRow && expandedRow.classList.contains('expanded-row')) {
      tbody.appendChild(expandedRow);
    }
  });
}

/* ===== Column Resizing ===== */
let resizingColumn = null;
let startX = 0;
let startWidth = 0;

function initColumnResizing() {
  const table = document.getElementById('interactions-table');
  if (!table) return;

  const resizeHandles = table.querySelectorAll('.resize-handle');
  resizeHandles.forEach(handle => {
    handle.addEventListener('mousedown', startResize);
  });

  document.addEventListener('mousemove', doResize);
  document.addEventListener('mouseup', stopResize);
}

function startResize(e) {
  e.preventDefault();
  e.stopPropagation();

  resizingColumn = e.target.closest('th');
  if (!resizingColumn) return;

  startX = e.pageX;
  startWidth = resizingColumn.offsetWidth;

  document.body.style.cursor = 'col-resize';
  document.body.style.userSelect = 'none';
}

function doResize(e) {
  if (!resizingColumn) return;

  const diff = e.pageX - startX;
  const newWidth = Math.max(40, startWidth + diff);

  resizingColumn.style.width = newWidth + 'px';
  resizingColumn.style.minWidth = newWidth + 'px';
}

function stopResize() {
  if (resizingColumn) {
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    resizingColumn = null;
  }
}

/* ===== Row Expansion ===== */
function toggleRowExpansion(clickedRow) {
  const isExpanded = clickedRow.dataset.expanded === 'true';

  // Find any existing expanded row
  const nextRow = clickedRow.nextElementSibling;
  const isExpandedRow = nextRow && nextRow.classList.contains('expanded-row');

  if (isExpanded) {
    // Collapse
    clickedRow.dataset.expanded = 'false';
    if (isExpandedRow) {
      nextRow.classList.remove('show');
      setTimeout(() => nextRow.remove(), 300);
    }
  } else {
    // Expand
    clickedRow.dataset.expanded = 'true';

    // Get entry data from row
    const entry = getEntryDataFromRow(clickedRow);
    if (!entry) return;

    // Create expanded row
    const expandedRow = createExpandedRow(entry);
    clickedRow.insertAdjacentElement('afterend', expandedRow);

    // Trigger animation
    setTimeout(() => expandedRow.classList.add('show'), 10);
  }
}

function getEntryDataFromRow(row) {
  const cells = row.querySelectorAll('td');
  if (cells.length < 6) return null; // Changed from 7 to 6 (we now have 6 columns)

  // We need to reconstruct the entry data from the row
  // We'll find it from the original entries using the stored data attributes
  const entries = collectFunctionEntries();
  const arrow = row.dataset.arrow;
  const searchKey = row.dataset.search;

  // Find matching entry
  const entry = entries.find(e => e.arrow === arrow && e.searchKey === searchKey);
  return entry;
}

function createExpandedRow(entry) {
  const expandedRow = document.createElement('tr');
  expandedRow.className = 'expanded-row';

  const td = document.createElement('td');
  td.colSpan = 6; // Match number of columns (reduced from 7 to 6)

  const content = document.createElement('div');
  content.className = 'expanded-content';

  // Build the expanded content - CLEAN TWO-COLUMN LAYOUT
  let html = '';

  // SECTION 1: INTERACTION DETAILS
  html += '<div class="detail-section">';
  html += '<h3 class="detail-section-header">INTERACTION DETAILS</h3>';
  html += '<div class="detail-divider"></div>';
  html += '<dl class="detail-grid">';

  // Interaction
  html += '<dt class="detail-label">Interaction:</dt>';
  html += `<dd class="detail-value">
    <span class="detail-interaction">
      ${escapeHtml(entry.source || 'Unknown')}
      <span class="detail-arrow">→</span>
      ${escapeHtml(entry.target || 'Unknown')}
    </span>
  </dd>`;

  // Function
  html += '<dt class="detail-label">Function:</dt>';
  html += `<dd class="detail-value">${escapeHtml(entry.functionLabel || 'Not specified')}</dd>`;

  // Interaction Effect (on the downstream protein)
  const interactionArrowClass = entry.interactionArrow || entry.arrow || 'binds';
  html += '<dt class="detail-label">Interaction Effect:</dt>';
  html += `<dd class="detail-value">
    <span class="detail-effect detail-effect-${interactionArrowClass}">${escapeHtml(entry.interactionEffectBadgeText || entry.effectBadgeText || 'Not specified')}</span>
    <span style="margin-left: 8px; font-size: 0.875em; color: var(--color-text-secondary);">(on ${escapeHtml(entry.interactorLabel)})</span>
  </dd>`;

  // Function Effect (on this specific function)
  const functionArrowClass = entry.functionArrow || entry.arrow || 'binds';
  html += '<dt class="detail-label">Function Effect:</dt>';
  html += `<dd class="detail-value">
    <span class="function-effect function-effect-${functionArrowClass}">${escapeHtml(entry.functionEffectBadgeText || entry.effectBadgeText || 'Not specified')}</span>
    <span style="margin-left: 8px; font-size: 0.875em; color: var(--color-text-secondary);">(on ${escapeHtml(entry.functionLabel)})</span>
  </dd>`;

  // Effect Type
  html += '<dt class="detail-label">Effect Type:</dt>';
  if (entry.effectTypeDetails && entry.effectTypeDetails.text) {
    html += `<dd class="detail-value">${escapeHtml(entry.effectTypeDetails.text)}</dd>`;
  } else {
    html += '<dd class="detail-value detail-empty">Not specified</dd>';
  }

  // Mechanism
  html += '<dt class="detail-label">Mechanism:</dt>';
  if (entry.mechanismText) {
    html += `<dd class="detail-value">${escapeHtml(entry.mechanismText)}</dd>`;
  } else {
    html += '<dd class="detail-value detail-empty">Not specified</dd>';
  }

  html += '</dl>';
  html += '</div>'; // end section

  // SECTION 2: CELLULAR CONTEXT
  html += '<div class="detail-section">';
  html += '<h3 class="detail-section-header">CELLULAR CONTEXT</h3>';
  html += '<div class="detail-divider"></div>';
  html += '<dl class="detail-grid">';

  // Cellular Process
  html += '<dt class="detail-label">Process:</dt>';
  if (entry.cellularProcess) {
    html += `<dd class="detail-value">${escapeHtml(entry.cellularProcess)}</dd>`;
  } else {
    html += '<dd class="detail-value detail-empty">Not specified</dd>';
  }

  // Specific Effects
  html += '<dt class="detail-label">Specific Effects:</dt>';
  if (entry.specificEffects && entry.specificEffects.length > 0) {
    html += '<dd class="detail-value"><ul class="detail-list">';
    entry.specificEffects.forEach(effect => {
      html += `<li>${escapeHtml(effect)}</li>`;
    });
    html += '</ul></dd>';
  } else {
    html += '<dd class="detail-value detail-empty">Not specified</dd>';
  }

  // Biological Cascade
  html += '<dt class="detail-label">Biological Cascade:</dt>';
  if (entry.biologicalCascade && entry.biologicalCascade.length > 0) {
    // Normalize: flatten all segments and split by arrow (→)
    const allSteps = [];
    entry.biologicalCascade.forEach(segment => {
      const text = (segment == null ? '' : segment).toString().trim();
      if (!text) return;
      const steps = text.split('→').map(s => s.trim()).filter(s => s.length > 0);
      allSteps.push(...steps);
    });

    if (allSteps.length > 0) {
      html += '<dd class="detail-value"><ol class="detail-list detail-list-ordered">';
      allSteps.forEach(step => {
        html += `<li>${escapeHtml(step)}</li>`;
      });
      html += '</ol></dd>';
    } else {
      html += '<dd class="detail-value detail-empty">Not specified</dd>';
    }
  } else {
    html += '<dd class="detail-value detail-empty">Not specified</dd>';
  }

  html += '</dl>';
  html += '</div>'; // end section

  // SECTION 3: EVIDENCE
  html += '<div class="detail-section">';
  html += '<h3 class="detail-section-header">EVIDENCE & PUBLICATIONS</h3>';
  html += '<div class="detail-divider"></div>';
  if (entry.evidence && entry.evidence.length > 0) {
    html += '<div class="expanded-evidence-list">';
    entry.evidence.forEach((ev, evIndex) => {
      // Determine primary link (PMID preferred, then DOI)
      const primaryLink = ev.pmid
        ? `https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(ev.pmid)}`
        : (ev.doi ? `https://doi.org/${escapeHtml(ev.doi)}` : null);

      // Simplified: Remove wrapper, keep card only
      html += `<div class="expanded-evidence-card" data-evidence-link="${primaryLink || ''}" data-has-link="${primaryLink ? 'true' : 'false'}">`;

      // Title
      const title = ev.paper_title || 'Untitled Publication';
      html += `<div class="expanded-evidence-title">${escapeHtml(title)}</div>`;

      // Meta information
      html += '<div class="expanded-evidence-meta">';
      if (ev.authors) {
        html += `<div class="expanded-evidence-meta-item"><strong>Authors:</strong> ${escapeHtml(ev.authors)}</div>`;
      }
      if (ev.journal) {
        html += `<div class="expanded-evidence-meta-item"><strong>Journal:</strong> ${escapeHtml(ev.journal)}</div>`;
      }
      if (ev.year) {
        html += `<div class="expanded-evidence-meta-item"><strong>Year:</strong> ${escapeHtml(ev.year)}</div>`;
      }
      if (ev.assay) {
        html += `<div class="expanded-evidence-meta-item"><strong>Assay:</strong> ${escapeHtml(ev.assay)}</div>`;
      }
      if (ev.species) {
        html += `<div class="expanded-evidence-meta-item"><strong>Species:</strong> ${escapeHtml(ev.species)}</div>`;
      }
      html += '</div>';

      // Quote
      if (ev.relevant_quote) {
        html += `<div class="expanded-evidence-quote">${escapeHtml(ev.relevant_quote)}</div>`;
      }

      // PMIDs and DOI
      html += '<div class="expanded-evidence-pmids">';
      if (ev.pmid) {
        html += `<a href="https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(ev.pmid)}" target="_blank" class="expanded-pmid-badge" onclick="event.stopPropagation();">PMID: ${escapeHtml(ev.pmid)}</a>`;
      }
      if (ev.doi) {
        html += `<a href="https://doi.org/${escapeHtml(ev.doi)}" target="_blank" class="expanded-pmid-badge" onclick="event.stopPropagation();">DOI: ${escapeHtml(ev.doi)}</a>`;
      }
      html += '</div>';

      html += '</div>'; // end evidence-card
    });
    html += '</div>';
  } else if (entry.fnData && entry.fnData.pmids && entry.fnData.pmids.length > 0) {
    // Show PMIDs even if no full evidence
    html += '<div class="expanded-evidence-pmids">';
    entry.fnData.pmids.forEach(pmid => {
      html += `<a href="https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(pmid)}" target="_blank" class="expanded-pmid-badge">PMID: ${escapeHtml(pmid)}</a>`;
    });
    html += '</div>';
  } else {
    html += '<p class="detail-empty" style="margin-top: 0;">No evidence provided</p>';
  }
  html += '</div>'; // end section

  content.innerHTML = html;
  td.appendChild(content);
  expandedRow.appendChild(td);

  // Add click handlers to evidence cards after DOM insertion
  setTimeout(() => {
    const evidenceCards = content.querySelectorAll('.expanded-evidence-card[data-has-link="true"]');
    evidenceCards.forEach(card => {
      card.addEventListener('click', (e) => {
        // Don't trigger if clicking on the badge links (they have stopPropagation)
        const link = card.dataset.evidenceLink;
        if (link) {
          window.open(link, '_blank');
        }
      });
    });
  }, 50);

  return expandedRow;
}

function buildTableView() {
  const tbody = document.getElementById('table-body');
  if (!tbody) return;

  tbody.innerHTML = '';

  const entries = collectFunctionEntries();

  entries.forEach(entry => {
    const row = document.createElement('tr');
    row.className = 'function-row';
    row.dataset.arrow = entry.arrow;
    row.dataset.search = entry.searchKey;
    row.dataset.expanded = 'false';

    const displaySource = entry.source || '—';
    const displayTarget = entry.target || '—';

    // Determine direction arrow symbol and color class
    // Support both query-relative AND absolute directions
    const direction = entry.direction || 'main_to_primary';
    let arrowSymbol = '↔';
    if (direction === 'main_to_primary' || direction === 'a_to_b' || direction.includes('to_primary')) arrowSymbol = '→';
    else if (direction === 'primary_to_main' || direction === 'b_to_a' || direction.includes('to_main')) arrowSymbol = '←';

    const arrowColorClass = `interaction-arrow-${entry.arrow}`;

    // Clean mechanism text (no wrapper)
    const mechanismHtml = entry.mechanismText
      ? `<span class="mechanism-text">${escapeHtml(entry.mechanismText.toUpperCase())}</span>`
      : '<span class="muted-text">Not specified</span>';

    // Clean effect type text (no wrapper)
    const effectTypeHtml = entry.effectTypeDetails && entry.effectTypeDetails.text
      ? `<span class="effect-type-text">${escapeHtml(entry.effectTypeDetails.text)}</span>`
      : '<span class="muted-text">Not specified</span>';

    row.innerHTML = `
      <td class="col-expand"><span class="expand-icon">▼</span></td>
      <td class="col-interaction">
        <div class="interaction-cell">
          <span class="interaction-text">
            ${escapeHtml(displaySource)}
            <span class="interaction-arrow ${arrowColorClass}">${arrowSymbol}</span>
            ${escapeHtml(displayTarget)}
          </span>
          <div class="interaction-subtitle">${escapeHtml(entry.interactorLabel)}</div>
        </div>
      </td>
      <td class="col-effect">
        <div style="display: flex; flex-direction: column; gap: 4px;">
          <span class="effect-text effect-text-${entry.interactionArrow}" style="font-size: 10px;" title="Interaction effect (on protein)">${escapeHtml(entry.interactionEffectBadgeText)}</span>
          <span class="function-effect-text function-effect-text-${entry.functionArrow}" style="font-size: 10px;" title="Function effect">${escapeHtml(entry.functionEffectBadgeText)}</span>
        </div>
      </td>
      <td class="col-function">
        <span class="function-text">${escapeHtml(entry.functionLabel)}</span>
      </td>
      <td class="col-effect-type">${effectTypeHtml}</td>
      <td class="col-mechanism">${mechanismHtml}</td>
    `;

    // Add click handler for row expansion
    row.addEventListener('click', (e) => {
      // Don't toggle if clicking on a link
      if (e.target.tagName === 'A' || e.target.closest('a')) {
        return;
      }
      // Toggle expansion for any other click on the row
      toggleRowExpansion(row);
    });

    tbody.appendChild(row);
  });

  applyFilters();
}

function collectFunctionEntries() {
  const entries = [];
  const interactions = SNAP.interactions || [];

  if (!SNAP.main) {
    console.warn('collectFunctionEntries: No main protein');
    return entries;
  }

  // NEW: Loop through interactions, then their functions
  interactions.forEach(interaction => {
    // Skip interactions without functions (e.g., shared links without context-specific functions)
    const functions = interaction.functions || [];
    if (functions.length === 0) {
      return;
    }

    // Extract interaction metadata
    const source = interaction.source || '';
    const target = interaction.target || '';
    const interactionArrow = interaction.arrow || 'binds';
    const intent = interaction.intent || 'binding';
    const supportSummary = interaction.support_summary || '';
    const direction = interaction.direction || 'main_to_primary';

    // Determine which protein is the "interactor" for display purposes
    // If interaction involves main protein, the other one is the interactor
    let interactorLabel = '';
    if (source === SNAP.main) {
      interactorLabel = target;
    } else if (target === SNAP.main) {
      interactorLabel = source;
    } else {
      // Shared link between two interactors - use source as display
      interactorLabel = source;
    }

    // Process each function
    functions.forEach((fn, fnIndex) => {
      if (!fn || typeof fn !== 'object') {
        console.warn('collectFunctionEntries: Invalid function data', fn);
        return;
      }

      const functionLabel = fn.function || 'Function';

      // IMPORTANT: Separate interaction effect from function effect
      // 1. Interaction Effect: Effect on the downstream PROTEIN (e.g., "ATXN3 inhibits VCP")
      // 2. Function Effect: Effect on this specific FUNCTION (e.g., "This interaction activates Autophagy")

      // Normalize interaction arrow (effect on the protein)
      const normalizedInteractionArrow = arrowKind(interactionArrow, intent, direction);

      // Normalize function arrow (effect on this specific function)
      const fnArrow = fn.arrow || interactionArrow;  // Fallback to interaction if function has no arrow
      const normalizedFunctionArrow = arrowKind(fnArrow, fn.intent || intent, direction);

      // Extract function details
      const cellularProcess = fn.cellular_process || '';
      const specificEffects = Array.isArray(fn.specific_effects) ? fn.specific_effects : [];
      const biologicalCascade = Array.isArray(fn.biological_consequence) ? fn.biological_consequence : [];
      const evidence = Array.isArray(fn.evidence) ? fn.evidence : [];
      const pmids = Array.isArray(fn.pmids) ? fn.pmids : [];

      // Get effect type details (use function arrow for function-specific details)
      const effectTypeDetails = getEffectTypeDetails(fn, normalizedFunctionArrow);

      // Get mechanism text
      const mechanismText = getMechanismText(intent);

      // Build searchable text
      const evidenceText = evidence.map(ev => [
        ev.paper_title,
        ev.authors,
        ev.journal,
        ev.year,
        ev.relevant_quote,
        ev.pmid
      ].filter(Boolean).join(' ')).join(' ');

      const searchParts = [
        source,
        target,
        interactorLabel,
        functionLabel,
        cellularProcess,
        specificEffects.join(' '),
        effectTypeDetails.text,
        mechanismText || '',
        supportSummary,
        biologicalCascade.join(' '),
        evidenceText,
        pmids.join(' ')
      ];

      // Create entry with BOTH interaction and function effects
      entries.push({
        interactorId: interactorLabel,
        interactorLabel: interactorLabel,
        source: String(source),
        target: String(target),
        direction: direction,

        // Interaction effect (on the downstream protein)
        interactionArrow: normalizedInteractionArrow,
        interactionEffectBadgeText: formatArrow(normalizedInteractionArrow),

        // Function effect (on this specific function)
        functionArrow: normalizedFunctionArrow,
        functionEffectBadgeText: formatArrow(normalizedFunctionArrow),

        // Legacy field for backward compatibility (use interactionArrow for most displays)
        arrow: normalizedInteractionArrow,
        effectBadgeText: formatArrow(normalizedInteractionArrow),

        functionLabel: functionLabel,
        cellularProcess: cellularProcess,
        specificEffects: specificEffects,
        effectTypeDetails: effectTypeDetails,
        mechanismText: mechanismText,
        biologicalCascade: biologicalCascade,
        evidence: evidence,
        fnData: fn,
        supportSummary: supportSummary,
        searchKey: searchParts.filter(Boolean).join(' ').toLowerCase()
      });
    });
  });

  return entries;
}

function renderSpecificEffects(effects) {
  if (!Array.isArray(effects) || effects.length === 0) {
    return '<span class="muted-text">Not specified</span>';
  }

  return `<div class="specific-effects-list">
    ${effects.map(effect => `<div class="specific-effect-chip">${escapeHtml(effect)}</div>`).join('')}
  </div>`;
}

function renderBiologicalCascade(steps) {
  if (!Array.isArray(steps) || steps.length === 0) {
    return '<span class="muted-text">Not specified</span>';
  }

  // Normalize: flatten all segments and split by arrows
  const allSteps = [];
  steps.forEach(segment => {
    const text = (segment == null ? '' : segment).toString().trim();
    if (!text) return;

    // Split by both arrow types (→ and \u001a) and clean each step
    const normalized = text.replace(/\u001a/g, '→');
    const stepsList = normalized.split('→').map(s => s.trim()).filter(s => s.length > 0);
    allSteps.push(...stepsList);
  });

  if (allSteps.length === 0) {
    return '<span class="muted-text">Not specified</span>';
  }

  return `<div class="biological-cascade-list">
    ${allSteps.map(step => `<div class="biological-cascade-item">${escapeHtml(step)}</div>`).join('')}
  </div>`;
}

function renderEvidenceSummary(evidence, fnData) {
  const items = Array.isArray(evidence) ? evidence.filter(Boolean) : [];
  const fnPmids = Array.isArray(fnData && fnData.pmids) ? fnData.pmids.filter(Boolean) : [];

  if (!items.length && !fnPmids.length) {
    return '<span class="muted-text">No evidence provided</span>';
  }

  if (!items.length) {
    return `<div class="table-evidence-pmids">
      ${fnPmids.map(p => `<a href="https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(p)}" target="_blank" class="pmid-link">PMID: ${escapeHtml(p)}</a>`).join('')}
    </div>`;
  }

  const limited = items.slice(0, 3);
  const displayedPmids = new Set();
  const listHtml = limited.map(ev => {
    const title = escapeHtml(ev.paper_title || 'Untitled');
    const authors = ev.authors ? escapeHtml(ev.authors) : '';
    const journal = ev.journal ? escapeHtml(ev.journal) : '';
    const year = ev.year ? escapeHtml(ev.year) : '';
    const metaParts = [];
    if (authors) metaParts.push(authors);
    if (journal) metaParts.push(journal);
    if (year) metaParts.push(`(${year})`);
    const metaHtml = metaParts.length ? `<div class="table-evidence-meta">${metaParts.join(' · ')}</div>` : '';
    let pmidHtml = '';
    if (ev.pmid) {
      const safePmid = escapeHtml(ev.pmid);
      displayedPmids.add(ev.pmid);
      pmidHtml = `<div class="table-evidence-pmids"><a href="https://pubmed.ncbi.nlm.nih.gov/${safePmid}" target="_blank" class="pmid-link">PMID: ${safePmid}</a></div>`;
    }
    return `<div class="table-evidence-item">
      <div class="table-evidence-title">${title}</div>
      ${metaHtml}
      ${pmidHtml}
    </div>`;
  }).join('');

  const moreCount = items.length - limited.length;
  const extraPmids = fnPmids.filter(p => p && !displayedPmids.has(p));
  const extraPmidHtml = extraPmids.length ? `<div class="table-evidence-pmids">
    ${extraPmids.map(p => `<a href="https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(p)}" target="_blank" class="pmid-link">PMID: ${escapeHtml(p)}</a>`).join('')}
  </div>` : '';
  const moreHtml = moreCount > 0 ? `<div class="table-evidence-more">+${moreCount} more sources</div>` : '';

  return `<div class="table-evidence-list">${listHtml}${extraPmidHtml}${moreHtml}</div>`;
}

function renderEffectType(details) {
  if (!details || !details.text) {
    return '<span class="muted-text">Not specified</span>';
  }

  const arrowClass = details.arrow === 'activates' || details.arrow === 'inhibits' ? details.arrow : 'binds';
  return `<div class="expanded-effect-type ${arrowClass}">
    <span class="effect-type-badge ${arrowClass}">${escapeHtml(details.text)}</span>
  </div>`;
}

function getEffectTypeDetails(fn, arrow) {
  const normalized = (arrow || '').toLowerCase();
  const arrowKey = normalized === 'activates' || normalized === 'inhibits' ? normalized : 'binds';

  let text = '';
  if (fn && fn.effect_description) {
    text = fn.effect_description;
  }

  if (!text) {
    if (arrowKey === 'activates') text = 'Function is enhanced or activated';
    else if (arrowKey === 'inhibits') text = 'Function is inhibited or disrupted';
    else text = 'Binds / interacts';
  }

  return { text, arrow: arrowKey };
}

function getMechanismText(intent) {
  if (!intent) return null;
  const value = Array.isArray(intent) ? intent.find(Boolean) : intent;
  if (!value) return null;
  const str = String(value).trim();
  if (!str) return null;
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatArrow(arrow) {
  if (arrow === 'activates') return 'Activates';
  if (arrow === 'inhibits') return 'Inhibits';
  return 'Binds';
}

function toPastTense(verb) {
  // Convert infinitive verb form to past tense/past participle
  // Handles common verbs used in interaction/function effects
  const v = verb.toLowerCase();
  if (v === 'activate') return 'activated';
  if (v === 'inhibit') return 'inhibited';
  if (v === 'bind') return 'bound';  // Irregular verb
  if (v === 'regulate') return 'regulated';
  if (v === 'modulate') return 'modulated';
  if (v === 'complex') return 'complexed';
  if (v === 'suppress') return 'suppressed';
  if (v === 'enhance') return 'enhanced';
  if (v === 'promote') return 'promoted';
  if (v === 'repress') return 'repressed';
  // Default fallback for regular verbs
  if (v.endsWith('e')) return v + 'd';
  return v + 'ed';
}

function extractSourceProteinFromChain(fn, interactorProtein) {
  // Extract the immediate upstream protein that acts on the target (interactor)
  // For chain context: [Query, A, B, Target] → returns B (acts on Target)
  // Returns the protein that directly causes the effect on interactorProtein

  if (!fn._context || fn._context.type !== 'chain') {
    // No chain context - fallback to interactor itself
    return interactorProtein;
  }

  const chainArray = fn._context.chain;
  const queryProtein = fn._context.query_protein || '';

  if (!Array.isArray(chainArray) || chainArray.length === 0) {
    return interactorProtein;
  }

  // Full chain: [Query, ...intermediates, Target]
  const fullChain = [queryProtein, ...chainArray];

  // Find the target protein in the chain
  const targetIndex = fullChain.findIndex(p => p === interactorProtein);

  if (targetIndex > 0) {
    // Return the protein immediately before target (the one acting on it)
    return fullChain[targetIndex - 1];
  }

  // Fallback: return last protein in chain before target
  return chainArray[chainArray.length - 1] || interactorProtein;
}

function buildFullChainPath(queryProtein, chainArray, linkData) {
  // Build full chain display for INDIRECT labels
  // Input: query protein + chain array from link/function metadata
  // Output: "ATF6 → SREBP2 → HMGCR"

  if (!Array.isArray(chainArray) || chainArray.length === 0) {
    // No chain - check if linkData has upstream_interactor
    if (linkData && linkData.upstream_interactor) {
      return `${escapeHtml(queryProtein)} → ${escapeHtml(linkData.upstream_interactor)} → ${escapeHtml(linkData.primary)}`;
    }
    return '';
  }

  const fullChain = [queryProtein, ...chainArray];
  return fullChain.map(p => escapeHtml(p)).join(' → ');
}

function formatDirection(dir) {
  const v = (dir || '').toLowerCase();
  // Handle both query-relative AND absolute directions
  if (v === 'bidirectional' || v === 'undirected' || v === 'both') return 'Bidirectional';
  if (v === 'primary_to_main' || v === 'b_to_a') return 'Protein → Main';
  if (v === 'main_to_primary' || v === 'a_to_b') return 'Main → Protein';
  return 'Bidirectional';
}

function renderPMIDs(pmids) {
  if (!Array.isArray(pmids) || pmids.length === 0) return '—';

  return `<div class="pmid-list">
    ${pmids.slice(0, 5).map(p =>
      `<a href="https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(p)}" target="_blank" class="pmid-link">${escapeHtml(p)}</a>`
    ).join('')}
    ${pmids.length > 5 ? `<span style="color:#6b7280;font-size:12px;">+${pmids.length - 5} more</span>` : ''}
  </div>`;
}

function escapeHtml(text) {
  if (text == null) return '';
  const div = document.createElement('div');
  div.textContent = String(text);
  return div.innerHTML;
}

function escapeCsv(text) {
  if (text == null) return '';
  const str = String(text);
  // Escape quotes and wrap in quotes if contains comma, quote, or newline
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return '"' + str.replace(/"/g, '""') + '"';
  }
  return str;
}

function toggleExportDropdown() {
  const menu = document.getElementById('export-dropdown-menu');
  if (menu) {
    menu.classList.toggle('show');
  }
}

function closeExportDropdown() {
  const menu = document.getElementById('export-dropdown-menu');
  if (menu) {
    menu.classList.remove('show');
  }
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
  const dropdown = document.querySelector('.export-dropdown');
  if (dropdown && !dropdown.contains(e.target)) {
    closeExportDropdown();
  }
});

function buildFunctionExportRows() {
  const header = [
    'Source',
    'Target',
    'Interaction',
    'Effect',
    'Function',
    'Cellular Process',
    'Specific Effects',
    'Effect Type',
    'Mechanism',
    'Biological Cascade',
    'Support Summary',
    'Evidence Title',
    'Authors',
    'Journal',
    'Year',
    'PMID',
    'Quote'
  ];

  const rows = [header];
  const entries = collectFunctionEntries();

  if (entries.length === 0) {
    rows.push(new Array(header.length).fill(''));
    return rows;
  }

  entries.forEach(entry => {
    const fnData = entry.fnData || {};
    const interaction = `${entry.source} -> ${entry.target}`;
    const effectLabel = entry.arrow === 'activates' ? 'Activates' : (entry.arrow === 'inhibits' ? 'Inhibits' : 'Binds');
    const cellularProcessText = entry.cellularProcess || 'Not specified';
    const specificEffectsText = entry.specificEffects.length ? entry.specificEffects.join(' | ') : 'Not specified';
    const effectTypeText = entry.effectTypeDetails.text || '';
    const mechanismText = entry.mechanismText || 'Not specified';
    const bioCascadeText = entry.biologicalCascade.length ? entry.biologicalCascade.join(' -> ') : '';
    const supportSummary = entry.supportSummary || '';
    const evidenceItems = entry.evidence.length ? entry.evidence : [null];
    const pmidFallback = Array.isArray(fnData.pmids) ? fnData.pmids.join(' | ') : '';

    evidenceItems.forEach((ev, evIndex) => {
      const pmidValue = ev && ev.pmid ? ev.pmid : pmidFallback;

      rows.push([
        entry.source,
        entry.target,
        interaction,
        effectLabel,
        entry.functionLabel,
        cellularProcessText,
        specificEffectsText,
        effectTypeText,
        mechanismText,
        evIndex === 0 ? bioCascadeText : '',  // Only show biological cascade in first evidence row
        evIndex === 0 ? supportSummary : '',  // Only show support summary in first evidence row
        ev ? (ev.paper_title || '') : '',
        ev ? (ev.authors || '') : '',
        ev ? (ev.journal || '') : '',
        ev ? (ev.year || '') : '',
        pmidValue,
        ev ? (ev.relevant_quote || '') : ''
      ]);
    });
  });

  return rows;
}

function exportToCSV() {
  const rows = buildFunctionExportRows();
  const csvContent = rows
    .map(row => row.map(escapeCsv).join(','))
    .join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${SNAP.main}_interaction_network.csv`;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function exportToExcel() {
  if (typeof XLSX === 'undefined') {
    alert('Excel export library not loaded. Please refresh the page.');
    return;
  }

  const wb = XLSX.utils.book_new();
  const data = buildFunctionExportRows();
  const ws = XLSX.utils.aoa_to_sheet(data);
  XLSX.utils.book_append_sheet(wb, ws, 'Functions');
  XLSX.writeFile(wb, `${SNAP.main}_interaction_network.xlsx`);
}

function renderPMIDs(pmids) {
  if (!Array.isArray(pmids) || pmids.length === 0) return '-';

  return `<div class="pmid-list">
    ${pmids.slice(0, 5).map(p =>
      `<a href="https://pubmed.ncbi.nlm.nih.gov/${escapeHtml(p)}" target="_blank" class="pmid-link">${escapeHtml(p)}</a>`
    ).join('')}
    ${pmids.length > 5 ? `<span style="color:#6b7280;font-size:12px;">+${pmids.length - 5} more</span>` : ''}
  </div>`;
}

function escapeHtml(text) {
  if (text == null) return '';
  const div = document.createElement('div');
  div.textContent = String(text);
  return div.innerHTML;
}

function escapeCsv(text) {
  if (text == null) return '';
  const str = String(text);
  // Escape quotes and wrap in quotes if contains comma, quote, or newline
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return '"' + str.replace(/"/g, '""') + '"';
  }
  return str;
}

function toggleExportDropdown() {
  const menu = document.getElementById('export-dropdown-menu');
  if (menu) {
    menu.classList.toggle('show');
  }
}

function closeExportDropdown() {
  const menu = document.getElementById('export-dropdown-menu');
  if (menu) {
    menu.classList.remove('show');
  }
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
  const dropdown = document.querySelector('.export-dropdown');
  if (dropdown && !dropdown.contains(e.target)) {
    closeExportDropdown();
  }
});

/* ===== Re-query and Cancellation ===== */
let currentRunningJob = null;

async function requeryMainProtein() {
  if (!SNAP || !SNAP.main) {
    alert('No main protein found');
    return;
  }

  // Check if there's a running job
  if (currentRunningJob) {
    const confirmed = confirm(`A query is already running for ${currentRunningJob}. Cancel it and start a new re-query?`);
    if (confirmed) {
      await cancelCurrentJob();
      // Wait a moment for cancellation to process
      await new Promise(resolve => setTimeout(resolve, 500));
    } else {
      return;
    }
  }

  // Prompt for number of rounds
  const interactorInput = prompt('Number of interactor discovery rounds (1-8, default 1):', '1');
  if (interactorInput === null) return; // User cancelled

  const functionInput = prompt('Number of function mapping rounds (1-8, default 1):', '1');
  if (functionInput === null) return; // User cancelled

  const interactorRounds = Math.max(1, Math.min(8, parseInt(interactorInput) || 1));
  const functionRounds = Math.max(1, Math.min(8, parseInt(functionInput) || 1));

  currentRunningJob = SNAP.main;

  try {
    // Get list of current nodes to send as context
    const currentNodes = nodes
      .filter(n => n.type === 'main' || n.type === 'interactor')
      .map(n => n.id);

    // Start re-query
    const response = await fetch('/api/requery', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        protein: SNAP.main,
        current_nodes: currentNodes,
        interactor_rounds: interactorRounds,
        function_rounds: functionRounds
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Re-query failed');
    }

    // Start polling for status
    pollForComplete(SNAP.main, () => {
      // On complete, reload the page to show new data
      location.reload();
    });

  } catch (err) {
    console.error('Error starting re-query:', err);
    alert(`Failed to start re-query: ${err.message}`);
    currentRunningJob = null;
  }
}

async function pollForComplete(proteinName, onComplete) {
  const maxAttempts = 600; // 10 minutes max (1 check per second)
  let attempts = 0;

  const checkStatus = async () => {
    try {
      const response = await fetch(`/api/status/${proteinName}`);
      const data = await response.json();

      if (data.status === 'complete') {
        miniDone('Re-query complete! Refreshing...');
        currentRunningJob = null;
        currentJobProtein = null;
        // Reload immediately to show new data
        if (onComplete) {
          onComplete();
        } else {
          // Fallback: reload anyway
          setTimeout(() => location.reload(), 500);
        }
        return;
      } else if (data.status === 'error') {
        const errorText = typeof data.progress === 'object' ? data.progress.text : data.progress;
        miniDone(`Error: ${errorText}`);
        currentRunningJob = null;
        return;
      } else if (data.status === 'cancelled') {
        miniDone('Cancelled');
        currentRunningJob = null;
        return;
      } else if (data.status === 'processing') {
        const prog = data.progress || {};
        const text = prog.text || 'Processing...';
        const current = prog.current || 0;
        const total = prog.total || 100;
        miniProgress(text, current, total, proteinName);
      }

      // Keep polling
      attempts++;
      if (attempts < maxAttempts) {
        setTimeout(checkStatus, 1000);
      } else {
        miniDone('Timeout waiting for re-query');
        currentRunningJob = null;
      }
    } catch (err) {
      console.error('Error polling status:', err);
      miniDone('Error checking status');
      currentRunningJob = null;
    }
  };

  checkStatus();
}

/* ===== Chat Functions ===== */
// Chat state
let chatHistory = [];
let chatPending = false;
const MAX_CHAT_HISTORY = 10; // Configurable max history to send to LLM

/**
 * Build compact state snapshot for LLM context.
 * Sends only visible protein list - backend reads full data from cache JSON.
 */
function buildChatCompactState() {
  // Collect all visible proteins (main + interactors only, not function nodes)
  const visibleProteins = new Set();

  // Always include root protein (with safety check)
  const mainProtein = SNAP && SNAP.main ? SNAP.main : 'Unknown';
  if (mainProtein !== 'Unknown') {
    visibleProteins.add(mainProtein);
  }

  // Add all visible interactor proteins from nodes array (with safety check)
  if (Array.isArray(nodes)) {
    nodes.forEach(n => {
      if (n && n.id && (n.type === 'main' || n.type === 'interactor')) {
        visibleProteins.add(n.id);
      }
    });
  }

  return {
    parent: mainProtein,
    visible_proteins: Array.from(visibleProteins)
  };
}

/**
 * Render a chat message in the UI.
 */
function renderChatMessage(role, content, isError = false) {
  const messagesContainer = document.getElementById('chat-messages');
  if (!messagesContainer) return;

  const messageDiv = document.createElement('div');

  if (isError) {
    messageDiv.className = 'chat-message error-message';
  } else if (role === 'user') {
    messageDiv.className = 'chat-message user-message';
  } else if (role === 'assistant') {
    messageDiv.className = 'chat-message assistant-message';
  } else if (role === 'system') {
    messageDiv.className = 'chat-message system-message';
  }

  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  contentDiv.textContent = content;

  messageDiv.appendChild(contentDiv);
  messagesContainer.appendChild(messageDiv);

  // Auto-scroll to bottom
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Send chat message to backend.
 */
async function sendChatMessage() {
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send-btn');
  const sendText = document.getElementById('chat-send-text');
  const sendLoading = document.getElementById('chat-send-loading');

  if (!input || !sendBtn) return;

  const userMessage = input.value.trim();
  if (!userMessage || chatPending) return;

  // Early validation: ensure SNAP exists before starting
  if (!SNAP || !SNAP.main) {
    renderChatMessage('error', 'Error: No protein data loaded', true);
    return;
  }

  // Update UI state
  chatPending = true;
  input.value = '';
  input.disabled = true;
  sendBtn.disabled = true;
  sendText.style.display = 'none';
  sendLoading.style.display = 'inline';

  // Add user message to history and UI
  chatHistory.push({ role: 'user', content: userMessage });
  renderChatMessage('user', userMessage);

  try {
    // Build compact state for context
    const compactState = buildChatCompactState();

    // Prepare request payload
    const payload = {
      parent: SNAP.main,
      messages: chatHistory,
      state: compactState,
      max_history: MAX_CHAT_HISTORY,
    };

    // Call chat API
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle API error
      const errorMsg = data.error || `Server error (${response.status})`;
      throw new Error(errorMsg);
    }

    // Extract reply
    const reply = data.reply;
    if (!reply) {
      throw new Error('Empty response from server');
    }

    // Add assistant response to history and UI
    chatHistory.push({ role: 'assistant', content: reply });
    renderChatMessage('assistant', reply);

    // Trim chat history to prevent unbounded growth
    // Keep only the most recent MAX_CHAT_HISTORY * 2 messages (generous buffer)
    const maxClientHistory = MAX_CHAT_HISTORY * 2;
    if (chatHistory.length > maxClientHistory) {
      chatHistory = chatHistory.slice(-maxClientHistory);
    }

  } catch (error) {
    console.error('Chat error:', error);

    // Render error message
    const errorText = error.message || 'Failed to get response. Please try again.';
    renderChatMessage('error', `Error: ${errorText}`, true);

    // Remove the user message from history if request failed
    chatHistory.pop();

  } finally {
    // Reset UI state
    chatPending = false;
    input.disabled = false;
    sendBtn.disabled = false;
    sendText.style.display = 'inline';
    sendLoading.style.display = 'none';
    input.focus();
  }
}

/**
 * Handle Enter key in chat input (Shift+Enter for new line, Enter to send).
 */
function handleChatKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendChatMessage();
  }
}

// Wire up chat input keyboard handler
document.addEventListener('DOMContentLoaded', () => {
  const chatInput = document.getElementById('chat-input');
  if (chatInput) {
    chatInput.addEventListener('keydown', handleChatKeydown);
  }
});

/* Wire up */
document.addEventListener('DOMContentLoaded', () => {
  // Restore theme preference (dark mode is default)
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'light') {
    document.body.classList.remove('dark-mode');
  } else if (!savedTheme) {
    // First visit: ensure dark mode is set
    localStorage.setItem('theme', 'dark');
  }

  // Update theme toggle icon
  const isDark = document.body.classList.contains('dark-mode');
  const icon = document.getElementById('theme-icon');
  if (icon) {
    icon.textContent = isDark ? '☀️' : '🌙';
  }

  // Wire up search bar - use same flow as interactor expansion
  const queryBtn = document.getElementById('query-button');
  const proteinInp = document.getElementById('protein-input');
  if (queryBtn && proteinInp) {
    const handleQuery = async () => {
      const p = proteinInp.value.trim();
      if (!p) {
        miniDone('<span style="color:#dc2626;">Please enter a protein name.</span>');
        return;
      }
      if (!/^[a-zA-Z0-9_-]+$/.test(p)) {
        miniDone('<span style="color:#dc2626;">Invalid format. Use only letters, numbers, hyphens, and underscores.</span>');
        return;
      }

      // Check if protein already cached
      try {
        const res = await fetch(`/api/results/${encodeURIComponent(p)}`);
        if (res.ok) {
          // Cached - redirect immediately
          window.location.href = `/api/visualize/${encodeURIComponent(p)}?t=${Date.now()}`;
          return;
        }
      } catch(e) {}

      // Not cached - queue and wait (same as interactor expansion)
      try {
        await queueAndWaitFull(p);
        // On success, redirect to viz page
        window.location.href = `/api/visualize/${encodeURIComponent(p)}?t=${Date.now()}`;
      } catch(err) {
        // queueAndWaitFull already shows error via miniDone
        if (err instanceof CancellationError || err.name === 'CancellationError') {
          return; // Silent exit on cancellation
        }
      }
    };
    queryBtn.addEventListener('click', handleQuery);
    proteinInp.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); handleQuery(); } });
  }

  // === SMART HEADER AUTO-HIDE ===
  // Solves the "hover chase" bug where panels shift as header shows/hides
  // Strategy: Delay hiding + extend hover zone to include panels
  (function initHeaderAutoHide() {
    const header = document.querySelector('.header');
    const headerTrigger = document.querySelector('.header-trigger');
    const controlsPanel = document.querySelector('.controls');
    const infoPanel = document.querySelector('.info-panel');

    if (!header || !headerTrigger) return;

    let hideTimer = null;
    let isHeaderVisible = false;

    // Check if header is in static mode (table view)
    function isStaticMode() {
      return header.classList.contains('header-static');
    }

    // Show header immediately (unless in static mode)
    function show() {
      if (isStaticMode()) return; // Don't toggle in static mode

      if (hideTimer) {
        clearTimeout(hideTimer);
        hideTimer = null;
      }
      if (!isHeaderVisible) {
        header.classList.add('header-visible');
        isHeaderVisible = true;
      }
    }

    // Hide header after delay (allows smooth mouse movement)
    function scheduleHide() {
      if (isStaticMode()) return; // Don't toggle in static mode

      if (hideTimer) clearTimeout(hideTimer);
      hideTimer = setTimeout(() => {
        header.classList.remove('header-visible');
        isHeaderVisible = false;
        hideTimer = null;
      }, 400); // 400ms grace period
    }

    // Attach hover listeners to all relevant elements
    [headerTrigger, header, controlsPanel, infoPanel].forEach(el => {
      if (!el) return;

      el.addEventListener('mouseenter', () => {
        show();
      });

      el.addEventListener('mouseleave', () => {
        scheduleHide();
      });
    });

    // Also respond to focus within header (keyboard accessibility)
    header.addEventListener('focusin', () => {
      show();
    });

    header.addEventListener('focusout', () => {
      scheduleHide();
    });
  })();

  initNetwork();
  buildTableView(); // Build initial table
  initColumnResizing(); // Initialize column resizing
  // Initialize with graph view active
  document.body.classList.add('graph-view-active');
  const container = document.querySelector('.container');
  if (container) container.classList.add('graph-active');
});
window.addEventListener('resize', ()=>{
  const el = document.getElementById('network');
  if (!el || !svg) return;
  const newWidth = el.clientWidth || width;
  const newHeight = el.clientHeight || height;
  if (newWidth) width = newWidth;
  if (newHeight) height = newHeight;
  svg.attr('width', width).attr('height', height);
  if (simulation) {
    simulation.force('center', d3.forceCenter(width / 2, height / 2));
    reheatSimulation(0.4);
  }
  scheduleFitToView(200, false);
});
</script>
</body>
</html>
"""

def _load_json(obj):
    if isinstance(obj, (str, bytes, Path)):
        return json.loads(Path(obj).read_text(encoding="utf-8"))
    if isinstance(obj, dict):
        return obj
    raise TypeError("json_data must be path or dict")

# JSON helper functions for data cleaning and validation
def _resolve_symbol(entry):
    """Resolves protein symbol from various field names"""
    for key in ('primary', 'hgnc_symbol', 'symbol', 'gene', 'name'):
        value = entry.get(key) if isinstance(entry, dict) else None
        if isinstance(value, str) and value.strip():
            return value.strip()
    placeholder = None
    if isinstance(entry, dict):
        placeholder = entry.get('id') or entry.get('interactor_id') or entry.get('mechanism_id')
    if placeholder:
        return f"MISSING_{placeholder}"
    return None

def _normalize_interactors(interactors):
    """Normalizes interactor data structure"""
    if not isinstance(interactors, list):
        return
    for idx, interactor in enumerate(interactors):
        if not isinstance(interactor, dict):
            continue
        symbol = _resolve_symbol(interactor)
        if not symbol:
            symbol = f"MISSING_{idx + 1}"
        current = interactor.get('primary')
        if not isinstance(current, str) or not current.strip():
            interactor['primary'] = symbol
        else:
            interactor['primary'] = current.strip()
        interactor.setdefault('hgnc_symbol', interactor['primary'])
        functions = interactor.get('functions')
        if isinstance(functions, list):
            interactor['functions'] = functions
        elif functions:
            interactor['functions'] = [functions]
        else:
            interactor['functions'] = []

def _build_interactor_key(interactor):
    """Creates unique key for interactor matching"""
    if not isinstance(interactor, dict):
        return None
    pmids = interactor.get('pmids')
    if isinstance(pmids, list) and pmids:
        normalized_pmids = tuple(sorted(str(pmid) for pmid in pmids))
        return ('pmids', normalized_pmids)
    summary = interactor.get('support_summary')
    if isinstance(summary, str) and summary.strip():
        return ('summary', summary.strip())
    mechanism = interactor.get('mechanism_details')
    if isinstance(mechanism, list) and mechanism:
        return ('mechanism', tuple(sorted(mechanism)))
    return None

def _hydrate_snapshot_from_ctx(snapshot_interactors, ctx_interactors):
    """Hydrates snapshot data with richer ctx_json data"""
    if not isinstance(snapshot_interactors, list) or not isinstance(ctx_interactors, list):
        return
    ctx_lookup = {}
    for ctx in ctx_interactors:
        key = _build_interactor_key(ctx)
        if key:
            ctx_lookup.setdefault(key, []).append(ctx)
    for idx, snap in enumerate(snapshot_interactors):
        if not isinstance(snap, dict):
            continue
        matched_ctx = None
        key = _build_interactor_key(snap)
        if key and key in ctx_lookup and ctx_lookup[key]:
            matched_ctx = ctx_lookup[key].pop(0)
        elif idx < len(ctx_interactors):
            matched_ctx = ctx_interactors[idx]
        if matched_ctx:
            primary_symbol = matched_ctx.get('primary') or matched_ctx.get('hgnc_symbol') or matched_ctx.get('symbol')
            if isinstance(primary_symbol, str) and primary_symbol.strip():
                snap.setdefault('primary', primary_symbol.strip())
                snap.setdefault('hgnc_symbol', primary_symbol.strip())

# Function name shortening map - REMOVED to preserve AI-generated specificity
# Previous NAME_FIXES was making specific names vague:
#   "ATXN3 Degradation" → "Degradation" (loses what's being degraded!)
#   "RNF8 Stability & DNA Repair" → "DNA repair" (loses the protein!)
#   "Apoptosis Inhibition" → "Apoptosis" (loses the arrow direction!)
# The AI prompts now generate specific, arrow-compatible names - preserve them!
NAME_FIXES = {}

def validate_function_name(name: str) -> tuple[bool, str]:
    """
    Check if function name is specific enough.
    Returns (is_valid, error_message)
    """
    if not name or not isinstance(name, str):
        return (False, "Function name is missing or invalid")

    name_lower = name.lower().strip()

    # Too short
    if len(name) < 5:
        return (False, f"Function name '{name}' is too short (< 5 chars)")

    # Check for overly generic terms without specifics
    generic_patterns = [
        ('regulation', 30),   # "Regulation" is vague unless part of longer specific name
        ('control', 25),      # "Control" is vague
        ('response', 25),     # "Response" is vague (unless specific like "DNA Damage Response")
        ('metabolism', 20),   # "Metabolism" alone is too vague
        ('signaling', 20),    # "Signaling" alone is too vague
        ('pathway', 20),      # "Pathway" alone is too vague
    ]

    for term, min_length in generic_patterns:
        if term in name_lower and len(name) < min_length:
            return (False, f"Function name '{name}' is too generic (contains '{term}' but too short)")

    # Check for very generic standalone terms
    very_generic = [
        'function', 'process', 'activity', 'mechanism', 'role',
        'involvement', 'participation', 'interaction'
    ]
    if name_lower in very_generic:
        return (False, f"Function name '{name}' is extremely generic")

    return (True, "")


def validate_interactor_quality(interactor: dict) -> list[str]:
    """
    Check for data quality issues in an interactor.
    Returns list of warning messages.
    """
    issues = []
    primary = interactor.get('primary', 'Unknown')

    # Check interactor-level confidence
    interactor_conf = interactor.get('confidence')
    if interactor_conf is not None and interactor_conf == 0:
        issues.append(f"{primary}: interaction confidence is 0 (likely data error)")

    # Check functions
    for idx, func in enumerate(interactor.get('functions', [])):
        func_name = func.get('function', f'Function #{idx}')

        # Validate function name specificity
        is_valid, msg = validate_function_name(func_name)
        if not is_valid:
            issues.append(f"{primary}/{func_name}: {msg}")

        # Validate function confidence
        fn_conf = func.get('confidence')
        if fn_conf is not None and fn_conf == 0:
            issues.append(f"{primary}/{func_name}: function confidence is 0 (likely data error)")

        # Check if arrow and function name are compatible
        arrow = func.get('arrow', '')
        if arrow in ['activates', 'inhibits']:
            # Function name should describe a process that can be activated/inhibited
            # This is a heuristic check
            incompatible_terms = ['interaction', 'binding', 'association']
            if any(term in func_name.lower() for term in incompatible_terms):
                issues.append(f"{primary}/{func_name}: arrow='{arrow}' may not match function name")

    return issues


def _refresh_pmids_if_needed(json_data) -> None:
    if isinstance(json_data, (str, bytes, Path)):
        json_path = Path(json_data)
        if json_path.exists():
            try:
                subprocess.run(
                    [sys.executable, "update_cache_pmids.py", str(json_path)],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            except (subprocess.CalledProcessError, FileNotFoundError) as exc:
                print(f"[warn] Unable to refresh PMIDs for {json_path}: {exc}")


def create_visualization(json_data, output_path=None):
    # PMID refresh disabled: PMIDs are already updated during pipeline execution (runner.py STAGE 5)
    # This eliminates 10-40 second blocking delays on visualization requests
    # _refresh_pmids_if_needed(json_data)
    data = _load_json(json_data)

    # CHANGED: Only use snapshot_json, completely ignore ctx_json
    # This simplifies the pipeline and reduces file sizes
    if 'snapshot_json' in data:
        # Use snapshot_json directly
        viz_data = data['snapshot_json']
        _normalize_interactors(viz_data.get('interactors', []))
    elif 'main' in data and 'interactors' in data:
        # Legacy format or direct snapshot - use data as-is
        viz_data = data
        _normalize_interactors(viz_data.get('interactors', []))
    else:
        # No valid data structure found
        raise ValueError("Invalid JSON structure: expected 'snapshot_json' or 'main'/'interactors' fields")

    # Merge interactors with duplicate primaries
    if isinstance(viz_data, dict):
        merged_interactors = {}
        for interactor in viz_data.get('interactors', []):
            primary = interactor.get('primary')
            if primary in merged_interactors:
                # Merge with existing
                existing = merged_interactors[primary]
                # Combine functions
                existing['functions'].extend(interactor.get('functions', []))
                # Keep higher confidence
                if interactor.get('confidence', 0) > existing.get('confidence', 0):
                    existing['confidence'] = interactor['confidence']
                # Combine evidence
                if 'evidence' in interactor:
                    if 'evidence' not in existing:
                        existing['evidence'] = []
                    existing['evidence'].extend(interactor['evidence'])
                # Note if there are multiple interaction types
                if existing.get('arrow') != interactor.get('arrow') or existing.get('direction') != interactor.get('direction'):
                    existing['multiple_arrows'] = True
                    if 'all_arrows' not in existing:
                        existing['all_arrows'] = [existing.get('arrow')]
                        existing['all_directions'] = [existing.get('direction')]
                        existing['all_intents'] = [existing.get('intent')]
                    existing['all_arrows'].append(interactor.get('arrow'))
                    existing['all_directions'].append(interactor.get('direction'))
                    existing['all_intents'].append(interactor.get('intent', 'binding'))
            else:
                merged_interactors[primary] = interactor.copy()
                merged_interactors[primary]['functions'] = interactor.get('functions', []).copy()
        viz_data['interactors'] = list(merged_interactors.values())

    # Get main protein name (with fallback logic)
    main = viz_data.get('main', 'Unknown')
    if not main or main == 'UNKNOWN':
        main = 'Unknown'

    # Validate data quality and log warnings
    all_issues = []
    for interactor in viz_data.get('interactors', []):
        issues = validate_interactor_quality(interactor)
        all_issues.extend(issues)

    if all_issues:
        print(f"\n⚠️  Data Quality Warnings for {main}:")
        for issue in all_issues[:10]:  # Limit to first 10 to avoid spam
            print(f"  - {issue}")
        if len(all_issues) > 10:
            print(f"  ... and {len(all_issues) - 10} more warnings")
        print()

    # Prepare final data for embedding
    raw = data  # Keep original structure for backwards compatibility

    # Title uses snapshot_json.main or fallback
    try:
        main = (raw.get('snapshot_json') or {}).get('main') or raw.get('main') or raw.get('primary') or 'Protein'
    except Exception:
        main = raw.get('main') or raw.get('primary') or 'Protein'

    html = HTML.replace('PLACEHOLDER_MAIN', str(main))
    html = html.replace('PLACEHOLDER_JSON', json.dumps(raw, ensure_ascii=False))

    if output_path:
        # If output_path provided, write to file and return path
        p = Path(output_path)
        p.write_text(html, encoding='utf-8')
        return str(p.resolve())
    else:
        # If no output_path, return HTML content directly (for web endpoints)
        return html

def open_visualization(html_path):
    """Opens the HTML visualization in the default web browser"""
    import webbrowser
    p = Path(html_path)
    webbrowser.open(f"file://{p.absolute()}")


def create_visualization_from_dict(data_dict, output_path=None):
    """
    Create visualization from dict (not file).

    NEW: Accepts dict directly from database (PostgreSQL).
    This maintains compatibility with existing frontend while enabling
    database-backed visualization.

    Args:
        data_dict: Dict with {snapshot_json: {...}, ctx_json: {...}}
        output_path: Optional output file path. If None, returns HTML content.

    Returns:
        HTML string if output_path is None, else path to saved HTML file

    Note:
        Internally calls create_visualization() which supports both
        dict input (via _load_json) and returns HTML or file path based on output_path.
    """
    if not isinstance(data_dict, dict):
        raise TypeError("data_dict must be a dict")

    # create_visualization already supports dict input via _load_json
    return create_visualization(data_dict, output_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python visualizer.py <json_file> [output_html]"); raise SystemExit(2)
    src = sys.argv[1]; dst = sys.argv[2] if len(sys.argv)>2 else None
    out = create_visualization(src, dst); print("Wrote:", out)
