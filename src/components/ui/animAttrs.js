// Builds the data-anim-* hook attributes read by the Animation pass
// (see src/motion/README.md). Undefined values are omitted.
export function animAttrs({ anim, delay, duration, stagger, ease, threshold, split } = {}) {
  if (!anim) return {}
  const attrs = { 'data-anim': anim }
  if (delay !== undefined) attrs['data-anim-delay'] = delay
  if (duration !== undefined) attrs['data-anim-duration'] = duration
  if (stagger !== undefined) attrs['data-anim-stagger'] = stagger
  if (ease !== undefined) attrs['data-anim-ease'] = ease
  if (threshold !== undefined) attrs['data-anim-threshold'] = threshold
  if (split !== undefined) attrs['data-anim-split'] = split
  return attrs
}
