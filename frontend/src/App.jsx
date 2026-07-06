import { useState, useEffect, useCallback } from "react";
import { fetchTags, fetchStickers, fetchRandom } from "./api";
import TagSelector from "./components/TagSelector";
import RandomSticker from "./components/RandomSticker";
import StickerGrid from "./components/StickerGrid";
import "./App.css";

const PAGE_SIZE = 50;

export default function App() {
  const [tags, setTags] = useState([]);
  const [selectedTags, setSelectedTags] = useState([]);
  const [mode, setMode] = useState("or");
  const [view, setView] = useState("random"); // "random" | "grid"

  // Random sticker state
  const [randomSticker, setRandomSticker] = useState(undefined);
  const [randomLoading, setRandomLoading] = useState(false);

  // Grid state
  const [stickers, setStickers] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [gridLoading, setGridLoading] = useState(false);

  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTags()
      .then(setTags)
      .catch(() => {});
  }, []);

  const toggleTag = (name) => {
    setSelectedTags((prev) =>
      prev.includes(name) ? prev.filter((t) => t !== name) : [...prev, name]
    );
  };

  const handleRandom = useCallback(async () => {
    setRandomLoading(true);
    setError(null);
    try {
      const s = await fetchRandom({ tags: selectedTags, mode });
      setRandomSticker(s);
    } catch (err) {
      setError(err.message);
    } finally {
      setRandomLoading(false);
    }
  }, [selectedTags, mode]);

  const loadGrid = useCallback(async (reset = true) => {
    setGridLoading(true);
    setError(null);
    const currentOffset = reset ? 0 : offset;
    try {
      const data = await fetchStickers({
        tags: selectedTags,
        mode,
        limit: PAGE_SIZE,
        offset: currentOffset,
      });
      if (reset) {
        setStickers(data.results);
        setOffset(PAGE_SIZE);
      } else {
        setStickers((prev) => [...prev, ...data.results]);
        setOffset((o) => o + PAGE_SIZE);
      }
      setTotal(data.total);
    } catch (err) {
      setError(err.message);
    } finally {
      setGridLoading(false);
    }
  }, [selectedTags, mode, offset]);

  const handleShowGrid = () => {
    setView("grid");
    loadGrid(true);
  };

  const handleLoadMore = () => loadGrid(false);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Sticker Finder</h1>
      </header>

      <section className="controls">
        <TagSelector
          tags={tags}
          selected={selectedTags}
          mode={mode}
          onToggle={toggleTag}
          onModeChange={setMode}
        />
        <div className="action-row">
          <button
            className={`view-btn ${view === "random" ? "active" : ""}`}
            onClick={() => setView("random")}
          >
            Random
          </button>
          <button
            className={`view-btn ${view === "grid" ? "active" : ""}`}
            onClick={handleShowGrid}
          >
            All matches
          </button>
          {selectedTags.length > 0 && (
            <button className="clear-btn" onClick={() => setSelectedTags([])}>
              Clear filters
            </button>
          )}
        </div>
      </section>

      <main className="main-content">
        {error && <p className="error">{error}</p>}
        {view === "random" ? (
          <RandomSticker
            sticker={randomSticker}
            loading={randomLoading}
            onFetch={handleRandom}
          />
        ) : (
          <StickerGrid
            stickers={stickers}
            total={total}
            loading={gridLoading}
            onLoadMore={handleLoadMore}
            hasMore={stickers.length < total}
          />
        )}
      </main>
    </div>
  );
}
