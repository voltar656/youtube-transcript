import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

async function proxyRequest(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const backendPath = path.join("/");
  const url = new URL(backendPath, BACKEND_URL);
  url.search = request.nextUrl.search;

  const headers = new Headers(request.headers);
  headers.delete("host");
  // Prevent the backend from gzip-encoding responses. Node.js fetch (undici)
  // auto-decompresses gzip bodies per the Fetch spec, which leaves the
  // Content-Encoding: gzip header intact but the body already decoded — the
  // browser then tries to decompress plain JSON and fails with an HTTP/2
  // INTERNAL_ERROR. Stripping Accept-Encoding ensures the backend returns a
  // plain response whose headers and body stay in sync.
  headers.delete("accept-encoding");

  const init: RequestInit = {
    method: request.method,
    headers,
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.arrayBuffer();
  }

  try {
    const upstream = await fetch(url.toString(), init);

    const responseHeaders = new Headers(upstream.headers);
    // Remove headers that Next.js/Node handle themselves or that would be
    // incorrect if the body was transparently decompressed by undici.
    responseHeaders.delete("transfer-encoding");
    responseHeaders.delete("content-encoding");
    responseHeaders.delete("content-length");

    return new NextResponse(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    });
  } catch {
    return NextResponse.json(
      { error: "BadGateway", message: "Backend unavailable" },
      { status: 502 }
    );
  }
}

export const GET = proxyRequest;
export const POST = proxyRequest;
