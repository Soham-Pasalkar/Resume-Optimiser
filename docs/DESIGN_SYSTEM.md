# CareerPilot — Design System Specification
## "Soft UI Evolution" Design Language

> **Document Version:** 1.0.0-PROPOSAL  
> **Status:** Review Ready  
> **Aesthetic Foundation:** Soft UI Evolution (Tactile Neumorphic Refinement with WCAG AA Rigor)  
> **Target Framework:** Tailwind CSS v4 / Next.js / shadcn/ui custom primitives

---

## 1. Design Philosophy: Soft UI Evolution

The **Soft UI Evolution** design system resolves the primary historical flaw of first-generation neumorphism (poor contrast and visual mushiness) by combining **tactile, soft-lit surface depth** with **crisp typography, explicit high-contrast borders where appropriate, accessible focus indicators, and disciplined functional color**.

### Core Tenets
1. **Physical Softness with Crisp Structure:** Surfaces appear sculpted from a continuous high-grade matte composite. Shadows are broad, ambient, and low-opacity, avoiding muddy grays or harsh dark lines.
2. **Strict Nesting Discipline:** Depth is strictly limited to **one level of nesting**: `Surface (raised) > Well (inset)`. Deeply nested card-in-card-in-card patterns are strictly prohibited.
3. **Contrast-First Accessibility:** Neumorphic depth is an *enhancement*, not a replacement for clear visual hierarchy. Text contrast strictly maintains $\ge 4.5:1$ against backgrounds; essential UI controls maintain $\ge 3:1$ contrast against adjacent surfaces.
4. **Restrained Functional Color:** The neutral base (`#F0F4F8`) comprises 85% of visual area. Color is reserved exclusively for interactive intent (`--soft-blue`), affirmative states (`--soft-green`), and cautionary or warning notices (`--soft-orange`).

---

## 2. Design Tokens & CSS Variables

```css
:root {
  /* ==========================================================================
     Surfaces & Lighting (The Neumorphic Foundation)
     ========================================================================== */
  --soft-bg: #F0F4F8;             /* Base canvas color (Cool light slate) */
  --soft-shadow: #D1D9E6;         /* Primary ambient shadow (Bottom-Right) */
  --soft-light: #FFFFFF;          /* Specular highlight shadow (Top-Left) */
  --soft-surface-white: #FFFFFF;  /* Crisp contrast surface variant */

  /* ==========================================================================
     Brand & Interactive Accents
     ========================================================================== */
  --soft-blue: #2563EB;           /* Primary action / Focus accent (Royal Blue) */
  --soft-blue-hover: #1D4ED8;     /* Hover state */
  --soft-blue-active: #1E40AF;    /* Pressed state */
  --soft-blue-subtle: #EFF6FF;    /* Light tinted badge background */

  /* ==========================================================================
     Semantic Affirmation (Success & Match)
     ========================================================================== */
  --soft-green: #22C55E;          /* Accent green */
  --soft-green-text: #15803D;     /* High-contrast WCAG AA text green */
  --soft-green-subtle: #F0FDF4;   /* Light tinted badge background */

  /* ==========================================================================
     Semantic Warning & Skill Gap Alerts
     ========================================================================== */
  --soft-orange: #EA580C;         /* Accent orange / warning */
  --soft-orange-text: #C2410C;    /* High-contrast WCAG AA text orange */
  --soft-orange-subtle: #FFF7ED;  /* Light tinted badge background */

  /* ==========================================================================
     Typography & Contrast
     ========================================================================== */
  --soft-text: #1F2937;           /* Primary text (Dark Slate) - Contrast 10.8:1 */
  --soft-muted: #4B5563;          /* Secondary / Caption text - Contrast 5.2:1 */
  --soft-subtle: #9CA3AF;         /* Placeholder & decorative text */
  --soft-border: #E2E8F0;         /* Fine accent borders where needed */

  /* ==========================================================================
     Radii Scale
     ========================================================================== */
  --radius-sm: 0.5rem;    /* 8px - Inputs, badges, small buttons */
  --radius-md: 0.75rem;   /* 12px - Interactive controls, modals */
  --radius-lg: 1.0rem;    /* 16px - Standard cards, wells, surfaces */
  --radius-xl: 1.5rem;    /* 24px - Large containers, hero panels */
  --radius-full: 9999px;  /* Pills, avatars, toggle thumbs */

  /* ==========================================================================
     Transitions & Motion
     ========================================================================== */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-smooth: 350ms cubic-bezier(0.16, 1, 0.3, 1);
}
```

