export default function RandomSticker({ sticker, loading, onFetch }) {
  return (
    <div className="random-section">
      <button className="primary-btn" onClick={onFetch} disabled={loading}>
        {loading ? "Loading…" : "Show random sticker"}
      </button>
      {sticker && (
        <div className="random-result">
          <img src={sticker.url} alt={sticker.filename} className="random-img" />
          <div className="sticker-tags">
            {sticker.tags.map((t) => (
              <span key={t} className="chip">{t}</span>
            ))}
          </div>
          <div className="sticker-filename">{sticker.filename}</div>
        </div>
      )}
      {sticker === null && !loading && (
        <p className="empty">No sticker found for the selected filters.</p>
      )}
    </div>
  );
}
