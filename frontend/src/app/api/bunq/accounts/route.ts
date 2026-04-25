import { NextResponse } from "next/server";

const BACKEND_URL = process.env.FINPILOT_BACKEND_URL ?? "http://127.0.0.1:8000";

export async function GET() {
  const response = await fetch(`${BACKEND_URL}/bunq/accounts`, {
    cache: "no-store",
  });

  const body = await response.text();
  return new NextResponse(body, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("content-type") ?? "application/json",
    },
  });
}
