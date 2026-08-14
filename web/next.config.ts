import type { NextConfig } from "next";

/** 서버에서만 읽는다. 브라우저는 항상 /api 로 간다 */
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "image.tmdb.org" },
      { protocol: "https", hostname: "image.aladin.co.kr" },
    ],
  },

  // 백엔드를 같은 출처로 묶는다. 그래야 쿠키가 이 도메인에 저장되고
  // 서버 컴포넌트가 cookies() 로 읽을 수 있다
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND_ORIGIN}/:path*` }];
  },
};

export default nextConfig;
