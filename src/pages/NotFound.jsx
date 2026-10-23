import { useEffect } from 'react'
import Layout from '../components/layout/Layout.jsx'

// Stock Next.js 12 `_error` body inside the shared app shell (specs/404.md).
// It deliberately uses the system font stack, not SuisseIntl.
export default function NotFound() {
  useEffect(() => {
    const prev = document.title
    document.title = '404: This page could not be found'
    document.body.classList.add('is-error-page')
    return () => {
      document.title = prev
      document.body.classList.remove('is-error-page')
    }
  }, [])

  return (
    // No main background: the body (#fff, position fixed) is then the only
    // backdrop, which sits outside the header's blend group, so the
    // mix-blend-difference header stays near-white like the source _error page.
    <Layout className="relative" showFooter={false} showProgress={false}>
      <div className="error-page">
        <div>
          <h1 className="error-page__h1">404</h1>
          <div className="error-page__msg">
            <h2>This page could not be found.</h2>
          </div>
        </div>
      </div>
    </Layout>
  )
}