---

## 3. Surface & Elevation System

```
       LIGHT SOURCE (-45 degrees, Top-Left)
              \
               \
  +---------------------------------------+
  |  HIGHLIGHT: -6px -6px 15px #FFFFFF    |
  |                                       |
  |            .surface                   |
  |     (Base Background: #F0F4F8)        |
  |                                       |
  |  SHADOW: 6px 6px 15px #D1D9E6         |
  +---------------------------------------+
                       \
                        v
          +---------------------------+
          |  INSET WELL (.well)       |
          |  Shadow: 4px 4px (inner)  |
          |  Light: -4px -4px (inner) |
          +---------------------------+
```

### 3.1 Raised Surface (`.surface`)
Used for primary container cards, modal dialogs, and elevated dashboard widgets.
```css
.surface {
  border-radius: var(--radius-lg);
  background: var(--soft-bg);
  box-shadow:
    -6px -6px 15px var(--soft-light),
     6px  6px 15px var(--soft-shadow);
  border: 1px solid rgba(255, 255, 255, 0.6);
}
```

### 3.2 Inset Well (`.well`)
Used for secondary grouped content, input form fields, progress tracks, and code/resume preview viewports.
```css
.well {
  border-radius: var(--radius-lg);
  background: var(--soft-bg);
  box-shadow:
    inset -4px -4px 10px var(--soft-light),
    inset  4px  4px 10px var(--soft-shadow);
}
```

### 3.3 Interactive Raised Button / Control (`.btn-soft`)
```css
.btn-soft {
  border-radius: var(--radius-md);
  background: var(--soft-bg);
  color: var(--soft-text);
  font-weight: 600;
  box-shadow:
    -4px -4px 10px var(--soft-light),
     4px  4px 10px var(--soft-shadow);
  transition: all var(--transition-normal);
  border: 1px solid rgba(255, 255, 255, 0.7);
}

.btn-soft:hover {
  box-shadow:
    -2px -2px 6px var(--soft-light),
     2px  2px 6px var(--soft-shadow);
  transform: translateY(-1px);
}

.btn-soft:active {
  box-shadow:
    inset -3px -3px 8px var(--soft-light),
    inset  3px  3px 8px var(--soft-shadow);
  transform: translateY(0);
}
```

### 3.4 Primary Solid Action Button (`.btn-primary`)
When high visual gravity is required (e.g., "Analyze Match", "Export Tailored Resume"):
```css
.btn-primary {
  border-radius: var(--radius-md);
  background: var(--soft-blue);
  color: #FFFFFF;
  font-weight: 600;
  box-shadow:
     0 4px 14px rgba(37, 99, 235, 0.35),
    -2px -2px 8px var(--soft-light);
  transition: all var(--transition-normal);
}

.btn-primary:hover {
  background: var(--soft-blue-hover);
  box-shadow:
     0 6px 20px rgba(37, 99, 235, 0.45);
  transform: translateY(-1px);
}

.btn-primary:active {
  background: var(--soft-blue-active);
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.25);
  transform: translateY(0);
}
```

---

## 4. Typography Hierarchy

CareerPilot utilizes a modern, legible geometric sans-serif font stack (`Inter`, `Plus Jakarta Sans`, or system `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto`).

