import { NextResponse } from "next/server";
import { promises as fs } from "node:fs";
import path from "node:path";

const MEMORY_DIR = path.resolve(
  process.cwd(),
  "..",
  "server",
  "data",
  "guest_memories"
);

type MemoryEntry = {
  chat_id: number | null;
  title: string;
  updated_at_iso: string;
  size_bytes: number;
  filename: string;
  markdown: string;
};

export async function GET() {
  let files: string[] = [];
  try {
    files = await fs.readdir(MEMORY_DIR);
  } catch {
    return NextResponse.json({ memories: [] });
  }

  const memories: MemoryEntry[] = [];
  for (const file of files) {
    if (!file.endsWith(".md")) continue;
    try {
      const full = path.join(MEMORY_DIR, file);
      const stat = await fs.stat(full);
      const md = await fs.readFile(full, "utf-8");
      const firstLine = md.split("\n")[0] || "";
      const title = firstLine.replace(/^#\s+/, "").trim() || file;
      const stem = file.replace(/\.md$/, "");
      const chat_id = /^\d+$/.test(stem) ? Number(stem) : null;
      memories.push({
        chat_id,
        title,
        updated_at_iso: stat.mtime.toISOString(),
        size_bytes: stat.size,
        filename: file,
        markdown: md,
      });
    } catch {
      /* skip */
    }
  }

  memories.sort((a, b) => b.updated_at_iso.localeCompare(a.updated_at_iso));
  return NextResponse.json({ memories });
}
