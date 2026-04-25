function CTASection() {
  return (
    <section className="cta-section">
      <div className="cta-section__container">
        <div className="cta-section__content">
          <p className="cta-section__eyebrow">Virtualus pagalbininkas</p>
          <h2 className="cta-section__title">Išbandyk, kaip AI widgetas veiktų SMK svetainėje</h2>
          <p className="cta-section__text">
            Paspausk AI mygtuką apačioje dešinėje. Tai demonstracinė sąsaja, skirta
            parodyti idėją: vartotojas lieka SMK puslapyje, bet klausimus užduoda
            greitam virtualiam asistentui.
          </p>
        </div>

        <div className="cta-section__side">
          <div className="cta-section__hint">
            <span>Demo scenarijus</span>
            <strong>„Kiek kainuoja Programavimas ir multimedija?“</strong>
          </div>
        </div>
      </div>
    </section>
  );
}

export default CTASection;
