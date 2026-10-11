import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Sparkline } from '@/components/Sparkline'

describe('Sparkline', () => {
  it('trace une ligne à partir de deux valeurs', () => {
    const { container } = render(<Sparkline values={[1, 3]} label="Tendance" />)
    const svg = screen.getByRole('img', { name: 'Tendance' })
    expect(svg).toBeInTheDocument()
    const polyline = container.querySelector('polyline')
    expect(polyline).not.toBeNull()
    expect(polyline?.getAttribute('points')).toBe('2.00,26.00 98.00,2.00')
  })

  it("n'affiche rien avec moins de deux points", () => {
    const { container } = render(<Sparkline values={[5]} label="Tendance" />)
    expect(container).toBeEmptyDOMElement()
  })

  it('gère une série constante sans division par zéro', () => {
    const { container } = render(<Sparkline values={[4, 4, 4]} label="Plate" />)
    const points = container.querySelector('polyline')?.getAttribute('points') ?? ''
    expect(points).not.toContain('NaN')
    const ys = points.split(' ').map((pair) => Number(pair.split(',')[1]))
    expect(new Set(ys).size).toBe(1)
  })

  it('place le maximum en haut et le minimum en bas', () => {
    const { container } = render(<Sparkline values={[10, 0]} label="Descend" />)
    const points = container.querySelector('polyline')?.getAttribute('points') ?? ''
    const ys = points.split(' ').map((pair) => Number(pair.split(',')[1]))
    expect(ys[0]).toBeLessThan(ys[1])
  })
})
