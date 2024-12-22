export interface MatrixStyles {
  card: {
    base: string;
    shadow: string;
    border: string;
    hover: string;
  };
  layout: {
    base: string;
    gradient: string;
  };
  text: {
    glow: string;
    fade: string;
  };
  effects: {
    scanline: string;
    flicker: string;
    pulse: string;
  };
}

export const matrixStyles: MatrixStyles; 