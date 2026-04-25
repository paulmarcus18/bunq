import { NextResponse } from "next/server";

const BACKEND_URL = process.env.FINPILOT_BACKEND_URL ?? "http://127.0.0.1:8000";

export async function POST(request: Request) {
  const formData = await request.formData();
  const response = await fetch(`${BACKEND_URL}/analyze-document`, {
    method: "POST",
    body: formData,
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
