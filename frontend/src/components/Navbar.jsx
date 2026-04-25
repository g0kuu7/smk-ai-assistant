function Navbar() {
  const navItems = [
    { label: "Studijos", href: "https://smk.lt/studiju-programos/" },
    { label: "Priėmimas", href: "https://smk.lt/priemimas/" },
    { label: "#smklife", href: "https://smk.lt/smklife/" },
    { label: "Studentams", href: "https://smk.lt/studentams/" },
    { label: "Kontaktai", href: "https://smk.lt/kontaktai/" },
  ];

  return (
    <header className="smk-navbar">
      <div className="smk-navbar__container">
        <a className="smk-navbar__logo" href="https://smk.lt/" target="_blank" rel="noreferrer">
          SMK
        </a>

        <nav className="smk-navbar__nav" aria-label="Pagrindinė navigacija">
          {navItems.map((item) => (
            <a key={item.label} href={item.href} target="_blank" rel="noreferrer">
              {item.label}
            </a>
          ))}
        </nav>

        <a
          className="smk-navbar__apply"
          href="https://smk.lt/priemimas/"
          target="_blank"
          rel="noreferrer"
        >
          Teikti paraišką
        </a>
      </div>
    </header>
  );
}

export default Navbar;
