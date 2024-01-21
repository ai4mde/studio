import { atom } from 'jotai'
import { createRef } from 'react'

export const navigationPortalAtom = atom(
    createRef<HTMLDivElement>() as React.MutableRefObject<HTMLDivElement>
)
