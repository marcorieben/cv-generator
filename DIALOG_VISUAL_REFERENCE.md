# Modern Dialog Visual Reference

## Dialog Structure

All dialogs follow this consistent layout:

```
┌─────────────────────────────────────────────────────┐
│  [ICON] Dialog Title                    (COLORED)   │ ← Header Bar (60px height)
├─────────────────────────────────────────────────────┤
│                                                     │
│  Main message text goes here...                    │ ← Content Area (white bg)
│  Professional, concise, actionable                 │    30px padding
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ Optional Details Section                      │ │ ← Details Box
│  │ • Bullet points                               │ │   (light gray bg)
│  │ • File paths                                  │ │   15px padding
│  │ • Technical information                       │ │   Scrollable
│  └───────────────────────────────────────────────┘ │
│                                                     │
│              [Button 1]  [Button 2]                │ ← Button Area
│                                                     │    20px bottom padding
└─────────────────────────────────────────────────────┘
   550-600px width          250-400px height
```

## Color Scheme by Dialog Type

### Success Dialog
```
Header:  #28A745 (Green) + ✅
Primary: #FF7900 (Orange) - "OK" button
Background: #FFFFFF (White)
Details: #F8F9FA (Light Gray)
```

### Error Dialog
```
Header:  #DC3545 (Red) + ❌
Primary: #444444 (Gray) - "Schließen" button
Background: #FFFFFF (White)
Details: #F8F9FA (Light Gray) - Scrollable
```

### Warning Dialog
```
Header:  #FFC107 (Yellow) + ⚠️
Primary: #FF7900 (Orange) - "Ja, fortfahren" button
Secondary: #444444 (Gray) - "Abbrechen" button
Background: #FFFFFF (White)
Details: #F8F9FA (Light Gray) - Scrollable
```

### Confirmation Dialog
```
Header:  #FF7900 (Orange) + ❓/ℹ️/✅
Primary: #FF7900 (Orange) - "Ja" button
Secondary: #444444 (Gray) - "Nein" button
Background: #FFFFFF (White)
```

## Typography Scale

```
Header Text:     14pt Segoe UI Bold, White
Content Text:    11pt Segoe UI Regular, #444444
Details Text:     9pt Segoe UI/Consolas Regular, #444444
Button Text:     10pt Segoe UI Bold, White
```

## Spacing & Dimensions

```
Window Width:    550-600px (consistent across types)
Window Height:   250-400px (varies by content)

Header Height:   60px fixed
Content Padding: 30px horizontal, 20px vertical
Button Padding:  10px vertical, 15px horizontal (width)
Button Spacing:  20px bottom margin, 5px between buttons

Details Box:
  - Padding: 15px all sides
  - Max Height: ~200px (scrollable)
  - Border Radius: 0 (flat design)
  - Border: None
```

## Icons Reference

All icons are Unicode characters, no image files needed:

```
✅  U+2705  Success, completion, OK
❌  U+274C  Error, critical failure, blocking
⚠️  U+26A0  Warning, caution, non-blocking
ℹ️  U+2139  Information, notice
❓  U+2753  Question, confirmation needed
📄  U+1F4C4  File, PDF document
📋  U+1F4CB  JSON, clipboard, data
📝  U+1F4DD  Word document, editing
```

## Button States

### Default State
```
Orange Button:   bg=#FF7900, fg=#FFFFFF, cursor=hand2
Gray Button:     bg=#444444, fg=#FFFFFF, cursor=hand2
Border:          0px (flat design)
Relief:          flat
Padding:         10px vertical
```

### Hover State (on mouse enter)
```
Orange Button:   bg=#E66D00 (90% brightness)
Gray Button:     bg=#3A3A3A (90% brightness)
Transition:      Immediate color change
```

### Layout
```
Buttons are always:
- Fixed width (12-18 characters)
- Bottom-aligned in dialog
- Horizontally centered
- 5px spacing between multiple buttons
- Primary action on left, secondary on right
```

## Alignment & Positioning

```
Window:
  - Center of screen (tk::PlaceWindow . center)
  - Always on top (attributes -topmost True)
  - Not resizable
  - Focus forced on open

Content:
  - Left-aligned text (justify=left)
  - Word-wrap enabled (wraplength=480-540px)
  - Anchor west for labels

Buttons:
  - Horizontally centered in button frame
  - Consistent width across dialog types
```

## Example: Success Dialog Breakdown

```
┌─────────────────────────────────────────────────────┐
│ ✅  Erfolg                          #28A745         │ 60px
├─────────────────────────────────────────────────────┤
│                                     30px padding    │
│  Der Lebenslauf wurde erfolgreich                  │ 11pt
│  generiert und ist bereit zur                      │ Segoe UI
│  Verwendung.                                       │ #444444
│                                     15px spacing    │
│  ┌───────────────────────────────────────────────┐ │
│  │ 📄 PDF Input:                  #F8F9FA 15px   │ │ 9pt
│  │   Marco_Rieben_CV.pdf                         │ │ Segoe UI
│  │                                                │ │ #444444
│  │ 📋 JSON gespeichert:                          │ │
│  │   input/json/Marco_...json                    │ │
│  │                                                │ │
│  │ 📝 Word Dokument:                             │ │
│  │   output/word/Marco_...docx                   │ │
│  └───────────────────────────────────────────────┘ │
│                                     20px spacing    │
│                   [     OK     ]    #FF7900        │ 10pt Bold
│                    150px width      White          │
└─────────────────────────────────────────────────────┘
  600px                              380px
```

## Responsive Behavior

```
Text Wrapping:
  - Automatic word wrap at 480-540px
  - No horizontal scrolling
  - Vertical expansion if needed (up to max height)

Scrolling:
  - Only in details boxes
  - Appears automatically when content > 200px
  - Windows-style scrollbar
  - Smooth scrolling

Window Sizing:
  - Fixed width per dialog type
  - Height adjusts for content (within limits)
  - No user resizing allowed
  - Maintains aspect ratio
```

## Accessibility Features

```
✓ High contrast colors (WCAG AA compliant)
✓ Large, readable fonts (11pt minimum)
✓ Clear visual hierarchy
✓ Keyboard navigation support (Tab, Enter, Escape)
✓ Icons supplement text (not replace)
✓ Consistent button positions
✓ Focus indicators on buttons
✓ Always-on-top for visibility
```

## Technical Implementation

Each dialog is implemented as a class inheriting from `ModernDialog`:

```python
class ModernDialog:
    # Base class with:
    # - Color constants
    # - Icon constants  
    # - Window setup
    # - Header creation
    # - Content frame creation
    # - Button creation with hover
    # - Color darkening for hover effects

class SuccessDialog(ModernDialog):
    # Implements success-specific:
    # - Green header
    # - Success icon
    # - Details box (optional)
    # - Orange OK button

class ErrorDialog(ModernDialog):
    # Implements error-specific:
    # - Red header
    # - Error icon
    # - Scrollable details with monospace
    # - Gray close button

# etc...
```

All dialogs return a result and are blocking (modal behavior).
