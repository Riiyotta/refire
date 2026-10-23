import { Fragment, forwardRef } from 'react'
import { animAttrs } from './animAttrs.js'

/**
 * Split-text heading/paragraph (spec §4.2). Renders the final, visible state;
 * the Animation agent tweens `.split-inner` (yPercent 100 → 0, or opacity for
 * splitFade) using the data-anim-* hooks on the root.
 *
 * Structure per unit:
 *   .split-root > .split-word > .split-el (inline-flex, overflow hidden) > .split-inner
 * Words are separated by real spaces so lines wrap naturally.
 *
 * Props:
 *  - text       string (required)
 *  - type       'words' | 'chars'   (unit to wrap; default 'words')
 *  - as         element tag (default 'div')
 *  - className  extra classes on the root
 *  - anim       data-anim value (default 'split'); pass null to omit the hook
 *  - delay, duration, stagger, ease, threshold   → data-anim-* attributes
 */
const SplitText = forwardRef(function SplitText({
  text,
  type = 'words',
  as: Tag = 'div',
  className = '',
  anim = 'split',
  delay,
  duration,
  stagger,
  ease,
  threshold,
  ...rest
}, ref) {
  const words = text.split(' ')
  return (
    <Tag
      ref={ref}
      className={`split-root ${className}`}
      aria-label={text}
      {...animAttrs({ anim, delay, duration, stagger, ease, threshold, split: type })}
      {...rest}
    >
      {words.map((word, i) => (
        <Fragment key={i}>
          {i > 0 && ' '}
          <span className="split-word" aria-hidden="true">
            {type === 'chars' ? (
              [...word].map((ch, j) => (
                <span className="split-el" key={j}>
                  <span className="split-inner">{ch}</span>
                </span>
              ))
            ) : (
              <span className="split-el">
                <span className="split-inner">{word}</span>
              </span>
            )}
          </span>
        </Fragment>
      ))}
    </Tag>
  )
})

export default SplitText
