export default function TagSelector({ tags, selected, mode, onToggle, onModeChange }) {
  return (
    <div className="tag-selector">
      <div className="mode-toggle">
        <label>
          <input
            type="radio"
            value="or"
            checked={mode === "or"}
            onChange={() => onModeChange("or")}
          />
          Any tag (OR)
        </label>
        <label>
          <input
            type="radio"
            value="and"
            checked={mode === "and"}
            onChange={() => onModeChange("and")}
          />
          All tags (AND)
        </label>
      </div>
      <div className="tag-list">
        {tags.map((t) => (
          <button
            key={t.name}
            className={`tag-btn ${selected.includes(t.name) ? "active" : ""}`}
            onClick={() => onToggle(t.name)}
          >
            {t.name}
            <span className="tag-count">{t.count}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
