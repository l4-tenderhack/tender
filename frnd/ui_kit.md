# UI Kit: Portal Postavshikov (Machine-Readable Reference)

This document describes the core UI components of the Portal to ensure consistency when developing new smart features.

## 1. Design Tokens
Import these via `tokens.css`.

| Variable | Description | Value |
| :--- | :--- | :--- |
| `--portal-red` | Primary Action Color | `#db2b21` |
| `--portal-blue` | Link & Header Color | `#264b82` |
| `--font-family` | Main Font | `Open Sans` |
| `--font-size-base` | Base Text Size | `14px` |

---

## 2. Core Components

### A. Buttons (Кнопки)
- **Primary**: Used for main actions (Publish, Sign).
  - Background: `var(--portal-red)`
  - Text: `#ffffff`
  - Font-weight: `700`
- **Secondary**: Used for auxiliary actions.
  - Border: `1px solid var(--portal-red)`
  - Text: `var(--portal-red)`

### B. Cards (Карточки СТЕ)
- **Container**:
  - Background: `#ffffff`
  - Border: `1px solid var(--border-color)`
  - Radius: `var(--radius-sm)`
- **Hierarchy**:
  - Heading: `var(--portal-blue)`, bold.
  - Price: Large, black, bold.

### C. Status Badges (Статусы)
- **Active (Активная)**:
  - Background: `#ebf5ff`
  - Text: `#0050b3` (Dark blue for contrast)
  - Border: `1px solid #91d5ff`
- **Won (Вы победили)**:
  - Background: `#f6ffed`
  - Text: `#237804` (Dark green for contrast)
  - Border: `1px solid #b7eb8f`
- **Lost (Победил другой поставщик)**:
  - Background: `#fff1f0`
  - Text: `#a8071a` (Dark red for contrast)
  - Border: `1px solid #ffa39e`
- **Closed (Завершена)**:
  - Background: `#f5f5f5`
  - Text: `#595959`
  - Border: `1px solid #d9d9d9`

### D. Quotation Session Card (Карточка котировочной сессии)
- **Timer (Таймер)**:
  - Display: `DD HH MM SS`
  - Typography: Monospace or heavy weight for numbers.
  - Sublabels: Small gray text below numbers.
- **Price Grid (Сетка цен)**:
  - Layout: 3 columns (Initial, Current, Reduction).
  - Reduction: Displayed as `+Amount (Percentage %)`, color: `var(--portal-red)` or `var(--portal-green)` depending on context.
- **Action Buttons**:
  - **Make Bid (Сделать ставку)**: Primary action, `var(--portal-blue)` or `var(--portal-red)`.
  - **Cancel (Отменить)**: Secondary action, gray text or thin border.

### E. Form Inputs (Поля ввода)
- **Default**:
  - Border: `1px solid var(--border-color)`
  - Focus: `1px solid var(--portal-blue)`
  - Placeholder: `#bfbfbf`

---

## 3. Usage Guide
When building a new feature (e.g., "Smart Price Suggestion"):
1.  Wrap the suggestion in a **secondary card** style.
2.  Use `var(--portal-green)` for positive price deviations.
3.  Use the standard **Primary Button** for "Apply Suggested Price".
