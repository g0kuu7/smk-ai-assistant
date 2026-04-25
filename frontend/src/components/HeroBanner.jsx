function HeroBanner() {
  return (
    <section className="hero-banner">
      <div className="hero-banner__container">
        <div className="hero-banner__copy">
          <p className="hero-banner__eyebrow">SMK Aukštoji mokykla</p>

          <h1 className="hero-banner__title">
            Studijos, kurios
            <span> įkvepia augti</span>
          </h1>

          <p className="hero-banner__text">
            Atrask savo kelią tarp idėjų, žmonių ir galimybių. Šiame demo puslapyje
            gali pamatyti, kaip SMK svetainėje atrodytų virtualus AI asistentas,
            padedantis rasti informaciją apie studijas, priėmimą ir studentų sistemas.
          </p>

          <div className="hero-banner__actions">
            <a
              className="hero-banner__button hero-banner__button--primary"
              href="https://smk.lt/studiju-programos/"
              target="_blank"
              rel="noreferrer"
            >
              Rinktis studijas
            </a>

            <a
              className="hero-banner__button hero-banner__button--secondary"
              href="https://smk.lt/priemimas/"
              target="_blank"
              rel="noreferrer"
            >
              Priėmimo informacija
            </a>
          </div>
        </div>

        <div className="hero-banner__visual" aria-label="SMK stiliaus vizualas">
          <div className="hero-banner__image-card">
            <img
              src="https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1200&q=85"
              alt="Studentai universiteto aplinkoje"
            />
          </div>

          <div className="hero-banner__shape hero-banner__shape--yellow"></div>
          <div className="hero-banner__shape hero-banner__shape--blue"></div>

          <div className="hero-banner__floating-card">
            <span>AI asistentas</span>
            <strong>Greiti atsakymai apie SMK</strong>
          </div>
        </div>
      </div>
    </section>
  );
}

export default HeroBanner;
