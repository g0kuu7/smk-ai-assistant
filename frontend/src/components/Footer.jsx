function Footer() {
  return (
    <footer className="smk-footer">
      <div className="smk-footer__container">
        <div>
          <div className="smk-footer__logo">SMK</div>
          <p className="smk-footer__text">
            Demonstracinis puslapis, skirtas parodyti, kaip AI asistentas galėtų
            papildyti SMK informacinę svetainę.
          </p>
        </div>

        <div className="smk-footer__links">
          <a href="https://smk.lt/" target="_blank" rel="noreferrer">
            smk.lt
          </a>
          <a href="https://smk.lt/studiju-programos/" target="_blank" rel="noreferrer">
            Studijos
          </a>
          <a href="https://smk.lt/priemimas/" target="_blank" rel="noreferrer">
            Priėmimas
          </a>
          <a href="https://smk.lt/kontaktai/" target="_blank" rel="noreferrer">
            Kontaktai
          </a>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
