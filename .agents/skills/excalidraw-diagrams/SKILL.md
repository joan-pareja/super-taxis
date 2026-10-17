---
name: excalidraw-diagrams
description: Create or edit repository-native .excalidraw diagrams when layout, visual semantics, movable connectors, or file integrity matter.
---

# Excalidraw diagrams

Edit the local `.excalidraw` file directly; no MCP is required. Inspect the current scene and its owning document first. Re-read before writing so editor changes are not overwritten.

## Compose

- Tell one clear story with visible grouping and reading order. Prefer short labels; keep explanation in the document.
- Size and space elements from their content. Leave room for labels and routes; never allow overflow, overlap, or text to hide a connector.
- Use Comic Shanns (`fontFamily: 8`) for all text.
- Bind shape and arrow labels natively and center them. Keep only titles, section headings, annotations, and legends standalone.
- Use a restrained palette with stable meaning. Do not give every object a different colour. Distinguish states or flow types consistently and add a small legend only when needed.
- Use straight two-point arrows for direct links and elbowed arrows with few bends for routing. Keep arrow labels brief.
- Bind every arrow at both ends. Add the matching arrow backlink to each endpoint's `boundElements`; visual contact is not a connection.

## Finish

1. Run `python .agents/skills/excalidraw-diagrams/scripts/validate_excalidraw.py <file>` and fix every error.
2. Preview the scene. Check hierarchy, colour meaning, text fit, crossings, hidden arrows, and whitespace at normal zoom.
3. Update derived SVG or PNG files only when the owning document uses them.

Preserve untouched IDs and elements. Make the smallest coherent edit.
