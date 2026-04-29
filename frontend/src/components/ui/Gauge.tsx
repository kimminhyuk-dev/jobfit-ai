interface GaugeProps {
  score: number;
  size?: number;
  stroke?: number;
  label?: string;
  // Modern 팔레트 기준 색상
  successColor?: string;
  primaryColor?: string;
  warnColor?: string;
  borderColor?: string;
  textColor?: string;
  subtleColor?: string;
}

export default function Gauge({
  score,
  size = 120,
  stroke = 10,
  label = '매칭 점수',
  successColor = '#15803d',
  primaryColor = '#1d4ed8',
  warnColor = '#b45309',
  borderColor = '#eaeaea',
  textColor = '#0a0a0a',
  subtleColor = '#a3a3a3',
}: GaugeProps) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = score / 100;
  const color = score >= 85 ? successColor : score >= 70 ? primaryColor : warnColor;

  return (
    <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={borderColor} strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${c * pct} ${c}`}
          style={{ transition: 'stroke-dasharray .8s cubic-bezier(.2,.7,.3,1)' }}
        />
      </svg>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            fontSize: size * 0.28,
            fontWeight: 700,
            color: textColor,
            letterSpacing: '-.02em',
            fontFamily: 'Inter, sans-serif',
            lineHeight: 1,
          }}
        >
          {score}
        </div>
        {label && (
          <div style={{ fontSize: 11, color: subtleColor, marginTop: 3, letterSpacing: '.01em' }}>{label}</div>
        )}
      </div>
    </div>
  );
}
