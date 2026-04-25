function Header({ onClearChat }) {
  return (
    <header className="header">
      <div>
        <div className="header__logo">SMK AI Assistant</div>
        <div className="header__subtitle">
          Virtualus asistentas pagal SMK informaciją
        </div>
      </div>

      <button className="header__clear-button" onClick={onClearChat}>
        Išvalyti pokalbį
      </button>
    </header>
  );
}

export default Header;