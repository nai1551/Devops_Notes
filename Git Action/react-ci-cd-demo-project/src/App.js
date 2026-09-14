import logo from "./logo.svg";
import "./App.css";

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          Welcome to <code>Marwiz</code> from CI / CD
        </p>
        <a
          className="App-link"
          href="https://marwiz.in/"
          target="_blank"
          rel="noopener noreferrer"
        >
          visit our website
        </a>
      </header>
    </div>
  );
}

export default App;
