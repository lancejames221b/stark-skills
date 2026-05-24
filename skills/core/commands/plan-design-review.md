---
description: Design review for frontend work — evaluate visual design, UX, accessibility, and aesthetics. Use when reviewing UI/UX or building new frontend screens
argument-hint: "[components | pages | screens | dashboard]"
---
## Design Review

When reviewing or building frontend work, apply these standards:

### Visual Design
- **Typography**: Distinctive fonts (not Inter/Roboto/system). Pair display + body font.
- **Color**: Cohesive palette with dominant colors and sharp accents. No purple gradients on white.
- **Spacing**: Consistent spacing scale (4px base). Generous negative space.
- **Hierarchy**: Clear visual hierarchy — title > section > body > caption.

### UX
- **User goals**: Does every element serve a user goal? Remove decorative noise.
- **Navigation**: Can users get from A to B in ≤ 3 clicks?
- **Feedback**: Do actions have visible results (loading, success, error)?
- **Progressive disclosure**: Show only what's needed now. Advanced options hidden behind "More".

### Accessibility
- Color contrast ≥ 4.5:1 for normal text, ≥ 3:1 for large text
- All interactive elements focus-visible
- Alt text on images
- Semantic HTML (nav, main, article, aside)
- Keyboard navigation (tab order, focus trap for modals)

### Responsive Design
- Mobile-first breakpoints (sm: 640px, md: 768px, lg: 1024px)
- Touch targets ≥ 44px on mobile
- Content reflows gracefully at all widths

### Code Quality
- No inline styles (use CSS classes or Tailwind)
- Component extraction for reusable patterns
- Proper prop types / interface definitions
- Loading states for all async data
