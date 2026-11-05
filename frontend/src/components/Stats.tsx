// Small line with generation time and token count.

interface Props {
  tokens: number | null;
  elapsedTime: number | null;
}

export function Stats({ tokens, elapsedTime }: Props) {
  if (tokens === null && elapsedTime === null) return null;
  return (
    <div className="stats">
      {elapsedTime !== null && <span>⏱ {elapsedTime.toFixed(2)} s</span>}
      {tokens !== null && <span># {tokens} tokens</span>}
    </div>
  );
}
