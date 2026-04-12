import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'

describe('sanity', () => {
  it('renders a simple element', () => {
    const { getByText } = render(<div>hello</div>)
    expect(getByText('hello')).toBeInTheDocument()
  })
})
