// Adds a stroke draw-in effect on top of the CSS transform/opacity keyframes
// already applied to each path, so the hexagon segments look like they are
// being traced as they reconstruct, not just fading in.
window.addEventListener('DOMContentLoaded', () => {
  const paths = document.querySelectorAll('.stroke-fragment')
  const baseAnimation = {
    'piece-a': 'assemble-a',
    'piece-b': 'assemble-b',
    'piece-c': 'assemble-c',
  }

  paths.forEach((path, index) => {
    const length = path.getTotalLength()
    path.style.strokeDasharray = String(length)

    const styleSheet = document.styleSheets[0]
    const animationName = `draw-${index}`
    styleSheet.insertRule(
      `@keyframes ${animationName} {
        0% { stroke-dashoffset: ${length}; }
        45% { stroke-dashoffset: 0; }
        55% { stroke-dashoffset: 0; }
        100% { stroke-dashoffset: ${length}; }
      }`,
      styleSheet.cssRules.length,
    )

    const base = baseAnimation[path.id]
    const timing = '3.2s cubic-bezier(0.65, 0, 0.35, 1) infinite'
    path.style.animation = `${base} ${timing}, ${animationName} ${timing}`
  })
})
