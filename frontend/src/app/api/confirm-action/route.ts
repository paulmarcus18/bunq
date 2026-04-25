import { NextResponse } from "next/server";

const BACKEND_URL = process.env.FINPILOT_BACKEND_URL ?? "http://127.0.0.1:8000";

export async function POST(request: Request) {
  const body = await request.text();
  const response = await fetch(`${BACKEND_URL}/confirm-action`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body,
    cache: "no-store",
  });

  const responseBody = await response.text();
  return new NextResponse(responseBody, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("content-type") ?? "application/json",
    },
  });
}
