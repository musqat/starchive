import type { Metadata } from "next";
import Link from "next/link";
import { Geist } from "next/font/google";

import SearchBox from "@/components/SearchBox";
import UserMenu from "@/components/UserMenu";
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
          <nav className="mx-auto grid max-w-6xl grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 px-4 py-3 sm:gap-6">
            {/* 좁은 화면에서 링크가 글자 단위로 쪼개지지 않게 nowrap */}
            <div className="flex items-baseline gap-3 whitespace-nowrap sm:gap-5">
              <Link href="/" className="text-[17px] font-medium">
                starchive
              </Link>
              {/* 홈의 전체 보기로도 닿아서 좁은 화면에서는 접는다 */}
              <Link href="/movies" className="hidden text-sm text-muted sm:block">
                영화
              </Link>
              <Link href="/books" className="hidden text-sm text-muted sm:block">
                책
              </Link>
              <Link href="/recommendations" className="text-sm text-muted">
                추천
              </Link>
            </div>

            <div className="mx-auto w-full max-w-md">
              <SearchBox />
            </div>

            <UserMenu />
          </nav>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">{children}</main>
        {modal}
      </body>
    </html>
  );
}
