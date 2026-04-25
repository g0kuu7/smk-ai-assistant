function InfoSection() {
  const programmes = [
    "Kūryba ir komunikacija",
    "Verslas ir vadyba",
    "Programavimas ir multimedija",
    "Teisė ir viešasis saugumas",
  ];

  return (
    <section className="info-section">
      <div className="info-section__container">
        <div className="section-heading">
          <p className="section-heading__eyebrow">Studijos SMK</p>
          <h2 className="section-heading__title">Rask programą, kuri tinka tavo ateičiai</h2>
          <p className="section-heading__text">
            Puslapis sukurtas kaip realistiškas pristatymo prototipas: lankytojas mato
            SMK stiliaus informacinę svetainę ir iš karto gali išbandyti AI widgetą.
          </p>
        </div>

        <div className="info-section__grid">
          <article className="info-card info-card--large">
            <div className="info-card__label">Populiarios kryptys</div>
            <h3 className="info-card__title">Studijų programos</h3>
            <p className="info-card__text">
              AI asistentas gali padėti greitai susigaudyti, kur ieškoti informacijos
              apie programas, kainas, miestus ir priėmimo procesą.
            </p>

            <div className="info-card__tags">
              {programmes.map((programme) => (
                <span key={programme}>{programme}</span>
              ))}
            </div>
          </article>

          <article className="info-card info-card--dark">
            <div className="info-card__label">Priėmimas</div>
            <h3 className="info-card__title">Įstok paprasčiau</h3>
            <p className="info-card__text">
              Klausimai apie dokumentus, terminus, konsultacijas ar registraciją gali
              būti nukreipti į AI asistentą.
            </p>
          </article>

          <article className="info-card info-card--accent">
            <div className="info-card__label">Studentams</div>
            <h3 className="info-card__title">Moodle, Classter ir kitos sistemos</h3>
            <p className="info-card__text">
              Demo parodo, kaip studentai galėtų gauti greitus atsakymus nesiblaškydami
              tarp skirtingų puslapių.
            </p>
          </article>
        </div>
      </div>
    </section>
  );
}

export default InfoSection;
