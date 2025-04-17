import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const search = async () => {
    const res = await fetch(`/api/search?title=${encodeURIComponent(query)}`);
    const data = await res.json();
    setResults(data);
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Search Manga</h2>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      <button onClick={search}>Search</button>
      <ul>
        {results.map(m => (
          <li key={m.id}>
            <Link to={`/manga/${m.id}`}>{m.title}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function MangaPage() {
  const id = window.location.pathname.split("/").pop();
  const [chapters, setChapters] = useState([]);

  React.useEffect(() => {
    fetch(`/api/chapters/${id}`)
      .then(res => res.json())
      .then(setChapters);
  }, [id]);

  return (
    <div style={{ padding: 20 }}>
      <h2>Chapters</h2>
      <ul>
        {chapters.map(c => (
          <li key={c.id}>
            <Link to={`/reader/${id}/${c.id}`}>Chapter {c.chapter}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Reader() {
  const [images, setImages] = useState([]);
  const chapterId = window.location.pathname.split("/").pop();

  React.useEffect(() => {
    fetch(`/api/pages/${chapterId}`)
      .then(res => res.json())
      .then(setImages);
  }, [chapterId]);

  return (
    <div style={{ padding: 20 }}>
      {images.map((img, i) => (
        <img key={i} src={img} style={{ width: '100%', marginBottom: '10px' }} loading="lazy" />
      ))}
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <nav style={{ padding: 10, backgroundColor: '#222' }}>
        <Link to="/" style={{ color: 'white', marginRight: 10 }}>Home</Link>
        <Link to="/search" style={{ color: 'white' }}>Search</Link>
      </nav>
      <Routes>
        <Route path="/" element={<div style={{ padding: 20 }}>Welcome to the Manga Reader</div>} />
        <Route path="/search" element={<Search />} />
        <Route path="/manga/:id" element={<MangaPage />} />
        <Route path="/reader/:mangaId/:chapterId" element={<Reader />} />
      </Routes>
    </Router>
  );
}
