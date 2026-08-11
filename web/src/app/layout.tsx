import type { Metadata } from "next";
import Link from "next/link";
import { Geist } from "next/font/google";

import SearchBox from "@/components/SearchBox";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "starchive",
  description: "영화와 책을 한곳에",
};

export default function RootLayout({ children, modal }: LayoutProps<"/">) {
  return (
    <html
      lang="ko"
      className={`${geistSans.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <header className="border-b border-line">
          <nav className="mx-auto grid max-w-6xl grid-cols-[auto_1fr_auto] items-center gap-6 px-4 py-3">
            <div className="flex items-baseline gap-5">
              <Link href="/" className="text-[17px] font-medium">
                starchive
              </Link>
              <Link href="/movies" className="text-sm text-muted">
                영화
              </Link>
              <Link href="/books" className="text-sm text-muted">
                책
              </Link>
            </div>

            <div className="mx-auto w-full max-w-md">
              <SearchBox />
            </div>

            <button
              type="button"
              aria-label="내 계정"
              className="grid h-8 w-8 place-items-center rounded-full bg-fill text-xs text-muted"
            >
              ●
            </button>
          </nav>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">{children}</main>
        {modal}
      </body>
    </html>
  );
}
