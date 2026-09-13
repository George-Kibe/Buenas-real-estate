import type { Metadata } from "next";

import Footer from "@/components/Footer";
import Header from "@/components/Header";

import "react-toastify/dist/ReactToastify.css";
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: {
    default: "Buenas Real Estate",
    template: "%s · Buenas Real Estate",
  },
  description:
    "Find houses, apartments and commercial property for sale and for rent across Kenya.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-dvh font-sans antialiased">
        <Providers>
          <div className="flex min-h-dvh flex-col">
            <Header />
            <main className="flex-1">{children}</main>
            <Footer />
          </div>
        </Providers>
      </body>
    </html>
  );
}