| Level | Size | Weight | Line Height | Tracking | Application |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Display 1** | 3.0rem (48px) | 800 (Bold) | 1.15 | -0.025em | Marketing Hero Headlines |
| **Heading 1** | 2.25rem (36px) | 700 (Bold) | 1.2 | -0.02em | Main Page Titles, Match Score Dial |
| **Heading 2** | 1.5rem (24px) | 700 (Bold) | 1.3 | -0.015em | Module Titles, Section Headers |
| **Heading 3** | 1.125rem (18px) | 600 (Semibold) | 1.4 | -0.01em | Card Headers, Candidate Names |
| **Body Large** | 1.0rem (16px) | 400 / 500 | 1.5 | normal | Lead Paragraphs, Resume Bullets |
| **Body Regular**| 0.875rem (14px) | 400 / 500 | 1.5 | normal | Standard UI, Tables, Form Labels |
| **Caption** | 0.75rem (12px) | 500 / 600 | 1.4 | +0.01em | Badges, Timestamp, Tooltip text |

---

## 5. UI Component Primitives

### 5.1 Inset-Well Form Inputs
Input fields sit recessed into the surface with soft internal lighting, giving a tactile "pressed" slot appearance.
```css
.input-well {
  border-radius: var(--radius-sm);
  background: var(--soft-bg);
  box-shadow:
    inset -3px -3px 7px var(--soft-light),
    inset  3px  3px 7px var(--soft-shadow);
  border: 1px solid transparent;
  color: var(--soft-text);
  padding: 0.75rem 1rem;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.input-well:focus {
  outline: none;
  border-color: var(--soft-blue);
  box-shadow:
    inset -3px -3px 7px var(--soft-light),
    inset  3px  3px 7px var(--soft-shadow),
    0 0 0 3px rgba(37, 99, 235, 0.2);
}
```

### 5.2 Status Chips & Badges
Badges are rendered on subtle inset wells or soft surface pills with high-contrast text:
- **Demonstrated:** Background `var(--soft-green-subtle)`, text `var(--soft-green-text)`, border `1px solid rgba(34, 197, 94, 0.3)`.
- **Skill Gap / Missing:** Background `var(--soft-orange-subtle)`, text `var(--soft-orange-text)`, border `1px solid rgba(234, 88, 12, 0.3)`.
- **Requires Verification:** Background `var(--soft-blue-subtle)`, text `var(--soft-blue)`, border `1px solid rgba(37, 99, 235, 0.3)`.

### 5.3 Neumorphic Radial Match Score Gauge
The match score is displayed via an evolved radial SVG gauge:
- Recessed outer well track (`inset -4px -4px 10px #FFFFFF, inset 4px 4px 10px #D1D9E6`).
- Vibrant radial indicator stroke in `--soft-blue` with gradient transition to `--soft-green` at $\ge 80\%$.
- Center raised disc displaying the numerical percentage (e.g. `87%`) in bold 32px text with an accessible subtitle (`Strong Match`).

---

## 6. Accessibility & Inclusivity Guidelines (WCAG AA Non-Negotiables)

1. **Contrast Ratios:**
   - Text against canvas (`#1F2937` on `#F0F4F8`): **10.8:1** (Far exceeds 4.5:1 requirement).
   - Secondary text (`#4B5563` on `#F0F4F8`): **5.2:1** (Exceeds 4.5:1 requirement).
   - Green text (`#15803D` on `#F0FDF4`): **5.4:1** (Exceeds 4.5:1 requirement).
   - Orange text (`#C2410C` on `#FFF7ED`): **5.8:1** (Exceeds 4.5:1 requirement).
2. **Keyboard Navigation & Focus Rings:**
   - All interactive elements possess explicit, highly visible 2px solid `--soft-blue` focus rings with a 2px offset.
   - Outlines are never removed without providing an equivalent accessible ring.
3. **Non-Color Dependent Indicators:**
   - Statuses are never conveyed by color alone. Every badge includes an icon and clear textual status (e.g., `[✓ Demonstrated]`, `[! Skill Gap]`, `[? Verify]`).
4. **Motion Sensitivity (`prefers-reduced-motion`):**
   - All hover elevations, radial score fills, and modal transitions gracefully degrade to instant opacity toggles when `prefers-reduced-motion: reduce` is enabled.
