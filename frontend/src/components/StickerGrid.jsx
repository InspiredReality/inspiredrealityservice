export default function StickerGrid({ stickers, total, loading, onLoadMore, hasMore }) {
  if (loading && stickers.length === 0) return <p className="loading">Loading…</p>;
  if (!loading && stickers.length === 0) return <p className="empty">No stickers match the selected filters.</p>;

  return (
    <div className="grid-section">
      <p className="result-count">{total} result{total !== 1 ? "s" : ""}</p>
      <div className="sticker-grid">
        {stickers.map((s) => (
          <div key={s.id} className="sticker-card">
            <div className="img-wrap">
              <img src={s.url} alt={s.filename} loading="lazy" />
            </div>
            <div className="sticker-tags">
              {s.tags.map((t) => (
                <span key={t} className="chip">{t}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
      {hasMore && (
        <button className="load-more-btn" onClick={onLoadMore} disabled={loading}>
          {loading ? "Loading…" : "Load more"}
        </button>
      )}
    </div>
  );
}
