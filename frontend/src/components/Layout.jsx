import { Outlet } from "react-router-dom";
import Navbar from "./Navbar.jsx";
import Footer from "./Footer.jsx";
import BottomNav from "./BottomNav.jsx";
import CookieBanner from "./CookieBanner.jsx";

export default function Layout() {
  return (
    <>
      <Navbar />
      <main className="container">
        <Outlet />
      </main>
      <Footer />
      <BottomNav />
      <CookieBanner />
    </>
  );
}
