/**
 * Pill button with sliding-circle hover (spec §2.6 Submit / BlackButton).
 * Hover: #383838 circle slides up (.6s) while the label slides out rotated and
 * a primary-coloured duplicate slides in (.6s cubic-bezier(.36,.28,0,.99)).
 *
 * Props:
 *  - children    label (rendered uppercase)
 *  - type        button type (default 'button')
 *  - bgClass     resting fill (default 'bg-primary')
 *  - textClass   resting label colour (default 'text-dark')
 *  - className, ...rest
 */
export default function BlackButton({
  children,
  type = 'button',
  bgClass = 'bg-primary',
  textClass = 'text-dark',
  className = '',
  ...rest
}) {
  return (
    <button
      type={type}
      className={`black-btn relative flex items-center justify-center rounded-f100 px-f45 py-f17 text-f16 leading-f24 tracking-[.15em] ${textClass} tablet:rounded-f148 tablet:px-f32 tablet:py-f7 tablet:tracking-normal mobile:rounded-f100 mobile:px-f20 mobile:py-f7 mobile:text-fmin12 mobile:tracking-[.15em] ${className}`}
      {...rest}
    >
      <span className={`black-btn-bg ${bgClass}`} data-anim="black-btn-bg" />
      <span className="black-btn-bg black-btn-hidden-bg bg-most-dark" />
      <span className="relative overflow-hidden">
        <span className="black-btn-text block">
          <span className="block uppercase" data-anim="black-btn-label">
            {children}
          </span>
        </span>
        <span className="black-btn-hidden-text absolute left-0 top-0 block uppercase text-primary">{children}</span>
      </span>
    </button>
  )
}
