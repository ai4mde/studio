import React from 'react'

type WrapMarkerProps = {
    id: string
    children: React.ReactNode
}

const WrapMarker: React.FC<WrapMarkerProps> = ({
    id,
    children,
}: WrapMarkerProps) => {
    return (
        <marker
            id={id}
            viewBox="0 0 16 16"
            markerHeight={16}
            markerWidth={16}
            refX={16}
            refY={8}
            orient="auto-start-reverse"
        >
            {children}
        </marker>
    )
}

const Markers: React.FC = () => {
    return (
        <>
            <svg style={{ position: 'absolute', top: 0, left: 0 }}>
                <defs>
                    <WrapMarker id="activity-end">
                        <svg width={16} height={16} viewBox="0 0 16 16">
                            <path
                                d="M 1, 1 L 16, 8 L 1, 16"
                                stroke="black"
                                fill="none"
                            />
                        </svg>
                    </WrapMarker>
                    <WrapMarker id="generalization-end">
                        <svg width={16} height={16} viewBox="0 0 16 16">
                            <path
                                d="M 1, 16 L 1, 1 L 16, 8 L 1, 16 Z"
                                stroke="black"
                                fill="white"
                            />
                        </svg>
                    </WrapMarker>
                    <WrapMarker id="inclusion-end">
                        <svg width={16} height={16} viewBox="0 0 16 16">
                            <path //"M0,0 L0,6 L9,3 z"
                                d="M 16, 8 L 8, 1 L 16, 8 L 8, 16 Z"
                                stroke="black"
                                fill="white"
                            />
                        </svg>
                    </WrapMarker>
                    <WrapMarker id="extension-end">
                        <svg width={16} height={16} viewBox="0 0 16 16">
                            <path //"M0,0 L0,6 L9,3 z"
                                d="M 16, 8 L 8, 1 L 16, 8 L 8, 16 Z"
                                stroke="black"
                                fill="white"
                            />
                        </svg>
                    </WrapMarker>
                    <WrapMarker id="association-end">
                        <></>
                    </WrapMarker>
                    <WrapMarker id="composition-start">
                        <svg width={16} height={16} viewBox="0 0 16 16">
                            <rect
                                xmlns="http://www.w3.org/2000/svg"
                                x="8"
                                width="11.3137"
                                height="11.3137"
                                transform="rotate(45 8 0)"
                                fill="black"
                            />
                        </svg>
                    </WrapMarker>
                    <WrapMarker id="edge-end">
                        <svg width={16} height={16} viewBox="0 0 16 16">
                            <path
                                d="M 1, 16 L 16,8 L 1, 1"
                                stroke="black"
                                fill="none"
                            />
                        </svg>
                    </WrapMarker>
                </defs>
            </svg>
        </>
    )
}

export default Markers
