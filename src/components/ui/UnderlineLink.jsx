/**
 * Link with a 1px currentColor underline that collapses on hover
 * (spec §5 "Email links": scaleX 1 → 0, origin right, .5s cubic-bezier(1,0,.29,1)).
 *
 * Props: href, children, className, as (default 'a'), ...rest
 */
export default function UnderlineLink({ href, children, className = '', as: Tag = 'a', ...rest }) {
  return (
    // Inline (not inline-block) like the source Button_hover-underline: the
    // bar sits on the bottom of the inline content area (font box), 2.5px
    // below the 12px line box at 1440.
    <Tag href={href} className={`hover-underline relative inline ${className}`} {...rest}>
      {children}
      <span className="underline-bar absolute bottom-0 left-0 block h-px w-full overflow-hidden" />
    </Tag>
  )
}
