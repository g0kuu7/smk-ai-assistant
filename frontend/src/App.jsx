import Navbar from "./components/Navbar";
import HeroBanner from "./components/HeroBanner";
import InfoSection from "./components/InfoSection";
import CTASection from "./components/CTASection";
import Footer from "./components/Footer";
import AssistantWidget from "./components/AssistantWidget";
import "./styles/main.css";

function App() {
  return (
    <div className="smk-page">
      <Navbar />
      <HeroBanner />
      <InfoSection />
      <CTASection />
      <Footer />
      <AssistantWidget />
    </div>
  );
}

export default App;