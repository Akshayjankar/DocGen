/** IndexedDB local Library — never server-side (Revision 2 WP4). */

import { openDB, type DBSchema, type IDBPDatabase } from "idb";
import type { DocType, DocumentMeta, Mode, RenderOptions } from "@/types/api";

const DB_NAME = "docgen-library";
const MAX_DOCS = 50;
export const LIBRARY_MAX_BYTES = 200 * 1024 * 1024;
const MAX_BYTES = LIBRARY_MAX_BYTES;

export interface LibraryDoc {
  id: string;
  createdAt: number;
  title: string;
  docType: DocType;
  mode: Mode;
  pages: number;
  sealPct: number | null;
  themeSnapshot?: unknown;
  request: {
    text: string;
    meta: DocumentMeta;
    options?: RenderOptions;
    /** Original logo uploads so "Open in Studio" reproduces the paper. */
    logos?: { cover?: Blob; corner?: Blob };
    logoFlags?: {
      sameForBoth: boolean;
      cornerPosition: "left" | "right";
      showCornerOnCover: boolean;
    };
  };
  files: {
    docx?: Blob;
    pdf?: Blob;
  };
  thumbnail?: Blob;
}

interface LibrarySchema extends DBSchema {
  docs: {
    key: string;
    value: LibraryDoc;
    indexes: { "by-created": number; "by-title": string };
  };
  meta: {
    key: string;
    value: { key: string; historyEnabled: boolean };
  };
}

let dbPromise: Promise<IDBPDatabase<LibrarySchema>> | null = null;

function getDb() {
  if (!dbPromise) {
    dbPromise = openDB<LibrarySchema>(DB_NAME, 1, {
      upgrade(db) {
        const store = db.createObjectStore("docs", { keyPath: "id" });
        store.createIndex("by-created", "createdAt");
        store.createIndex("by-title", "title");
        db.createObjectStore("meta", { keyPath: "key" });
      },
    });
  }
  return dbPromise;
}

export async function isHistoryEnabled(): Promise<boolean> {
  try {
    const db = await getDb();
    const row = await db.get("meta", "prefs");
    return row?.historyEnabled !== false;
  } catch {
    return false;
  }
}

export async function setHistoryEnabled(enabled: boolean): Promise<void> {
  const db = await getDb();
  await db.put("meta", { key: "prefs", historyEnabled: enabled });
}

export async function listDocs(): Promise<LibraryDoc[]> {
  const db = await getDb();
  const all = await db.getAllFromIndex("docs", "by-created");
  return all.reverse();
}

export async function getDoc(id: string): Promise<LibraryDoc | undefined> {
  const db = await getDb();
  return db.get("docs", id);
}

/** Save (merging files with an existing entry of the same id). Returns false when history is off. */
export async function saveDoc(doc: LibraryDoc): Promise<boolean> {
  if (!(await isHistoryEnabled())) return false;
  const db = await getDb();
  const prev = await db.get("docs", doc.id);
  const merged: LibraryDoc = prev
    ? {
        ...doc,
        createdAt: prev.createdAt,
        files: {
          docx: doc.files.docx ?? prev.files.docx,
          pdf: doc.files.pdf ?? prev.files.pdf,
        },
        thumbnail: doc.thumbnail ?? prev.thumbnail,
      }
    : doc;
  await db.put("docs", merged);
  await evictIfNeeded(db);
  return true;
}

export async function deleteDoc(id: string): Promise<void> {
  const db = await getDb();
  await db.delete("docs", id);
}

export async function clearAll(): Promise<void> {
  const db = await getDb();
  await db.clear("docs");
}

export async function storageStats(): Promise<{ count: number; bytes: number }> {
  const docs = await listDocs();
  let bytes = 0;
  for (const d of docs) {
    bytes += d.files.docx?.size ?? 0;
    bytes += d.files.pdf?.size ?? 0;
    bytes += d.thumbnail?.size ?? 0;
    bytes += d.request.logos?.cover?.size ?? 0;
    bytes += d.request.logos?.corner?.size ?? 0;
    bytes += (d.request.text?.length ?? 0) * 2;
  }
  return { count: docs.length, bytes };
}

async function evictIfNeeded(db: IDBPDatabase<LibrarySchema>) {
  let docs = await db.getAllFromIndex("docs", "by-created");
  let { bytes } = await storageStats();
  while (docs.length > MAX_DOCS || bytes > MAX_BYTES) {
    const oldest = docs[0];
    if (!oldest) break;
    await db.delete("docs", oldest.id);
    docs = docs.slice(1);
    bytes = (await storageStats()).bytes;
  }
}
