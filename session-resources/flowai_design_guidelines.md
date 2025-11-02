# FlowAI — Design Guidelines for Coding Agent

## 🎨 Color Palette
**Goal:** Minimal, modern, mostly monochrome interface with subtle color accents.

### Base Colors
- **Background:** `#FFFFFF` or light gray `#F5F5F5`
- **Primary text:** `#111111` (charcoal black)
- **Secondary text:** `#555555` (medium gray)
- **Borders / dividers:** `#E0E0E0`

### Accent Colors
Choose **one main accent color**, used sparingly:
- Example: **Deep Blue:** `#0055FF`
- Alternative: **Muted Teal:** `#009688`

Accent is used for buttons, links, highlights, and active elements.

Optional secondary accent for warnings or states:
- **Amber:** `#FFA000`
- **Soft Red:** `#D32F2F`

> Keep the UI mostly grayscale, use color only to guide attention.

---

## 🅰 Typography
**Objective:** Clear, modern, and highly readable.

### Fonts
- Primary font: “Inter”, “Roboto”, or “Helvetica Neue”
- Monospace font (for code): “JetBrains Mono” or “Source Code Pro”

### Sizing & Weight
- **Body text:** 16px, line-height 1.5
- **Headings:** H1 32px / H2 24px / H3 20px
- **UI labels / inputs:** 14–15px

### Hierarchy & Style
- Headings: dark text or accent color
- Secondary information: lighter gray
- Links & buttons: accent color (underline or bold on hover)

---

## 📐 Layout & Spacing
**Principles:** Airy, balanced, consistent spacing.

- Sidebar width: 280–320px
- Use white or very light backgrounds for main content
- Provide consistent padding (e.g., 24px per section)
- Avoid visual clutter, use whitespace generously

### Cards / Panels
- Background: `#FFFFFF`
- Border: `#E0E0E0`
- Border-radius: 4px
- Optional soft shadow for elevation

### Buttons
- **Primary button:** filled with accent color, white text
- **Secondary button:** outline style, accent border, transparent background
- **Hover state:** slightly darker accent shade

### Inputs / Fields
- Minimal borders (`#CCCCCC`)
- Focused: accent border
- Use clear labels and spacing

---

## 🎨 Streamlit Theme Configuration
Define your custom theme in `.streamlit/config.toml`:

```toml
[theme]
base = "light"
primaryColor = "#0055FF"          # your chosen accent
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F9F9F9"
textColor = "#111111"
font = "sans serif"

[theme.sidebar]
backgroundColor = "#F9F9F9"
textColor = "#111111"

# Optional extras
linkColor = "#0055FF"
buttonRadius = 4
baseRadius = 4
borderColor = "#D0D0D0"
```

> Restart Streamlit after editing `config.toml` to apply changes.

---

## 💡 UI Principles
- **Keep it minimal:** avoid gradients or multiple bright colors.
- **Be consistent:** use one accent color throughout.
- **Industrial aesthetic:** prioritize clarity, precision, and reliability.
- **Readable contrast:** ensure sufficient contrast between text and background.
- **Dark mode (optional):**
  ```toml
  [theme]
  base = "dark"
  primaryColor = "#009688"
  backgroundColor = "#121212"
  secondaryBackgroundColor = "#1E1E1E"
  textColor = "#EEEEEE"
  ```
- **Responsive design:** ensure UI scales well on smaller displays.
- **Brand alignment:** accent color can be adapted to Steute or FlowDesk branding.

---

## 🧠 Final Notes for Developer
- Use **monochrome icons**, apply accent only for active states.
- Prefer **flat design** (no heavy gradients).
- Maintain **ample whitespace** between UI components.
- Keep text **legible and non-distracting**.
- Prioritize a **professional, lightweight look** over decorative elements.

---

**Deliverables for UI Implementation:**
- Custom Streamlit `config.toml` file with defined theme.
- Optional `style.css` overrides (for typography and shadows).
- Preview mockup using 2–3 sample screens (Chat, Tools, Settings).
- Ensure all elements adhere to the monochrome + accent design system.

---

FlowAI — UI Design Direction v1.0
